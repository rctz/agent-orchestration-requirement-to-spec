"""Live executor tests against a real `opencode serve` (plan M2 verify).

Run: pytest tests/live -m live -k executor
Needs LITELLM_BASE_URL / LITELLM_API_KEY (loaded from ~/req3/.env by
conftest) and the global `opencode` 1.19.0 on PATH (.184 dev host).

Structure note: the server fixture is SYNC (spawn + readiness via urllib)
and each test builds its own OpencodeExecutor inside the test's event loop —
sharing an httpx AsyncClient across pytest-asyncio loops raises
"Event object is bound to a different event loop".
"""
from __future__ import annotations

import base64
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from req3.executor.opencode import OpencodeExecutor

REPO = Path(__file__).resolve().parents[2]
PASSWORD = "live-test-pw"
REQUIRED_AGENTS = [
    "repo-scanner", "req-designer", "req-reviewer", "spec-designer",
    "spec-reviewer", "revise-analyst", "scan-worker", "spec-worker",
    "review-lens",
]
REQUIRED_MODELS = ["litellm/glm-5.3-flash", "litellm/glm-5.3"]
SCHEMA = {
    "type": "object",
    "properties": {"reply": {"type": "string"}, "n": {"type": "integer"}},
    "required": ["reply", "n"],
    "additionalProperties": False,
}

pytestmark = pytest.mark.live


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _http_up(port: int, password: str, timeout_s: float = 120.0) -> bool:
    auth = "Basic " + base64.b64encode(f"opencode:{password}".encode()).decode()
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/agent",
                headers={"Authorization": auth},
            )
            with urllib.request.urlopen(request, timeout=5):
                return True
        except urllib.error.HTTPError:
            return True  # server answered (status != 2xx is still "up")
        except OSError:
            time.sleep(0.5)
    return False


class OcServer:
    """A short-lived `opencode serve` bound to a project directory."""

    def __init__(self, project_dir: Path):
        self.dir = project_dir
        self.port = _free_port()
        self.err_path = project_dir / "server.err.log"
        # long-lived handle: collects the subprocess stderr until stop()
        self._err_file = open(self.err_path, "wb")  # noqa: SIM115
        env = {**os.environ, "OPENCODE_SERVER_PASSWORD": PASSWORD}
        self.proc = subprocess.Popen(
            ["opencode", "serve", "--hostname", "127.0.0.1", "--port", str(self.port)],
            cwd=project_dir,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=self._err_file,
        )

    def wait_up(self) -> None:
        assert _http_up(self.port, PASSWORD), (
            f"opencode did not start on port {self.port}; "
            f"stderr tail: {self.err_path.read_text(errors='replace')[-500:]}"
        )

    def executor(self) -> OpencodeExecutor:
        return OpencodeExecutor(
            f"http://127.0.0.1:{self.port}",
            password=PASSWORD,
            required_agents=REQUIRED_AGENTS,
            required_models=REQUIRED_MODELS,
        )

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self._err_file.close()


def _generate_config(project_dir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "gen_opencode_config.py"),
            "--roles", str(REPO / "roles.yaml"),
            "--prompts", str(REPO / "prompts"),
            "--out", str(project_dir / "opencode.json"),
        ],
        check=True,
        capture_output=True,
    )


def _needs_credentials() -> None:
    if not os.environ.get("LITELLM_API_KEY"):
        pytest.skip("no LiteLLM credentials available")


@pytest.fixture()
def configured_server(tmp_path):
    """opencode serve with the generated req3 config (all agents)."""
    _needs_credentials()
    _generate_config(tmp_path)
    (tmp_path / "ws").mkdir()
    server = OcServer(tmp_path)
    try:
        server.wait_up()
        yield server
    finally:
        server.stop()


@pytest.fixture()
def empty_server(tmp_path):
    """opencode serve in an empty dir: starts with NO custom agents (spike
    finding) — health() must report that clearly."""
    _needs_credentials()
    server = OcServer(tmp_path)
    try:
        server.wait_up()
        yield server
    finally:
        server.stop()


async def test_health_ok_with_generated_config(configured_server):
    executor = configured_server.executor()
    try:
        report = await executor.health()
        assert report.ok, report.detail
        assert set(REQUIRED_AGENTS) <= set(report.agents)
        assert set(REQUIRED_MODELS) <= set(report.models)
    finally:
        await executor.aclose()


async def test_structured_result_design_model(configured_server):
    executor = configured_server.executor()
    try:
        job_dir = configured_server.dir / "ws" / "j-design"
        job_dir.mkdir()
        result = await executor.run_agent(
            job_dir,
            "req-designer",
            "Reply with a one-sentence greeting and n=7. Nonce live-design-1.",
            schema=SCHEMA,
            timeout_s=300,
        )
        assert result.error is None, result.error
        assert result.structured is not None
        assert result.structured["n"] == 7
        assert result.structured["reply"]
        # info.modelID carries the bare model name (provider prefix stripped
        # by opencode) — verified in the M2 probe.
        assert result.model == "glm-5.3-flash"
        assert result.duration_s and result.duration_s > 0
        assert result.tokens and result.tokens > 0
    finally:
        await executor.aclose()


async def test_structured_result_review_model(configured_server):
    executor = configured_server.executor()
    try:
        job_dir = configured_server.dir / "ws" / "j-review"
        job_dir.mkdir()
        result = await executor.run_agent(
            job_dir,
            "req-reviewer",
            "Reply with a one-sentence ack and n=13. Nonce live-review-1.",
            schema=SCHEMA,
            timeout_s=600,
        )
        assert result.error is None, result.error
        assert result.structured is not None
        assert result.structured["n"] == 13
        assert result.model == "glm-5.3"
    finally:
        await executor.aclose()


async def test_health_fails_clearly_without_config(empty_server):
    executor = empty_server.executor()
    try:
        report = await executor.health()
        assert not report.ok
        assert "missing agents" in report.detail
        assert "req-designer" in report.detail
    finally:
        await executor.aclose()

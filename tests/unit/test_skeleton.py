"""M0 smoke test — the package skeleton imports. Real tests land in M1+."""

import req3


def test_package_imports_with_version() -> None:
    assert req3.__version__ == "0.1.0"

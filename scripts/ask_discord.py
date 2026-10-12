#!/usr/bin/env python3
"""Post a message to Discord (DM by default) — req3 owner questions.

Usage:
  ask_discord.py <message>                     -> DM the owner
  ask_discord.py --channel <channel_id> <message>
Reads DISCORD_BOT_TOKEN and REQ3_OWNER_DISCORD_ID (fallback
464508119934828556) from the environment. Token is never printed.
Exit codes: 0 ok, 1 failure (reason on stderr).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://discord.com/api/v10"
DEFAULT_OWNER_ID = "464508119934828556"


def api_call(method: str, path: str, token: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            # Discord's Cloudflare bans the default python-urllib UA
            "User-Agent": "req3-ask/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode()
            return {"status": response.status, "body": json.loads(raw) if raw.strip() else {}}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:300]
        return {"status": exc.code, "error": detail}


def main() -> int:
    args = sys.argv[1:]
    channel_id = None
    if args and args[0] == "--channel":
        channel_id = args[1]
        args = args[2:]
    if not args:
        print("usage: ask_discord.py [--channel id] <message>", file=sys.stderr)
        return 1
    message = " ".join(args)
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        print("error: DISCORD_BOT_TOKEN not set", file=sys.stderr)
        return 1
    if channel_id is None:
        owner_id = os.environ.get("REQ3_OWNER_DISCORD_ID", DEFAULT_OWNER_ID)
        dm = api_call("POST", "/users/@me/channels", token, {"recipient_id": owner_id})
        if dm.get("status") != 200:
            print(f"error: cannot open DM: {dm.get('error') or dm.get('body')}", file=sys.stderr)
            return 1
        channel_id = dm["body"]["id"]
    sent = api_call(
        "POST", f"/channels/{channel_id}/messages", token, {"content": message}
    )
    if sent.get("status") not in (200, 201):
        print(f"error: send failed: {sent.get('error') or sent.get('body')}", file=sys.stderr)
        return 1
    print(f"sent: message id {sent['body'].get('id')} -> channel {channel_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

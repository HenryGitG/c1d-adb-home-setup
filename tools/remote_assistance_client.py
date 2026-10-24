#!/usr/bin/env python3
"""Owner-authorized C1D remote-assistance bootstrap for standard network ADB."""

import argparse
import base64
import binascii
import json
import re
import sys
import time
import uuid
from pathlib import Path


READ_ONLY_COMMANDS = {
    "probe": (
        "echo C1D_REMOTE_PROBE; id; getprop ro.serialno; "
        "getprop ro.product.model; getprop ro.product.name"
    ),
    "adb-status": (
        "printf 'adb_enabled='; settings get global adb_enabled; "
        "printf 'persist_tcp_port='; getprop persist.adb.tcp.port; "
        "printf 'service_tcp_port='; getprop service.adb.tcp.port; "
        "printf 'adbd_state='; getprop init.svc.adbd"
    ),
}

MUTATING_COMMANDS = {
    "start-adbd": (
        "setprop ctl.start adbd; sleep 1; "
        "printf 'adbd_state='; getprop init.svc.adbd; "
        "printf 'service_tcp_port='; getprop service.adb.tcp.port"
    ),
    "stop-adbd": (
        "setprop ctl.stop adbd; sleep 1; "
        "printf 'adbd_state='; getprop init.svc.adbd"
    ),
}


def load_route(path: Path) -> tuple[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    base_url = str(data.get("remoteDebugUrl", "")).strip().rstrip("/")
    device_serial = str(data.get("deviceSerial", "")).strip()
    if not base_url.startswith(("ws://", "wss://")):
        raise ValueError("remoteDebugUrl must start with ws:// or wss://")
    if ".invalid" in base_url or "REPLACE" in base_url.upper():
        raise ValueError("replace the example remoteDebugUrl with the value shown on your device")
    if not re.fullmatch(r"[A-Za-z0-9._:-]{4,128}", device_serial):
        raise ValueError("deviceSerial is missing or contains unsupported characters")
    return base_url, device_serial


def read_adb_public_key(path: Path) -> str:
    key = path.expanduser().read_text(encoding="utf-8").strip()
    if "\n" in key or len(key) < 100 or len(key) > 4096:
        raise ValueError("ADB public key must be one line between 100 and 4096 characters")
    encoded_key = key.split(maxsplit=1)[0]
    try:
        base64.b64decode(encoded_key, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("ADB public key does not begin with valid base64 data") from error
    return key


def authorize_key_command(public_key: str) -> str:
    encoded = base64.b64encode(public_key.encode("utf-8")).decode("ascii")
    return (
        "KEY=$(printf '%s' '" + encoded + "' | base64 -d); "
        "FILE=/data/misc/adb/adb_keys; "
        "BACKUP=/data/misc/adb/adb_keys.before-c1d-home; "
        "test -e \"$BACKUP\" || cp -p \"$FILE\" \"$BACKUP\"; "
        "grep -Fqx \"$KEY\" \"$FILE\" || printf '%s\\n' \"$KEY\" >> \"$FILE\"; "
        "chown system:shell \"$FILE\"; chmod 0640 \"$FILE\"; "
        "sha256sum \"$FILE\"; setprop ctl.restart adbd; sleep 2; "
        "printf 'adbd_state='; getprop init.svc.adbd"
    )


def run_remote(base_url: str, device_serial: str, command: str, timeout: float) -> None:
    try:
        import websocket
    except ImportError as error:
        raise SystemExit(
            "Missing dependency. Run: python3 -m pip install -r requirements.txt"
        ) from error

    client_id = "c1d-owner-" + uuid.uuid4().hex
    websocket_url = f"{base_url}/webSocket/{client_id}"
    connection = websocket.create_connection(
        websocket_url,
        timeout=min(timeout, 12),
        http_proxy_host=None,
    )
    accepted = False
    completed = False
    try:
        connection.send(
            json.dumps(
                {
                    "from": client_id,
                    "to": device_serial,
                    "type": "chat",
                    "text": command,
                },
                ensure_ascii=False,
            )
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            connection.settimeout(max(0.2, deadline - time.monotonic()))
            try:
                message = json.loads(connection.recv())
            except websocket.WebSocketTimeoutException:
                break
            if message.get("from") != device_serial or message.get("to") != client_id:
                continue
            response = str(message.get("text", ""))
            if response.startswith("收到:"):
                accepted = True
            elif response.endswith(" 执行结束"):
                completed = True
                break
            else:
                print(response, end="" if response.endswith("\n") else "\n")
    finally:
        connection.close()

    if not accepted:
        raise RuntimeError("the device did not acknowledge the command")
    if not completed:
        raise RuntimeError("the device did not report command completion")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Use an owner-authorized C1D remote-assistance route to bootstrap ADB."
    )
    parser.add_argument(
        "action",
        choices=("probe", "adb-status", "start-adbd", "authorize-key", "stop-adbd"),
    )
    parser.add_argument(
        "--route",
        type=Path,
        default=Path("private/remote-route.json"),
        help="private JSON containing remoteDebugUrl and deviceSerial",
    )
    parser.add_argument(
        "--confirm-device-serial",
        help="required for mutating actions; must exactly match deviceSerial",
    )
    parser.add_argument(
        "--adb-public-key",
        type=Path,
        default=Path.home() / ".android" / "adbkey.pub",
        help="public key used by authorize-key; never pass the private adbkey",
    )
    parser.add_argument("--timeout", type=float, default=25.0)
    args = parser.parse_args()

    try:
        base_url, device_serial = load_route(args.route)
        if args.action in MUTATING_COMMANDS or args.action == "authorize-key":
            if args.confirm_device_serial != device_serial:
                raise ValueError(
                    "mutating actions require --confirm-device-serial with the exact serial"
                )
        if args.action == "authorize-key":
            command = authorize_key_command(read_adb_public_key(args.adb_public_key))
        else:
            command = READ_ONLY_COMMANDS.get(args.action) or MUTATING_COMMANDS[args.action]
        run_remote(base_url, device_serial, command, args.timeout)
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

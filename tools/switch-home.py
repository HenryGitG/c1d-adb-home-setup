#!/usr/bin/env python3
"""Switch the HOME activity on an owner-controlled C1D over standard ADB."""

import argparse
import subprocess
import sys


C1D_HOME = "com.gathin.tvhome/com.gathin.tvhome.MainActivity"
VENDOR_HOME = "com.ktcp.launcher/com.ktcp.launcher.activity.LauncherMainActivity"


def adb(serial: str, *args: str, capture: bool = False) -> str:
    result = subprocess.run(
        ["adb", "-s", serial, *args],
        check=True,
        text=True,
        capture_output=capture,
    )
    return result.stdout.strip() if capture else ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Switch between the public C1D Home package and the factory HOME."
    )
    parser.add_argument("host", help="projector LAN address; no port")
    parser.add_argument("mode", choices=("c1d", "factory"))
    parser.add_argument(
        "--yes",
        action="store_true",
        help="skip the model confirmation prompt",
    )
    args = parser.parse_args()

    serial = f"{args.host}:5555"
    subprocess.run(["adb", "connect", serial], check=True)
    model = adb(serial, "shell", "getprop", "ro.product.model", capture=True)
    product = adb(serial, "shell", "getprop", "ro.product.name", capture=True)
    print(f"Connected device: model={model or 'unknown'}, product={product or 'unknown'}")

    if not args.yes:
        answer = input("Confirm this is your C1D projector [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Cancelled; no HOME setting was changed.")
            return 1

    if args.mode == "c1d":
        package = C1D_HOME.split("/", 1)[0]
        adb(serial, "shell", "pm", "enable", "--user", "0", package)
        adb(serial, "shell", "cmd", "package", "set-home-activity", "--user", "0", C1D_HOME)
        adb(serial, "shell", "am", "force-stop", "com.ktcp.launcher")
        expected = C1D_HOME
    else:
        adb(serial, "shell", "pm", "enable", "--user", "0", "com.ktcp.aiagent")
        adb(serial, "shell", "pm", "enable", "--user", "0", "com.ktcp.launcher")
        adb(serial, "shell", "cmd", "package", "set-home-activity", "--user", "0", VENDOR_HOME)
        expected = VENDOR_HOME

    resolved = adb(
        serial,
        "shell",
        "cmd",
        "package",
        "resolve-activity",
        "--brief",
        "-a",
        "android.intent.action.MAIN",
        "-c",
        "android.intent.category.HOME",
        capture=True,
    )
    print(f"Resolved HOME: {resolved}")
    if expected not in resolved:
        print("HOME verification failed.", file=sys.stderr)
        return 2
    print("HOME switch verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

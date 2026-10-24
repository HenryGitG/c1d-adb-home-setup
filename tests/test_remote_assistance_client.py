import base64
import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import remote_assistance_client as client


class FakeConnection:
    def __init__(self, device_serial):
        self.device_serial = device_serial
        self.sent = None
        self.index = 0
        self.closed = False

    def send(self, payload):
        self.sent = json.loads(payload)

    def settimeout(self, _timeout):
        pass

    def recv(self):
        messages = [
            {"from": "another-device", "to": self.sent["from"], "text": "ignore"},
            {
                "from": self.device_serial,
                "to": self.sent["from"],
                "text": "收到: probe",
            },
            {
                "from": self.device_serial,
                "to": self.sent["from"],
                "text": "uid=1000(system)\n",
            },
            {
                "from": self.device_serial,
                "to": self.sent["from"],
                "text": "probe 执行结束",
            },
        ]
        message = messages[self.index]
        self.index += 1
        return json.dumps(message, ensure_ascii=False)

    def close(self):
        self.closed = True


class RemoteAssistanceClientTest(unittest.TestCase):
    def test_load_route_requires_real_websocket_url(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.json"
            path.write_text(
                json.dumps(
                    {
                        "remoteDebugUrl": "ws://relay.example.invalid:0000",
                        "deviceSerial": "SERIAL123",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "replace the example"):
                client.load_route(path)

    def test_public_key_command_backs_up_and_restarts_adbd(self):
        public_key = base64.b64encode(b"x" * 128).decode("ascii") + " owner@mac"
        command = client.authorize_key_command(public_key)
        self.assertIn("adb_keys.before-c1d-home", command)
        self.assertIn("ctl.restart adbd", command)
        self.assertNotIn(public_key, command)

    def test_protocol_addresses_device_and_waits_for_completion(self):
        serial = "SERIAL123"
        connection = FakeConnection(serial)
        fake_module = types.SimpleNamespace(
            create_connection=lambda *_args, **_kwargs: connection,
            WebSocketTimeoutException=TimeoutError,
        )
        output = io.StringIO()
        with patch.dict(sys.modules, {"websocket": fake_module}), contextlib.redirect_stdout(output):
            client.run_remote(
                "ws://relay.local:9000",
                serial,
                client.READ_ONLY_COMMANDS["probe"],
                2,
            )

        self.assertRegex(connection.sent["from"], r"^c1d-owner-[0-9a-f]{32}$")
        self.assertEqual(serial, connection.sent["to"])
        self.assertEqual("chat", connection.sent["type"])
        self.assertIn("uid=1000(system)", output.getvalue())
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()

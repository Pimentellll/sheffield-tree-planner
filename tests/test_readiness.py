"""Synthetic protocol-only loopback server; it is neither a model nor simulator."""

import contextlib
import json
import os
import subprocess
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ProtocolHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.requests.append((self.path, None))
        self.respond(self.server.get_status, self.server.get_body)

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append((self.path, payload))
        if self.server.delay:
            time.sleep(self.server.delay)
        if len(self.server.requests) == 2:
            body = self.server.first
        else:
            observation = json.loads(payload["messages"][-1]["content"])
            body = self.server.final_response or {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": self.server.final or observation["nonce"],
                        },
                    }
                ]
            }
        self.respond(200, body)

    def respond(self, status, body):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        try:
            self.send_response(status)
            lengths = self.server.length_headers
            if lengths is None:
                lengths = [
                    str(
                        len(raw)
                        + self.server.length_padding.get(len(self.server.requests), 0)
                    )
                ]
            for value in lengths:
                self.send_header("Content-Length", value)
            if self.server.transfer_encoding is not None:
                self.send_header("Transfer-Encoding", self.server.transfer_encoding)
            if status == 302:
                self.send_header("Location", "http://example.com/")
            self.end_headers()
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


def valid_call():
    return {
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {"name": "inspect_runtime", "arguments": "{}"},
                        }
                    ],
                },
            }
        ]
    }


@contextlib.contextmanager
def protocol_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ProtocolHandler)
    server.length_padding = {}
    server.length_headers, server.transfer_encoding = None, None
    server.requests, server.get_status, server.get_body = (
        [],
        200,
        {"data": [{"id": "test-model"}]},
    )
    server.first, server.final, server.final_response, server.delay = (
        valid_call(),
        None,
        None,
        0,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def invoke(*args, env=None):
    return subprocess.run(
        [sys.executable, "-m", "sheffield_readiness", *args],
        text=True,
        capture_output=True,
        env=env,
    )


class ReadinessTests(unittest.TestCase):
    def run_inference(self, server, *extra, env=None):
        return invoke(
            "inference",
            "--base-url",
            f"http://127.0.0.1:{server.server_port}/v1",
            "--model",
            "test-model",
            *extra,
            env=env,
        )

    def test_exchange_and_payload(self):
        with protocol_server() as server:
            result = self.run_inference(server, "--disable-thinking")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            receipt = json.loads(result.stdout)
            self.assertTrue(receipt["tool_roundtrip_verified"])
            self.assertFalse(receipt["spark_verified"])
            self.assertEqual(
                [p for p, _ in server.requests],
                ["/v1/models", "/v1/chat/completions", "/v1/chat/completions"],
            )
            first, second = server.requests[1][1], server.requests[2][1]
            self.assertEqual(
                (
                    first["model"],
                    first["tool_choice"],
                    first["temperature"],
                    first["max_tokens"],
                ),
                ("test-model", "auto", 0, 2048),
            )
            self.assertEqual(
                first["tools"][0]["function"]["parameters"],
                {"type": "object", "properties": {}, "additionalProperties": False},
            )
            self.assertEqual(first["chat_template_kwargs"], {"enable_thinking": False})
            self.assertEqual(second["chat_template_kwargs"], {"enable_thinking": False})
            self.assertEqual(second["tool_choice"], "none")
            self.assertEqual(second["messages"][-1]["tool_call_id"], "call-1")
            self.assertTrue(json.loads(second["messages"][-1]["content"])["nonce"])

    def test_default_and_proxy_ignored(self):
        with protocol_server() as server:
            env = dict(
                os.environ,
                HTTP_PROXY="http://127.0.0.1:1",
                http_proxy="http://127.0.0.1:1",
                NO_PROXY="",
                no_proxy="",
            )
            result = self.run_inference(server, env=env)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("chat_template_kwargs", server.requests[1][1])

    def test_invalid_urls_and_arguments(self):
        for url in [
            "http://example.com/v1",
            "http://localhost:99999/v1",
            "http://user@localhost/v1",
            "http://localhost/v1?x=1",
            "http://localhost/v1#x",
            "http://localhost/v2",
            "ftp://localhost/v1",
        ]:
            with self.subTest(url=url):
                self.assertNotEqual(
                    invoke("inference", "--base-url", url, "--model", "m").returncode, 0
                )
        self.assertNotEqual(
            invoke("inference", "--base-url", "http://localhost/v1").returncode, 0
        )
        for args in [["--timeout", "nan"], ["--timeout", "0"], ["--max-tokens", "0"]]:
            self.assertNotEqual(
                invoke(
                    "inference",
                    "--base-url",
                    "http://localhost/v1",
                    "--model",
                    "m",
                    *args,
                ).returncode,
                0,
            )
        with protocol_server() as server:
            result = invoke(
                "inference",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}/v1?x=1",
                "--model",
                "m",
            )
            self.assertEqual(json.loads(result.stdout)["code"], "invalid_endpoint")
            self.assertEqual(server.requests, [])

    def test_http_and_response_failures(self):
        for status, body, code in [
            (302, {}, "http_error"),
            (500, b"secret", "http_error"),
            (200, b"x" * 1048577, "response_error"),
            (200, b"{", "response_error"),
            (200, b'{"data":[],"data":[]}', "response_error"),
            (200, b'{"data":[],"x":1e999}', "response_error"),
            (200, [], "response_error"),
            (200, {"data": []}, "unknown_model"),
        ]:
            with self.subTest(code=code, status=status), protocol_server() as server:
                server.get_status, server.get_body = status, body
                result = self.run_inference(server)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["code"], code)
                self.assertNotIn("secret", result.stdout + result.stderr)

    def test_bad_tool_calls(self):
        mutations = [
            lambda c: c["choices"].append(c["choices"][0]),
            lambda c: c["choices"][0]["message"]["tool_calls"].append(
                c["choices"][0]["message"]["tool_calls"][0]
            ),
            lambda c: c["choices"][0]["message"]["tool_calls"][0]["function"].update(
                name="other"
            ),
            lambda c: c["choices"][0]["message"]["tool_calls"][0]["function"].update(
                arguments='{"x":1}'
            ),
            lambda c: c["choices"][0]["message"]["tool_calls"][0]["function"].update(
                arguments='{"x":1,"x":2}'
            ),
            lambda c: c["choices"][0]["message"]["tool_calls"][0]["function"].pop(
                "arguments"
            ),
            lambda c: c["choices"][0].update(finish_reason="length"),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate), protocol_server() as server:
                mutate(server.first)
                result = self.run_inference(server)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["code"], "invalid_tool")
                self.assertEqual(len(server.requests), 2)

    def test_nonce_and_timeout(self):
        with protocol_server() as server:
            server.final = "wrong"
            self.assertEqual(
                json.loads(self.run_inference(server).stdout)["code"], "nonce_mismatch"
            )
        with protocol_server() as server:
            server.delay = 0.2
            self.assertEqual(
                json.loads(self.run_inference(server, "--timeout", ".05").stdout)[
                    "code"
                ],
                "connection_timeout",
            )

    def test_truncated_final_and_extra_call(self):
        for choice in [
            {
                "finish_reason": "length",
                "message": {"role": "assistant", "content": "partial"},
            },
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "x",
                    "tool_calls": [{"id": "extra"}],
                },
            },
        ]:
            with self.subTest(choice=choice), protocol_server() as server:
                server.final_response = {"choices": [choice]}
                self.assertEqual(
                    json.loads(self.run_inference(server).stdout)["code"],
                    "response_error",
                )

    def test_incomplete_http_bodies_are_rejected(self):
        for request_number, stage in (
            (1, "models"),
            (2, "first_completion"),
            (3, "second_completion"),
        ):
            with self.subTest(stage=stage), protocol_server() as server:
                server.length_padding[request_number] = 32
                result = self.run_inference(server)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(
                    json.loads(result.stdout),
                    {"ok": False, "stage": stage, "code": "response_error"},
                )
                self.assertEqual(len(server.requests), request_number)

    def test_http_framing_headers(self):
        with protocol_server() as server:
            server.length_headers = []
            self.assertEqual(self.run_inference(server).returncode, 0)
        for lengths, encoding in (
            (["invalid"], None),
            (["-1"], None),
            (["1048577"], None),
            (["30", "30"], None),
            (None, "chunked"),
        ):
            with (
                self.subTest(lengths=lengths, encoding=encoding),
                protocol_server() as server,
            ):
                server.length_headers, server.transfer_encoding = lengths, encoding
                result = self.run_inference(server)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["code"], "response_error")

    def test_cli(self):
        self.assertEqual(invoke("--help").returncode, 0)
        self.assertEqual(invoke("--version").returncode, 0)
        env = json.loads(invoke("environment").stdout)
        self.assertEqual(env["scope"], "environment_only")
        self.assertFalse(env["spark_verified"])
        self.assertFalse(env["gpu_verified"])


if __name__ == "__main__":
    unittest.main()

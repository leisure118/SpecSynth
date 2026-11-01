"""ASGI projection layer for Skill/private-artifact redaction.

The redaction rules live in :mod:`acsl.application.privacy`; this module only
applies them to JSON responses at the HTTP boundary.
"""
import json

from acsl.application.privacy import (  # noqa: F401
    NOTICE,
    private_artifact,
    protected_fragments,
    public_payload,
)


class SkillPrivacyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith("/api/"):
            return await self.app(scope, receive, send)
        start = None
        chunks = []
        is_json = False

        async def project(message):
            nonlocal start, is_json
            if message["type"] == "http.response.start":
                start = message
                headers = dict(message.get("headers", []))
                is_json = b"application/json" in headers.get(b"content-type", b"")
                if not is_json:
                    await send(message)
            elif message["type"] == "http.response.body" and is_json:
                chunks.append(message.get("body", b""))
                if not message.get("more_body"):
                    data = json.loads(b"".join(chunks))
                    body = json.dumps(public_payload(data), ensure_ascii=False).encode()
                    start["headers"] = [
                        (key, value)
                        for key, value in start["headers"]
                        if key.lower() not in (b"content-length", b"etag")
                    ] + [(b"content-length", str(len(body)).encode()), (b"cache-control", b"no-store")]
                    await send(start)
                    await send({"type": "http.response.body", "body": body})
            else:
                await send(message)

        await self.app(scope, receive, project)

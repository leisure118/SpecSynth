"""Browsers must discover new bundles after rebuilding the local website."""
import hashlib
import re
from fastapi.testclient import TestClient
from apps.api.app.main import app
from apps.api.app.config import WEB_DIR


def test_entry_revalidates_and_asset_versions_match_actual_contents():
    client = TestClient(app)
    index = client.get('/')
    assert index.status_code == 200
    assert index.headers['cache-control'] == 'no-store'
    for asset in ('main.js', 'main.css'):
        digest = hashlib.sha256((WEB_DIR/'dist'/asset).read_bytes()).hexdigest()[:16]
        assert f'/dist/{asset}?v={digest}' in index.text
        response = client.get(f'/dist/{asset}?v={digest}')
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-cache'
        unchanged = client.get(f'/dist/{asset}?v={digest}', headers={'If-None-Match': response.headers['etag']})
        assert unchanged.status_code == 304
        assert unchanged.headers['cache-control'] == 'no-cache'

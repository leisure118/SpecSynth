"""Server-only API profiles shared by generation agents. Keys are write-only."""
import json
import os
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit
from . import platform_provider as provider

ROOT = Path(__file__).resolve().parents[2]
PROFILES_PATH = ROOT / 'runtime' / 'generation-models.json'
LOCK = threading.RLock()


def configured_profiles():
    with LOCK:
        rows = json.loads(PROFILES_PATH.read_text()) if PROFILES_PATH.is_file() else {}
    return rows


def legacy_profiles(snapshot=None):
    config = snapshot if snapshot is not None else provider.get_config()
    rows = {}
    for key, model in config.models.items():
        if isinstance(config, provider.PlatformConfig):
            rows[key] = {'id': key, 'name': model.model_name, 'model': model.model_name, 'base_url': model.base_url, 'api_key': model.api_key, 'protocol': 'chat', 'legacy': True}
        elif model.configured:
            url = model.url.removesuffix('/chat/completions')
            rows[key] = {'id': key, 'name': model.name, 'model': model.name, 'base_url': url, 'api_key': model.key, 'protocol': 'chat', 'legacy': True}
    return rows


def all_profiles(snapshot=None):
    try:
        rows = legacy_profiles(snapshot)
    except Exception:
        rows = {}
    return rows | configured_profiles()


def public_profile(row):
    return {k: row[k] for k in ('id','name','model','base_url','protocol')} | {'auth_mode': row.get('auth_mode','api_key'), 'is_default': bool(row.get('is_default')),  'configured': row.get('auth_mode')=='none' or bool(row.get('api_key')), 'editable': not row.get('legacy', False)}


def save_profile(body):
    row = dict(body)
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', row['id']):
        raise ValueError('配置编号只允许字母、数字、下划线和短横线。')
    u = urlsplit(row['base_url'])
    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError('请输入有效的 API Base URL，不要在地址中填写密钥。')
    row['base_url'] = row['base_url'].rstrip('/')
    for suffix in ('/chat/completions','/responses'):
        row['base_url'] = row['base_url'].removesuffix(suffix)
    if row.get('auth_mode','api_key') not in ('api_key','none'):
        raise ValueError('请选择有效的认证方式。')
    with LOCK:
        rows = configured_profiles()
        if len(rows)>=40 and row['id'] not in rows:
            raise ValueError('最多配置 40 个模型。')
        if row.get('auth_mode')=='none':
            row['api_key']=''
        else:
            if not row.get('api_key'):
                row['api_key'] = rows.get(row['id'],{}).get('api_key','')
            if not row['api_key']:
                raise ValueError('新配置需要填写 API Key，或明确选择无需认证。')
        if row.get('is_default'):
            for existing in rows.values():
                if existing['protocol']==row['protocol']: existing['is_default']=False
        rows[row['id']] = row
        PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = PROFILES_PATH.with_suffix('.tmp')
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w') as stream:
            json.dump(rows,stream,ensure_ascii=False)
        os.replace(tmp,PROFILES_PATH)
    return public_profile(row)

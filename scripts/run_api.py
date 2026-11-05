from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Run API with local Docker or server-native tools")
    parser.add_argument('--profile',choices=['local','server'])
    parser.add_argument('--host',default='0.0.0.0')
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    if args.profile:
        from acsl.infrastructure.runtime_profile import apply_runtime_profile
        apply_runtime_profile(args.profile)
    uvicorn.run("apps.api.app.main:app", host=args.host, port=args.port, reload=False)

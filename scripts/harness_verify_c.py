"""Frama-C tool for official Harness candidates; output is verifier evidence."""
from pathlib import Path
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from apps.api.app.agent_execution import verify_candidates
    data = json.loads(Path(sys.argv[1]).read_text())
    files = data['files']
    from pathlib import PurePosixPath
    for item in files:
        path = PurePosixPath(item['path'])
        if path.is_absolute() or '..' in path.parts or not str(path).endswith(('.c', '.h','.gh')):
            raise ValueError('Invalid candidate path')
    entry = next(f['path'] for f in files if f['path'].endswith('.c'))
    folder = Path(sys.argv[1]).resolve().parent / '.platform-proofs'
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=folder) as temporary:
        tool='verifast' if sys.argv[2:]==['--tool','verifast'] else 'framac'
        check = verify_candidates(files, entry, 'single' if tool=='verifast' else 'inter-modular', Path(temporary), 30,verification_tool=tool)
        print(json.dumps(check, ensure_ascii=False))


if __name__ == '__main__':
    main()

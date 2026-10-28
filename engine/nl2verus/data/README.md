# Bundled NL2VBench data

`NL2VBench.jsonl` is the workbench's self-contained dataset copy. The web UI and API read this file by default, so the project continues to work when distributed without the original NL2VRAG repository.

The imported copy intentionally removes the duplicated function signature from the end of every `description`. The interface remains available in the separate `function_signature` field.

To rebuild this copy from the original dataset:

```powershell
python scripts/import_dataset.py --source D:\path\to\NL2VBench.jsonl
```


"""Validate a native patch tool submission, without running a proof or model."""
import json
import sys
from .spec_patches import candidate_quality,normalize_patch_delimiters


def main():
    try:
        payload=json.loads(sys.stdin.read(1048576))
        data,notes=normalize_patch_delimiters(payload['data'],payload.get('verification_tool','framac'))
        quality=candidate_quality(payload['files'],data,verification_tool=payload.get('verification_tool','framac'))
        if notes:quality.update(delimiter_normalization=notes,normalized_patches=data)
        if not quality['annotation_nonempty'] and (payload.get('verification_tool')=='verifast' or quality.get('uncovered_loops_estimate')):
            raise ValueError('未生成实际规约：原始循环缺少不变量，不能用空 patches 或成功摘要代替生成结果。')
        print(json.dumps(quality,ensure_ascii=False))
    except (ValueError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())

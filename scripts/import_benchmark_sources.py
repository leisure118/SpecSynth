"""Attach original C sources to historical cases using unique normalized names."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def normalized(name):
    return name.translate(str.maketrans({'‘':"'",'’':"'",'“':'"','”':'"'}))


def attach_sources(source, destination):
    summaries=[]
    for bid,folder in [('live25','live25'),('live24','live24'),('autobench_v2','autobench')]:
        root=source/folder
        mapping={}
        for path in sorted(root.rglob('*.c')):
            if path.is_symlink():continue
            key=normalized(path.relative_to(root).with_suffix('').as_posix().replace('/','_'))
            if key in mapping:raise ValueError('Ambiguous original source name: '+key)
            mapping[key]=path
        index_path=destination/bid/'index.json'
        data=json.loads(index_path.read_text());matched=0;missing=[]
        for row in data['items']:
            path=mapping.get(normalized(row['id']))
            if path is None:
                missing.append(row['id']);continue
            relative=path.relative_to(root)
            target=destination/bid/'original'/relative
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
            row['artifacts']['original_source']=target.relative_to(destination).as_posix()
            row['original_filename']=path.name
            row['original_path']=relative.as_posix()
            row['original_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            matched+=1
        data['benchmark']['original_source_count']=matched
        index_path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
        summaries.append({'id':bid,'matched':matched,'missing':missing})
    catalog=json.loads((destination/'index.json').read_text())
    counts={r['id']:r['matched'] for r in summaries}
    for b in catalog:
        if b['id'] in counts:b['original_source_count']=counts[b['id']]
    (destination/'index.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
    return summaries

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    args=parser.parse_args()
    print(json.dumps(attach_sources(args.source.resolve(),Path(__file__).resolve().parents[1]/'resources'/'benchmarks'),ensure_ascii=False,indent=2))

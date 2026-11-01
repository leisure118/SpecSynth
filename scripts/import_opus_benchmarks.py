"""Import a Claude Opus result bundle as a separate, portable configuration.

Reads data only. Never executes scripts, model calls, or files in the source bundle.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil

CONFIGURATION='Claude Code + opus 4.6 + spec-skill'
DATASETS=(('live25','live25','LiveFMBench 2025'),('live24','live24','LiveFMBench 2024'),('autobench','autobench_v2','autobench'))


def normalize(name):
    return name.translate(str.maketrans({'‘':"'",'’':"'",'“':'"','”':'"'}))


def records(folder):
    lines=[json.loads(line) for line in (folder/'results.jsonl').read_text().splitlines() if line.strip()]
    rows={r['file']:r for r in lines}
    if len(rows)!=len(lines):raise ValueError('Duplicate final records: '+folder.name)
    if (folder/'results.csv').is_file():
        table={r['file']:r for r in csv.DictReader((folder/'results.csv').open())}
        if set(table)!=set(rows):raise ValueError('CSV/JSONL case lists differ: '+folder.name)
        for name,row in rows.items():
            if any(str(table[name][key])!=str(row[key]) for key in ('status','round','proved','total')):
                raise ValueError('CSV/JSONL results differ: '+name)
    for name,r in rows.items():
        if not re.fullmatch(r'[^/\\\x00-\x1f]+',name) or name in ('.','..'):raise ValueError('Unsafe case identifier')
        if not 0<=int(r['round'])<=100 or (r['status']=='pass' and int(r['round'])==0):raise ValueError('Invalid attempt round: '+name)
        if not 0<=int(r['proved'])<=int(r['total']):raise ValueError('Invalid proof counts: '+name)
    return rows


def is_flagged(row):
    return row['status'] in ('cheat','flagged') or bool(re.search(r'\b(?:cheat|illegal admit)\b',str(row.get('error') or ''),re.I))


def import_bundle(source, destination):
    catalog_path=destination/'index.json'
    catalog=json.loads(catalog_path.read_text())
    manifest=[]
    for source_name,base_id,title in DATASETS:
        folder=source/source_name
        rows=records(folder)
        report=(folder/'report.md').read_text() if (folder/'report.md').is_file() else ''
        summary={}
        valid=lambda r:r['status']=='pass' and not is_flagged(r) and int(r['total'])>0 and int(r['proved'])==int(r['total'])
        for metric in ('pass@1','pass@5'):
            passed=sum(valid(r) and (1<=int(r['round'])<=5 if metric=='pass@5' else int(r['round'])==1) for r in rows.values())
            total=len(rows);rate=round(passed/total*100,1) if total else 0
            match=re.search(r'\|\s*'+re.escape(metric)+r'\s*\|\s*(\d+)/(\d+)\s*\(([\d.]+)%\)',report)
            if match and (int(match[1]),int(match[2]),float(match[3]))!=(passed,total,rate):
                raise ValueError('Report and final records disagree: '+source_name+' '+metric)
            summary[metric]={'passed':passed,'total':total,'rate':rate}
        bid='opus46_'+source_name
        originals={}
        original_root=destination/base_id/'original'
        if original_root.exists():
            for path in original_root.rglob('*.c'):
                if path.is_symlink():continue
                key=normalize(path.relative_to(original_root).with_suffix('').as_posix().replace('/','_'))
                if key in originals:raise ValueError('Ambiguous original source: '+key)
                originals[key]=path
        items=[];original_count=0
        for name,r in sorted(rows.items()):
            proved,total=int(r['proved']),int(r['total'])
            flagged=is_flagged(r)
            status='flagged' if flagged else 'passed' if valid(r) else 'error' if r['status']=='error' else 'failed'
            item={'id':name,'path':name+'.c','status':status,'raw_status':r['status'],'round':int(r['round']),'proved':proved,'total':total,'goal_rate':round(proved/total*100,1) if total else None,'tokens':int(r.get('tokens') or 0),'elapsed_sec':float(r.get('elapsed_sec') or 0),'error':r.get('error') or '', 'artifacts':{}}
            if flagged and not item['error']:item['error']='输入记录标记存在违规证明假设，按失败计。'
            for kind,suffix in (('source','.acsl.c'),('log','.wp.txt')):
                artifact=folder/name/(name+suffix)
                if artifact.is_symlink() or not artifact.resolve().is_relative_to(source.resolve()):raise ValueError('External or symlink artifact rejected: '+name)
                if artifact.is_file():
                    target=destination/bid/name/artifact.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(artifact,target)
                    item['artifacts'][kind]=target.relative_to(destination).as_posix()
            original=originals.get(normalize(name))
            if original:
                relative=original.relative_to(original_root)
                item.update(original_filename=original.name,original_path=relative.as_posix(),original_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
                item['artifacts']['original_source']=original.relative_to(destination).as_posix();original_count+=1
            items.append(item)
        beyond_budget=sum(valid(r) and int(r['round'])>5 for r in rows.values())
        date=re.search(r'日期[：:]\s*(\d{4}-\d{2}-\d{2})',report)
        benchmark={'id':bid,'dataset_id':base_id,'name':title,'language':'C / ACSL','model':'claude-opus-4-6','agent':'claude-code','skill':'spec-bottomup','skill_family':'spec-skill','configuration_label':CONFIGURATION,'date':date[1] if date else None,'summary':summary,'summary_source':'report-and-final-records' if report else 'final-records','reported_total':len(items),'indexed_total':len(items),'passed_count':sum(r['status']=='passed' for r in items),'flagged_count':sum(r['status']=='flagged' for r in items),'original_source_count':original_count,'passed_after_round5':beyond_budget,'description':'自底向上生成 ACSL 规约，通过 Frama-C WP 检查逐文件证明目标。','notice':'导入 Claude Code + opus 4.6 + spec-skill 的已有结果，未重新调用模型。违规假设和0/0不计通过。'+(' 此数据集未附汇总报告，pass@1/pass@5按最终记录状态与轮次计算。' if not report else '')+(f' 有{beyond_budget}个文件在第5轮之后才通过，保留最终成功状态，但不计入pass@5。' if beyond_budget else '')}
        target=destination/bid/'index.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps({'benchmark':benchmark,'items':items},ensure_ascii=False,indent=2)+'\n')
        manifest.append(benchmark)
    new_ids={r['id'] for r in manifest}
    catalog=[r for r in catalog if r['id'] not in new_ids]+manifest
    catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--destination',type=Path,default=Path(__file__).resolve().parents[1]/'resources/benchmarks')
    args=parser.parse_args()
    result=import_bundle(args.source.resolve(),args.destination)
    print(json.dumps([{k:b[k] for k in ('id','summary','flagged_count','original_source_count')} for b in result],ensure_ascii=False,indent=2))

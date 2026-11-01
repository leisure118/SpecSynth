"""Import historical benchmark artifacts without running supplied scripts or models."""
import argparse
import csv,json,re,shutil
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path,help='Experiment bundle containing output/ and scripts/')
args=parser.parse_args()
src=args.source.resolve()
dest=Path(__file__).resolve().parents[1]/'resources'/'benchmarks'
manifest=[]
for key,title in [('live25','LiveFMBench 2025'),('live24','LiveFMBench 2024'),('autobench_v2','autobench')]:
 report=(src/'scripts'/f'{key}_report.md').read_text()
 summary={}
 for metric in ['pass@1','pass@5']:
  m=re.search(r'\| '+metric+r' \| (\d+)/(\d+) \(([\d.]+)%\)',report)
  summary[metric]={'passed':int(m[1]),'total':int(m[2]),'rate':float(m[3])}
 failed={}; flagged=set(); section=''
 for line in report.splitlines():
  if line.startswith('## '): section=line
  if not line.startswith('| '):continue
  cells=[x.strip() for x in line.strip('|').split('|')]
  if section=='## 失败案例（不含作弊）' and len(cells)>=4 and cells[0]!='文件':
   failed[cells[0]]=cells[3]
  if section=='## 作弊案例' and cells[0]!='文件': flagged.add(cells[0])
 rows={r['file']:r for r in csv.DictReader((src/'output'/key/'results.csv').open())}
 items=[]
 for name,r in sorted(rows.items()):
  proved,total=int(r['proved']),int(r['total']); status='flagged' if name in flagged else 'failed' if name in failed else 'passed' if r['status']=='pass' else 'error' if r['status']=='error' else 'failed'
  record={'id':name,'path':name+'.c','status':status,'raw_status':r['status'],'round':int(r['round']),'proved':proved,'total':total,'goal_rate':round(proved/total*100,1) if total else None,'tokens':int(r['tokens']),'elapsed_sec':float(r['elapsed_sec']),'error':('报告标记存在违规 admit，按失败计。' if status=='flagged' else failed.get(name) or r['error'] or ''),'artifacts':{}}
  directory=src/'output'/key/name
  for kind,suffix in [('source','.acsl.c'),('log','.wp.txt')]:
   file=directory/(name+suffix)
   if file.is_file():
    target=dest/key/name/file.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,target)
    record['artifacts'][kind]=target.relative_to(dest).as_posix()
  items.append(record)
 data={'id':key,'name':title,'language':'C / ACSL','model':'deepseek-v4-flash','agent':'claude-code','skill_family':'spec-skill','configuration_label':'Claude Code + deepseek-v4-flash + spec-skill','skill':'spec-bottomup','date':'2026-06-06','summary':summary,'reported_total':summary['pass@5']['total'],'indexed_total':len(items),'flagged_count':len(flagged),'passed_count':sum(r['status']=='passed' for r in items),'description':'自底向上生成 ACSL 规约，通过 Frama-C WP、Alt-Ergo 与 Z3 迭代验证。','notice':'汇总采用修正版实验报告；逐文件状态优先采用该报告的失败和违规名单，目标通过率来自原始结果。历史导入结果，未在当前服务器重新验证。'+(' 原始逐文件清单与报告总数不一致，保留全部记录，不强行凑齐统计。' if len(items)!=summary['pass@5']['total'] else '')+(' 本次导入为较早的 284 文件版本。' if key=='live24' else '')}
 (dest/key/'index.json').write_text(json.dumps({'benchmark':data,'items':items},ensure_ascii=False,indent=2))
 manifest.append(data)
catalog_path=dest/'index.json'
existing=json.loads(catalog_path.read_text()) if catalog_path.exists() else []
updates={b['id']:b for b in manifest}
old_ids={b['id'] for b in existing}
merged=[updates.get(b['id'],b) for b in existing]+[b for b in manifest if b['id'] not in old_ids]
catalog_path.write_text(json.dumps(merged,ensure_ascii=False,indent=2))
print([(x['name'],x['indexed_total'],x['reported_total']) for x in manifest])

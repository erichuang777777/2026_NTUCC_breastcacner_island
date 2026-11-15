"""Export the existing SQLite store locally; output contains secrets and must stay out of Git."""
import argparse,json,sqlite3,os
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.out.exists():p.error('輸出已存在，請使用新檔名')
tables=['content_settings','agent_keys','agent_requests','articles','article_revisions','attachments','sessions','resident_profiles','events','participants']
conn=sqlite3.connect(a.database.resolve().as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
existing={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")};data={t:[dict(r) for r in conn.execute('SELECT * FROM '+t)] for t in tables if t in existing};conn.close()
a.out.parent.mkdir(parents=True,exist_ok=True)
fd=os.open(a.out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:json.dump({'tables':data,'attachmentsDirectory':str(a.database.resolve().parent/'attachments')},f,ensure_ascii=False)
print('本機匯出完成；未包含登入工作階段或即時位置，請勿提交此檔案。')

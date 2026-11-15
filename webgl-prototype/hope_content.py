"""Article publishing and event participation, backed by the shared SQLite database."""
import base64
import hashlib
import hmac
import io
import json
import math
import os
import re
import secrets
import socket
import time
import uuid
import zipfile
from datetime import datetime
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit, unquote
from zoneinfo import ZoneInfo

MAX_FILE = 12 * 1024 * 1024

def stamp():
    return datetime.now(ZoneInfo('Asia/Taipei')).isoformat(timespec='seconds')

def today():
    return stamp()[:10]

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

class ApiError(Exception):
    def __init__(self, status, message): self.status, self.message = status, message

def require(condition, message, status=400):
    if not condition: raise ApiError(status, message)

class ContentService:
    def __init__(self, connect, data_dir, seed_path):
        self.connect, self.data_dir = connect, Path(data_dir)
        self.uploads = self.data_dir / 'attachments'
        self.uploads.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.seed = json.loads(Path(seed_path).read_text())
        self.failures = {}
        from hope_realtime import ResidentUpdates
        self.resident_updates=ResidentUpdates()
        from hope_world import IslandWorld
        self.world=IslandWorld(Path(__file__).parent/'server-assets/walkable-v22.json')
        with connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS agent_keys(id TEXT PRIMARY KEY, label TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL, prefix TEXT NOT NULL, created_at TEXT NOT NULL, last_used_at TEXT, revoked_at TEXT);
            CREATE TABLE IF NOT EXISTS agent_requests(key_id TEXT NOT NULL, request_key TEXT NOT NULL, fingerprint TEXT NOT NULL, response TEXT NOT NULL, status INTEGER NOT NULL, PRIMARY KEY(key_id,request_key));
            CREATE TABLE IF NOT EXISTS content_settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS admin_sessions(token TEXT PRIMARY KEY, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS articles(id TEXT PRIMARY KEY, draft TEXT NOT NULL, published TEXT, status TEXT NOT NULL DEFAULT 'draft', version INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS article_revisions(id INTEGER PRIMARY KEY, article_id TEXT NOT NULL REFERENCES articles(id), version INTEGER NOT NULL, payload TEXT NOT NULL, action TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attachments(id TEXT PRIMARY KEY, article_id TEXT NOT NULL REFERENCES articles(id), name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, title TEXT NOT NULL, date TEXT NOT NULL, status TEXT NOT NULL, questions TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS participants(id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id), profile_id TEXT NOT NULL REFERENCES resident_profiles(id), token TEXT NOT NULL UNIQUE, progress INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0, completed_at TEXT, created_at TEXT NOT NULL);
            ''')
            from hope_world import initialize_world
            initialize_world(db)
            if not db.execute("SELECT 1 FROM content_settings WHERE key='seeded'").fetchone():
                for station in self.seed['stations']:
                    for i, item in enumerate(station['items']):
                        payload = dict(title=item['title'], body=item['body'], summary='', stations=[station['id']], stage='一般衛教', author='', reviewer='', source='', order=i, attachments=[])
                        db.execute('INSERT INTO articles VALUES(?,?,NULL,?,?,?)', (str(uuid.uuid4()), json.dumps(payload, ensure_ascii=False), 'draft', 1, stamp()))
                db.execute("INSERT INTO content_settings VALUES('seeded','1')")

    def session(self, handler, db):
        try:
            cookie = SimpleCookie(handler.headers.get('Cookie', ''))
            token = cookie['hope_admin'].value
        except (KeyError, ValueError): return False
        return bool(db.execute('SELECT 1 FROM admin_sessions WHERE token=? AND expires>?', (digest(token), time.time())).fetchone())

    def origin(self, h):
        # Mutations must originate in the app, not a cross-site form or DNS-rebinding host.
        host = urlsplit('http://'+h.headers.get('Host', '')).hostname
        hosts={'127.0.0.1','localhost','::1',h.server.server_address[0]} | set(os.environ.get('HOPE_ALLOWED_HOSTS','').split(','))
        with self.connect() as db:
            configured=db.execute("SELECT value FROM content_settings WHERE key='entry_url'").fetchone()
            if configured: hosts.add(urlsplit(configured[0]).hostname)
        if os.environ.get('HOPE_PUBLIC_URL'): hosts.add(urlsplit(os.environ['HOPE_PUBLIC_URL']).hostname)
        require(host in hosts, '主機名稱不允許，請使用伺服器的本機或院內位址。', 403)
        origin = h.headers.get('Origin')
        require(origin and urlsplit(origin).netloc == h.headers.get('Host'), '請從希望島頁面操作。', 403)
        require(h.headers.get('Sec-Fetch-Site', 'same-origin') in ('same-origin', 'none'), '不接受跨網站操作。', 403)

    def body(self, h, limit=512_000):
        try: size = int(h.headers.get('Content-Length', '0'))
        except ValueError: raise ApiError(400, '資料長度錯誤。')
        require(0 < size <= limit, '資料過大或沒有內容。', 413)
        require(h.headers.get('Content-Type', '').startswith('application/json'), '需要 JSON 格式。', 415)
        try: value = json.loads(h.rfile.read(size))
        except (ValueError, UnicodeError): raise ApiError(400, '資料格式錯誤。')
        require(isinstance(value, dict), '需要物件格式。')
        return value

    def article_payload(self, body, db, article_id):
        row=db.execute('SELECT draft FROM articles WHERE id=?',(article_id,)).fetchone()
        previous=json.loads(row['draft']) if row else {}
        body=dict(body)
        if 'references' in body: body['source']=body['references']
        if 'category' in body:
            categories=body['category'] if isinstance(body['category'],list) else [body['category']]
            names={station['name']:station['id'] for station in self.seed['stations']}
            body['stations']=[names.get(c,c) if isinstance(c,str) else c for c in categories]
        payload = {}
        for key, maximum in [('title',160),('body',100_000),('summary',600),('stage',60),('author',100),('reviewer',100),('source',10000)]:
            value = body.get(key, previous.get(key,''))
            require(isinstance(value,str) and len(value)<=maximum, '文章欄位格式或長度不正確：'+key)
            payload[key] = value.strip()
        require(payload['title'], '請填寫文章標題。')
        stations = body.get('stations',previous.get('stations', []))
        require(isinstance(stations,list) and stations and all(type(s) is int and 0<=s<10 for s in stations), '請選擇至少一個科別。')
        payload['stations'] = sorted(set(stations))
        order = body.get('order',previous.get('order',0))
        require(type(order) is int and 0<=order<=9999, '排序請輸入 0 至 9999。')
        payload['order'] = order
        ids = body.get('attachments',previous.get('attachments',[]))
        require(isinstance(ids,list) and len(ids)<=20 and all(isinstance(i,str) for i in ids), '附件格式不正確。')
        for i in ids: require(db.execute('SELECT 1 FROM attachments WHERE id=? AND article_id=?',(i,article_id)).fetchone(), '附件不屬於這篇文章。')
        payload['attachments'] = list(dict.fromkeys(ids))
        return payload

    def article(self, row, db, public=False):
        payload = json.loads(row['published'] if public else row['draft'])
        files = [dict(r) for r in db.execute('SELECT id,name,mime,size FROM attachments WHERE article_id=?',(row['id'],))]
        payload['files'] = [f for f in files if f['id'] in payload['attachments']]
        return dict(payload, category=payload['stations'][0] if len(payload['stations'])==1 else payload['stations'], references=payload['source'], id=row['id'], version=payload.get('publicationVersion',row['version']) if public else row['version'], status='published' if public else row['status'], updatedAt=row['updated_at'], hasPublished=bool(row['published']))

    def event_active(self, event):
        require(event and event['status']=='open' and event['date']==today(), '活動尚未開始或已結束，請洽現場工作人員。', 409)

    def progress(self, row, db):
        event = db.execute('SELECT * FROM events WHERE id=?',(row['event_id'],)).fetchone()
        questions = json.loads(event['questions']); index=row['progress']
        profile = db.execute('SELECT * FROM resident_profiles WHERE id=?',(row['profile_id'],)).fetchone()
        result=dict(id=row['id'],eventId=event['id'],role=profile['role'],appearance=json.loads(profile['appearance_json']),title=event['title'],date=event['date'],active=event['date']==today() and event['status']=='open',progress=index,total=len(questions),completedAt=row['completed_at'],name=profile['display_name'])
        if index<len(questions): result['question'] = {k:questions[index][k] for k in ('prompt','choices')}
        return result

    def handle(self, h):
        path = urlsplit(h.path).path
        if not (path.startswith('/api/agent/') or path.startswith('/api/admin/') or path.startswith('/api/education') or path.startswith('/api/files/') or path.startswith('/api/events/') or path.startswith('/api/participant')): return False
        try:
            if path=='/api/events/resident-stream' and h.command=='GET':
                self.stream_residents(h);return True
            if h.command!='GET' and not path.startswith('/api/agent/'): self.origin(h)
            with self.connect() as db: self.dispatch(h,path,db)
            if (h.command!='GET' or path=='/api/participant/control') and (path.startswith('/api/events/') or path.startswith('/api/participant') or path.startswith('/api/admin/events')):self.resident_updates.changed()
        except ApiError as e: h.send_json(e.status,{'error':e.message})
        except (ValueError, TypeError, KeyError): h.send_json(400,{'error':'欄位格式不正確，請檢查後重試。'})
        return True

    def dispatch(self,h,path,db):
        method=h.command; authenticated=self.session(h,db)
        if path.startswith('/api/agent/'):
            self.agent_dispatch(h,path,db);return
        configured=bool(db.execute("SELECT 1 FROM content_settings WHERE key='password'").fetchone())
        if path=='/api/admin/session' and method=='GET':
            h.send_json(200,dict(authenticated=authenticated,configured=configured,today=today()));return
        if path in ('/api/admin/setup','/api/admin/login') and method=='POST':
            require(h.client_address[0] in ('127.0.0.1','::1') or path.endswith('/login'), '首次設定請在伺服器本機操作。',403)
            body=self.body(h); password=body.get('password','')
            require(isinstance(password,str) and 8<=len(password)<=128,'管理密碼請使用 8 至 128 個字元。')
            bucket=self.failures.setdefault(h.client_address[0],[]);bucket[:]=[t for t in bucket if t>time.time()-300]
            require(len(bucket)<8,'嘗試次數過多，請於五分鐘後再試。',429)
            if path.endswith('/setup'):
                db.execute('BEGIN IMMEDIATE')
                require(not db.execute("SELECT 1 FROM content_settings WHERE key='password'").fetchone(),'已設定管理密碼，請改用登入。',409)
                salt=secrets.token_hex(16); hashed=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600_000).hex()
                db.execute("INSERT INTO content_settings VALUES('password',?)",(salt+':'+hashed,))
            else:
                require(configured,'請先設定管理密碼。',409)
                salt,expected=db.execute("SELECT value FROM content_settings WHERE key='password'").fetchone()[0].split(':')
                actual=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600_000).hex()
                if not hmac.compare_digest(actual,expected): bucket.append(time.time());raise ApiError(401,'密碼不正確。')
            token=secrets.token_urlsafe(32)
            db.execute('DELETE FROM admin_sessions WHERE expires<?',(time.time(),))
            db.execute('INSERT INTO admin_sessions VALUES(?,?)',(digest(token),time.time()+8*3600))
            db.commit();h.extra_headers={'Set-Cookie':f'hope_admin={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'}
            h.send_json(200,{'authenticated':True});return
        if path=='/api/admin/logout' and method=='POST':
            if authenticated:
                token=SimpleCookie(h.headers.get('Cookie',''))['hope_admin'].value;db.execute('DELETE FROM admin_sessions WHERE token=?',(digest(token),))
            db.commit();h.extra_headers={'Set-Cookie':'hope_admin=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'};h.send_json(200,{'ok':True});return
        if path.startswith('/api/admin/'): require(authenticated,'請先登入管理介面。',401)
        if path=='/api/admin/api-keys':
            if method=='GET':
                h.send_json(200,{'keys':[dict(r) for r in db.execute('SELECT id,label,prefix,created_at,last_used_at,revoked_at FROM agent_keys ORDER BY created_at DESC')]});return
            if method=='POST':
                label=self.body(h).get('label','');require(isinstance(label,str) and 1<=len(label.strip())<=80,'請填寫金鑰名稱。')
                token='hope_agent_'+secrets.token_urlsafe(32);kid=str(uuid.uuid4())
                db.execute('INSERT INTO agent_keys VALUES(?,?,?,?,?,NULL,NULL)',(kid,label.strip(),digest(token),token[:17],stamp()));db.commit()
                h.send_json(201,dict(id=kid,label=label.strip(),key=token));return
        if path.startswith('/api/admin/api-keys/') and method=='DELETE':
            cursor=db.execute('UPDATE agent_keys SET revoked_at=? WHERE id=?',(stamp(),path.rsplit('/',1)[-1]));require(cursor.rowcount,'找不到金鑰。',404)
            db.commit();h.send_json(200,{'ok':True});return
        if path=='/api/admin/entry':
            if method=='PATCH':
                value=self.body(h).get('url','');require(isinstance(value,str),'網址格式不正確。')
                parsed=urlsplit(value.strip())
                require(parsed.scheme in ('http','https') and parsed.hostname and not parsed.username and not parsed.password and parsed.path in ('','/') and not parsed.query and not parsed.fragment,'請輸入完整網站位址，例如 http://192.168.1.100:8001。')
                require(parsed.hostname not in ('localhost','127.0.0.1','::1','0.0.0.0'),'請使用手機可連線的網路位址。')
                value=parsed.scheme+'://'+parsed.netloc
                db.execute("INSERT INTO content_settings VALUES('entry_url',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(value,));db.commit()
            row=db.execute("SELECT value FROM content_settings WHERE key='entry_url'").fetchone()
            value=os.environ.get('HOPE_PUBLIC_URL') or (row[0] if row else None)
            if not value:
                host=urlsplit('http://'+h.headers.get('Host','')).hostname
                if host in ('localhost','127.0.0.1','::1','0.0.0.0'):
                    try:
                        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
                            probe.connect(('192.0.2.1',80));host=probe.getsockname()[0]
                    except OSError: host=None
                if host: value=f'http://{host}:{h.server.server_port}'
            h.send_json(200,dict(url=value,localOnly=h.server.server_address[0] in ('127.0.0.1','::1')));return
        if path=='/api/education' and method=='GET':
            rows=db.execute('SELECT * FROM articles WHERE published IS NOT NULL').fetchall()
            h.send_json(200,{'articles':sorted([self.article(r,db,True) for r in rows],key=lambda a:(a['order'],a['title']))});return
        if path=='/api/admin/articles':
            if method=='GET': h.send_json(200,{'articles':[self.article(r,db) for r in db.execute('SELECT * FROM articles ORDER BY updated_at DESC')]});return
            if method=='POST':
                body=self.body(h);aid=str(uuid.uuid4());payload=self.article_payload(body,db,aid)
                db.execute('INSERT INTO articles VALUES(?,?,NULL,?,?,?)',(aid,json.dumps(payload,ensure_ascii=False),'draft',1,stamp()))
                db.commit();h.send_json(201,self.article(db.execute('SELECT * FROM articles WHERE id=?',(aid,)).fetchone(),db));return
        match=re.fullmatch(r'/api/admin/articles/([a-f0-9-]+)(?:/(publish|unpublish|restore|revisions|attachments))?',path)
        if match:
            aid,action=match.groups();row=db.execute('SELECT * FROM articles WHERE id=?',(aid,)).fetchone();require(row,'找不到文章。',404)
            if action=='revisions' and method=='GET':
                h.send_json(200,{'revisions':[dict(r) for r in db.execute('SELECT id,version,action,created_at FROM article_revisions WHERE article_id=? ORDER BY id DESC',(aid,))]});return
            if action=='attachments' and method=='POST': self.upload(h,db,aid);return
            require(method in ('PATCH','POST'),'不支援這個操作。',405)
            body=self.body(h)
            db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM articles WHERE id=?',(aid,)).fetchone()
            require(body.get('version')==row['version'],'文章已被其他頁面修改，請重新載入後再編輯。',409)
            payload=json.loads(row['draft']);status=row['status'];published=row['published']
            if action is None:
                payload=self.article_payload(body,db,aid);status=body.get('status','draft');require(status in ('draft','review'),'草稿狀態不正確。')
            elif action=='publish':
                require(payload['body'] or payload['attachments'],'請先填寫內文或加入附件。')
                payload['publicationVersion']=row['version']+1;published=json.dumps(payload,ensure_ascii=False);status='published'
            elif action=='unpublish': published=None;status='archived'
            elif action=='restore':
                revision=db.execute('SELECT payload FROM article_revisions WHERE id=? AND article_id=?',(body.get('revision'),aid)).fetchone();require(revision,'找不到這個版本。',404)
                payload=json.loads(revision['payload']);status='draft'
            else: raise ApiError(405,'不支援這個操作。')
            db.execute('INSERT INTO article_revisions(article_id,version,payload,action,created_at) VALUES(?,?,?,?,?)',(aid,row['version'],row['draft'],action or 'save',stamp()))
            db.execute('UPDATE articles SET draft=?,published=?,status=?,version=version+1,updated_at=? WHERE id=?',(json.dumps(payload,ensure_ascii=False),published,status,stamp(),aid))
            db.commit();h.send_json(200,self.article(db.execute('SELECT * FROM articles WHERE id=?',(aid,)).fetchone(),db));return
        if path.startswith('/api/files/') and method=='GET':
            fid=path.rsplit('/',1)[-1];row=db.execute('SELECT * FROM attachments WHERE id=?',(fid,)).fetchone();require(row,'找不到附件。',404)
            article=db.execute('SELECT published FROM articles WHERE id=?',(row['article_id'],)).fetchone()
            require(authenticated or (article['published'] and fid in json.loads(article['published'])['attachments']),'附件尚未發布。',404)
            file=self.uploads/fid;require(file.is_file(),'附件檔案遺失。',404)
            from urllib.parse import quote
            data=file.read_bytes();h.send_response(200);h.send_header('Content-Type',row['mime']);h.send_header('Content-Length',str(len(data)));h.send_header('X-Content-Type-Options','nosniff');h.send_header('Cache-Control','no-store');h.send_header('Content-Security-Policy',"sandbox; default-src 'none'")
            mode='inline' if row['mime'] in ('application/pdf','image/png','image/jpeg') else 'attachment'
            h.send_header('Content-Disposition',f"{mode}; filename*=UTF-8''{quote(row['name'])}");h.end_headers();h.wfile.write(data);return
        if path=='/api/admin/events':
            if method=='GET':
                rows=db.execute('SELECT e.id,e.code,e.title,e.date,e.status,COUNT(p.id) joined,SUM(CASE WHEN p.completed_at IS NOT NULL THEN 1 ELSE 0 END) completed FROM events e LEFT JOIN participants p ON p.event_id=e.id GROUP BY e.id ORDER BY e.date DESC').fetchall();h.send_json(200,{'events':[dict(r) for r in rows]});return
            if method=='POST':
                b=self.body(h);title=b.get('title','');date=b.get('date','');require(isinstance(title,str) and isinstance(date,str),'活動名稱與日期格式錯誤。');title=title.strip();require(1<=len(title)<=100,'請填寫活動名稱。')
                require(re.fullmatch(r'\d{4}-\d{2}-\d{2}',date),'活動日期格式錯誤。');datetime.strptime(date,'%Y-%m-%d')
                eid=str(uuid.uuid4());code=secrets.token_hex(3).upper();db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(eid,code,title,date,'open',json.dumps(self.seed['questions'],ensure_ascii=False),stamp()));db.commit();h.send_json(201,dict(id=eid,code=code,title=title,date=date,status='open'));return
        if path.startswith('/api/admin/events/') and method=='PATCH':
            b=self.body(h);require(b.get('status') in ('open','closed'),'活動狀態錯誤。');cursor=db.execute('UPDATE events SET status=? WHERE id=?',(b['status'],path.rsplit('/',1)[-1]));require(cursor.rowcount,'找不到活動。',404);db.commit();h.send_json(200,{'ok':True});return
        if path=='/api/events/today' and method=='GET':
            h.send_json(200,{'events':[dict(r) for r in db.execute("SELECT id,title,date FROM events WHERE date=? AND status='open'",(today(),))]});return
        if path=='/api/events/join' and method=='POST':
            b=self.body(h)
            db.execute('BEGIN IMMEDIATE')
            event=db.execute('SELECT * FROM events WHERE id=?',(b['eventId'],)).fetchone() if b.get('eventId') else db.execute('SELECT * FROM events WHERE code=?',(str(b.get('code','')).strip().upper(),)).fetchone()
            self.event_active(event)
            token=b.get('joinToken') or secrets.token_urlsafe(32)
            require(isinstance(token,str) and re.fullmatch(r'[A-Za-z0-9_-]{32,128}',token),'加入識別資料不正確。')
            previous=db.execute('SELECT * FROM participants WHERE token=?',(digest(token),)).fetchone()
            if previous:
                require(previous['event_id']==event['id'],'此加入紀錄屬於另一場活動。',409)
                h.send_json(200,dict(self.progress(previous,db),token=token));return
            name=b.get('name','');require(isinstance(name,str),'暱稱格式不正確。');name=name.strip();require(1<=len(name)<=18,'請輸入 1 至 18 字的暱稱。')
            role=b.get('role','visitor');require(role in ('visitor','scarf','doctor','nurse','surgeon','scrub'),'角色不正確。')
            color=b.get('color','#b97c87');require(isinstance(color,str) and re.fullmatch(r'#[0-9a-fA-F]{6}',color),'顏色格式錯誤。')
            pid,rid=str(uuid.uuid4()),str(uuid.uuid4())
            appearance=dict(style='scarf' if role=='visitor' else 'short',shirt=color,pants='#657a8d',skin='#edc6a7',hair='#654738')
            if 'appearance' in b:
                appearance=b['appearance']
                require(isinstance(appearance,dict) and appearance.get('style') in ('short','bob','scarf','cap','mask'),'髮型或配件不正確。')
                for key in ('shirt','pants','skin','hair'):
                    require(isinstance(appearance.get(key),str) and re.fullmatch(r'#[0-9a-fA-F]{6}',appearance[key]),'角色顏色格式錯誤。')
                appearance={key:appearance[key] for key in ('style','shirt','pants','skin','hair')}
            db.execute('INSERT INTO resident_profiles(id,status,display_name,role,appearance_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(rid,'joined',name,role,json.dumps(appearance),stamp(),stamp()))
            db.execute('INSERT INTO participants(id,event_id,profile_id,token,created_at) VALUES(?,?,?,?,?)',(pid,event['id'],rid,digest(token),stamp()))
            db.commit();row=db.execute('SELECT * FROM participants WHERE id=?',(pid,)).fetchone();h.send_json(201,dict(self.progress(row,db),token=token));return
        if path=='/api/events/residents' and method=='GET':
            h.send_json(200,self.resident_feed(db));return
        if path=='/api/events/navigation' and method=='GET':
            h.send_json(200,dict(self.world.data,walkable=sorted(self.world.cells)));return
        if re.fullmatch(r'/api/events/[a-f0-9-]{36}',path) and method=='GET':
            event=db.execute('SELECT id,title,date,status FROM events WHERE id=?',(path.rsplit('/',1)[-1],)).fetchone()
            require(event,'找不到這場活動，請重新掃描現場 QR Code。',404)
            h.send_json(200,dict(event,active=event['status']=='open' and event['date']==today()));return
        if path in ('/api/participant/control','/api/participant/control/release'):
            self.control(h,db);return
        if path in ('/api/participant','/api/participant/answer'):
            token=h.headers.get('Authorization','').removeprefix('Bearer ')
            row=db.execute('SELECT * FROM participants WHERE token=?',(digest(token),)).fetchone();require(row,'找不到參加紀錄，請重新加入活動。',401)
            if path=='/api/participant' and method=='GET': h.send_json(200,self.progress(row,db));return
            require(method=='POST','不支援這個操作。',405);b=self.body(h)
            db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM participants WHERE id=?',(row['id'],)).fetchone()
            event=db.execute('SELECT * FROM events WHERE id=?',(row['event_id'],)).fetchone();self.event_active(event)
            questions=json.loads(event['questions']);index=row['progress']
            if index>=len(questions): h.send_json(200,dict(self.progress(row,db),correct=True));return
            require(b.get('index')==index,'進度已更新，請重新載入目前題目。',409)
            choice=b.get('choice');require(type(choice) is int and 0<=choice<len(questions[index]['choices']),'請選擇一個答案。')
            correct=choice==questions[index]['answer'];progress=index+int(correct)
            db.execute('UPDATE participants SET progress=?,attempts=attempts+1,completed_at=? WHERE id=?',(progress,stamp() if progress==len(questions) else None,row['id']))
            db.commit();updated=db.execute('SELECT * FROM participants WHERE id=?',(row['id'],)).fetchone()
            h.send_json(200,dict(self.progress(updated,db),correct=correct,explanation=questions[index]['explanation'] if correct else '還不正確，請再想一想。',sources=questions[index].get('sources',[]) if correct else []));return
        raise ApiError(404,'找不到這項服務。')

    def resident_feed(self,db):
        rows=db.execute("SELECT r.id,r.display_name,r.role,r.appearance_json,p.completed_at FROM resident_profiles r JOIN participants p ON p.profile_id=r.id JOIN events e ON e.id=p.event_id LEFT JOIN player_positions w ON w.profile_id=r.id WHERE e.date=? AND e.status='open' ORDER BY CASE WHEN w.updated_at>? THEN 0 ELSE 1 END,p.created_at DESC LIMIT 12",(today(),time.time()-90)).fetchall()
        from hope_world import active_positions,position_dict
        positions={r['profile_id']:position_dict(r) for r in active_positions(db)}
        return {'serverTime':time.time(),'profiles':[dict(id=r['id'],displayName=r['display_name'],role=r['role'],appearance=json.loads(r['appearance_json']),completed=bool(r['completed_at']),position=positions.get(r['id'])) for r in rows]}

    def stream_residents(self,h):
        require(self.resident_updates.slots.acquire(blocking=False),'即時連線暫時額滿，將使用一般同步。',503)
        try:
            h.send_response(200)
            h.send_header('Content-Type','text/event-stream; charset=utf-8')
            h.send_header('Cache-Control','no-store')
            h.send_header('X-Accel-Buffering','no')
            h.send_header('Connection','close')
            h.end_headers();h.close_connection=True;h.connection.settimeout(10)
            h.wfile.write(b'retry: 500\n\n');h.wfile.flush()
            deadline=time.monotonic()+60
            while time.monotonic()<deadline:
                version=self.resident_updates.version
                db=self.connect()
                try:payload=self.resident_feed(db)
                finally:db.close()
                data=json.dumps(payload,ensure_ascii=False,separators=(',',':'))
                h.wfile.write(('event: residents\ndata: '+data+'\n\n').encode());h.wfile.flush()
                self.resident_updates.wait(version)
        except (BrokenPipeError,ConnectionResetError,TimeoutError,OSError):pass
        finally:self.resident_updates.slots.release()

    def control(self,h,db):
        from hope_world import active_positions,position_dict
        token=h.headers.get('Authorization','').removeprefix('Bearer ')
        db.execute('BEGIN IMMEDIATE')
        participant=db.execute('SELECT * FROM participants WHERE token=?',(digest(token),)).fetchone();require(participant,'請先掃描活動 QR Code 加入。',401)
        event=db.execute('SELECT * FROM events WHERE id=?',(participant['event_id'],)).fetchone();self.event_active(event)
        profile=participant['profile_id'];position=db.execute('SELECT * FROM player_positions WHERE profile_id=?',(profile,)).fetchone()
        others=[(r['x'],r['z']) for r in active_positions(db) if r['profile_id']!=profile]
        now=time.time()
        if urlsplit(h.path).path.endswith('/release'):
            require(h.command=='POST','請使用 POST。',405);self.body(h)
            db.execute('DELETE FROM player_positions WHERE profile_id=?',(profile,));db.commit();h.send_json(200,{'ok':True});return
        require(len(others)<7,'目前已有 7 位島民正在操控，請稍後再加入。',409)
        require(position or h.command=='GET','請重新開啟手機搖桿以取得操控權。',409)
        if not position:
            x,z=self.world.spawn(others)
            db.execute('INSERT INTO player_positions(profile_id,x,z,heading,sequence,updated_at) VALUES(?,?,?,0,0,?)',(profile,x,z,now))
            position=db.execute('SELECT * FROM player_positions WHERE profile_id=?',(profile,)).fetchone()
        if h.command=='GET':
            if position['updated_at']<now-90 and any(math.hypot(position['x']-o[0],position['z']-o[1])<.7 for o in others):
                x,z=self.world.spawn(others);db.execute('UPDATE player_positions SET x=?,z=? WHERE profile_id=?',(x,z,profile))
            db.execute('UPDATE player_positions SET updated_at=?,input_dx=0,input_dz=0 WHERE profile_id=?',(now,profile));position=db.execute('SELECT * FROM player_positions WHERE profile_id=?',(profile,)).fetchone()
        if h.command=='POST':
            body=self.body(h);dx,dz,sequence=body.get('dx'),body.get('dz'),body.get('sequence')
            require(all(type(v) in (int,float) and math.isfinite(v) and -1<=v<=1 for v in (dx,dz)),'移動方向不正確。')
            require(type(sequence) is int and 0<sequence<=9007199254740991,'移動序號不正確。')
            if sequence>position['sequence']:
                x,z=self.world.move(position['x'],position['z'],position['input_dx'],position['input_dz'],now-position['updated_at'] if now-position['updated_at']<.5 else 0,others)
                heading=math.atan2(dx,dz) if math.hypot(dx,dz)>.05 else position['heading']
                db.execute('UPDATE player_positions SET x=?,z=?,heading=?,sequence=?,updated_at=?,input_dx=?,input_dz=? WHERE profile_id=?',(x,z,heading,sequence,now,dx,dz,profile))
                position=db.execute('SELECT * FROM player_positions WHERE profile_id=?',(profile,)).fetchone()
        else:require(h.command=='GET','請使用 GET 或 POST。',405)
        result=dict(position=position_dict(position),profileId=profile)
        if h.command=='GET':result['participant']=self.progress(participant,db)
        db.commit();h.send_json(200,result)

    def agent_dispatch(self,h,path,db):
        token=h.headers.get('Authorization','').removeprefix('Bearer ')
        require(token.startswith('hope_agent_'),'請提供 Agent API 金鑰。',401)
        # Hold a transaction for authentication, optimistic updates, and idempotent retries.
        if h.command=='POST': db.execute('BEGIN IMMEDIATE')
        key=db.execute('SELECT * FROM agent_keys WHERE token_hash=? AND revoked_at IS NULL',(digest(token),)).fetchone()
        require(key,'API 金鑰無效或已撤銷。',401)
        if path=='/api/agent/categories' and h.command=='GET':
            h.send_json(200,{'categories':[{'id':s['id'],'name':s['name']} for s in self.seed['stations']]});return
        match=re.fullmatch(r'/api/agent/articles(?:/([a-f0-9-]{36}))?',path);require(match,'找不到 Agent API。',404)
        aid=match.group(1)
        row=db.execute('SELECT * FROM articles WHERE id=?',(aid,)).fetchone() if aid else None
        if aid:require(row,'找不到文章。',404)
        if h.command=='GET':
            if aid:h.send_json(200,self.article(row,db));return
            h.send_json(200,{'articles':[self.article(r,db) for r in db.execute('SELECT * FROM articles ORDER BY updated_at DESC')]});return
        require(h.command=='POST','請使用 GET 或 POST。',405)
        body=self.body(h)
        request_key=h.headers.get('Idempotency-Key','');require(len(request_key)<=128,'Idempotency-Key 最長 128 字元。')
        fingerprint=digest(path+'\n'+json.dumps(body,sort_keys=True,ensure_ascii=False))
        if request_key:
            cached=db.execute('SELECT * FROM agent_requests WHERE key_id=? AND request_key=?',(key['id'],request_key)).fetchone()
            if cached:
                require(cached['fingerprint']==fingerprint,'此 Idempotency-Key 已用於不同內容。',409)
                h.send_json(cached['status'],json.loads(cached['response']));return
        for field in ('title','category','body','references'):require(field in body,'缺少欄位：'+field)
        publish=body.get('publish',False);require(type(publish) is bool,'publish 請使用布林值。')
        if row:require(body.get('version')==row['version'],'文章已有更新，請 GET 最新版本後再修改。',409)
        aid=aid or str(uuid.uuid4());payload=self.article_payload(body,db,aid)
        if publish:require(payload['body'] or payload['attachments'],'發布前請填寫內文或加入附件。')
        version=row['version']+1 if row else 1
        if publish:payload['publicationVersion']=version
        published=json.dumps(payload,ensure_ascii=False) if publish else (row['published'] if row else None)
        status='published' if publish else 'draft'
        if row:
            db.execute('INSERT INTO article_revisions(article_id,version,payload,action,created_at) VALUES(?,?,?,?,?)',(aid,row['version'],row['draft'],'agent-publish' if publish else 'agent-save',stamp()))
            db.execute('UPDATE articles SET draft=?,published=?,status=?,version=?,updated_at=? WHERE id=?',(json.dumps(payload,ensure_ascii=False),published,status,version,stamp(),aid))
        else:
            db.execute('INSERT INTO articles VALUES(?,?,?,?,?,?)',(aid,json.dumps(payload,ensure_ascii=False),published,status,version,stamp()))
        result=self.article(db.execute('SELECT * FROM articles WHERE id=?',(aid,)).fetchone(),db)
        code=200 if row else 201
        if request_key:db.execute('INSERT INTO agent_requests VALUES(?,?,?,?,?)',(key['id'],request_key,fingerprint,json.dumps(result,ensure_ascii=False),code))
        db.execute('UPDATE agent_keys SET last_used_at=? WHERE id=?',(stamp(),key['id']))
        db.commit();h.send_json(code,result)

    def upload(self,h,db,aid):
        body=self.body(h,MAX_FILE*4//3+4096);name=body.get('name','')
        require(isinstance(name,str) and 1<=len(name)<=160 and '/' not in name and '\\' not in name and not any(ord(c)<32 for c in name),'附件名稱不正確。')
        try: data=base64.b64decode(body.get('data',''),validate=True)
        except (ValueError,TypeError): raise ApiError(400,'附件資料損毀。')
        require(0<len(data)<=MAX_FILE,'單一附件上限為 12 MB。',413)
        ext=Path(name).suffix.lower();mime=None
        if ext=='.pdf' and data.startswith(b'%PDF-'): mime='application/pdf'
        elif ext=='.png' and data.startswith(b'\x89PNG\r\n\x1a\n'): mime='image/png'
        elif ext in ('.jpg','.jpeg') and data.startswith(b'\xff\xd8\xff'): mime='image/jpeg'
        elif ext=='.docx':
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    require(len(z.infolist())<2000 and sum(i.file_size for i in z.infolist())<80*1024*1024,'Word 檔案解壓後過大。')
                    require('word/document.xml' in z.namelist() and '[Content_Types].xml' in z.namelist(),'Word 檔案格式不正確。')
                    require(not any('vbaProject' in i for i in z.namelist()),'不接受含巨集的檔案。')
                    mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            except zipfile.BadZipFile: raise ApiError(400,'Word 檔案格式不正確。')
        require(mime,'僅接受 PDF、DOCX、JPG 與 PNG，且內容須符合檔案格式。',415)
        require(db.execute('SELECT COUNT(*) FROM attachments WHERE article_id=?',(aid,)).fetchone()[0]<100,'這篇文章附件已達上限。')
        fid=str(uuid.uuid4());target=self.uploads/fid;target.write_bytes(data);target.chmod(0o600)
        try:
            db.execute('INSERT INTO attachments VALUES(?,?,?,?,?,?)',(fid,aid,name,mime,len(data),stamp()));db.commit()
        except Exception: target.unlink(missing_ok=True);raise
        h.send_json(201,dict(id=fid,name=name,mime=mime,size=len(data)))

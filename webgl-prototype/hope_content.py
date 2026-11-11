"""Article publishing and event participation, backed by the shared SQLite database."""
import base64
import hashlib
import hmac
import io
import json
import re
import secrets
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
        with connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS content_settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS admin_sessions(token TEXT PRIMARY KEY, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS articles(id TEXT PRIMARY KEY, draft TEXT NOT NULL, published TEXT, status TEXT NOT NULL DEFAULT 'draft', version INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS article_revisions(id INTEGER PRIMARY KEY, article_id TEXT NOT NULL REFERENCES articles(id), version INTEGER NOT NULL, payload TEXT NOT NULL, action TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attachments(id TEXT PRIMARY KEY, article_id TEXT NOT NULL REFERENCES articles(id), name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, title TEXT NOT NULL, date TEXT NOT NULL, status TEXT NOT NULL, questions TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS participants(id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id), profile_id TEXT NOT NULL REFERENCES resident_profiles(id), token TEXT NOT NULL UNIQUE, progress INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0, completed_at TEXT, created_at TEXT NOT NULL);
            ''')
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
        host = h.headers.get('Host', '').split(':')[0]
        require(host in ('127.0.0.1','localhost','[',h.server.server_address[0]), '主機名稱不允許，請使用伺服器的本機或院內位址。', 403)
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
        payload = {}
        for key, maximum in [('title',160),('body',100_000),('summary',600),('stage',60),('author',100),('reviewer',100),('source',1000)]:
            value = body.get(key, '')
            require(isinstance(value,str) and len(value)<=maximum, '文章欄位格式或長度不正確：'+key)
            payload[key] = value.strip()
        require(payload['title'], '請填寫文章標題。')
        stations = body.get('stations', [])
        require(isinstance(stations,list) and stations and all(type(s) is int and 0<=s<10 for s in stations), '請選擇至少一個科別。')
        payload['stations'] = sorted(set(stations))
        order = body.get('order',0)
        require(type(order) is int and 0<=order<=9999, '排序請輸入 0 至 9999。')
        payload['order'] = order
        ids = body.get('attachments',[])
        require(isinstance(ids,list) and len(ids)<=20 and all(isinstance(i,str) for i in ids), '附件格式不正確。')
        for i in ids: require(db.execute('SELECT 1 FROM attachments WHERE id=? AND article_id=?',(i,article_id)).fetchone(), '附件不屬於這篇文章。')
        payload['attachments'] = list(dict.fromkeys(ids))
        return payload

    def article(self, row, db, public=False):
        payload = json.loads(row['published'] if public else row['draft'])
        files = [dict(r) for r in db.execute('SELECT id,name,mime,size FROM attachments WHERE article_id=?',(row['id'],))]
        payload['files'] = [f for f in files if f['id'] in payload['attachments']]
        return dict(payload, id=row['id'], version=payload.get('publicationVersion',row['version']) if public else row['version'], status='published' if public else row['status'], updatedAt=row['updated_at'], hasPublished=bool(row['published']))

    def event_active(self, event):
        require(event and event['status']=='open' and event['date']==today(), '活動尚未開始或已結束，請洽現場工作人員。', 409)

    def progress(self, row, db):
        event = db.execute('SELECT * FROM events WHERE id=?',(row['event_id'],)).fetchone()
        questions = json.loads(event['questions']); index=row['progress']
        profile = db.execute('SELECT * FROM resident_profiles WHERE id=?',(row['profile_id'],)).fetchone()
        result=dict(id=row['id'],title=event['title'],date=event['date'],active=event['date']==today() and event['status']=='open',progress=index,total=len(questions),completedAt=row['completed_at'],name=profile['display_name'])
        if index<len(questions): result['question'] = {k:questions[index][k] for k in ('prompt','choices')}
        return result

    def handle(self, h):
        path = urlsplit(h.path).path
        if not (path.startswith('/api/admin/') or path.startswith('/api/education') or path.startswith('/api/files/') or path.startswith('/api/events/') or path.startswith('/api/participant')): return False
        try:
            if h.command!='GET': self.origin(h)
            with self.connect() as db: self.dispatch(h,path,db)
        except ApiError as e: h.send_json(e.status,{'error':e.message})
        except (ValueError, TypeError, KeyError): h.send_json(400,{'error':'欄位格式不正確，請檢查後重試。'})
        return True

    def dispatch(self,h,path,db):
        method=h.command; authenticated=self.session(h,db)
        configured=bool(db.execute("SELECT 1 FROM content_settings WHERE key='password'").fetchone())
        if path=='/api/admin/session' and method=='GET':
            h.send_json(200,dict(authenticated=authenticated,configured=configured,today=today()));return
        if path in ('/api/admin/setup','/api/admin/login') and method=='POST':
            require(h.client_address[0] in ('127.0.0.1','::1') or path.endswith('/login'), '首次設定請在伺服器本機操作。',403)
            body=self.body(h); password=body.get('password','')
            require(isinstance(password,str) and 12<=len(password)<=128,'管理密碼請使用 12 至 128 個字元。')
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
                require(payload['reviewer'],'發布前請填寫審閱者。')
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
                b=self.body(h);title=b.get('title','').strip();date=b.get('date','');require(1<=len(title)<=100,'請填寫活動名稱。')
                require(re.fullmatch(r'\d{4}-\d{2}-\d{2}',date),'活動日期格式錯誤。');datetime.strptime(date,'%Y-%m-%d')
                eid=str(uuid.uuid4());code=secrets.token_hex(3).upper();db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(eid,code,title,date,'open',json.dumps(self.seed['questions'],ensure_ascii=False),stamp()));db.commit();h.send_json(201,dict(id=eid,code=code,title=title,date=date,status='open'));return
        if path.startswith('/api/admin/events/') and method=='PATCH':
            b=self.body(h);require(b.get('status') in ('open','closed'),'活動狀態錯誤。');cursor=db.execute('UPDATE events SET status=? WHERE id=?',(b['status'],path.rsplit('/',1)[-1]));require(cursor.rowcount,'找不到活動。',404);db.commit();h.send_json(200,{'ok':True});return
        if path=='/api/events/today' and method=='GET':
            h.send_json(200,{'events':[dict(r) for r in db.execute("SELECT title,date FROM events WHERE date=? AND status='open'",(today(),))]});return
        if path=='/api/events/join' and method=='POST':
            b=self.body(h);event=db.execute('SELECT * FROM events WHERE code=?',(str(b.get('code','')).strip().upper(),)).fetchone();self.event_active(event)
            name=b.get('name','').strip();require(1<=len(name)<=18,'請輸入 1 至 18 字的暱稱。')
            role=b.get('role','visitor');require(role in ('visitor','scarf','doctor','nurse','surgeon','scrub'),'角色不正確。')
            color=b.get('color','#b97c87');require(isinstance(color,str) and re.fullmatch(r'#[0-9a-fA-F]{6}',color),'顏色格式錯誤。')
            pid,rid,token=str(uuid.uuid4()),str(uuid.uuid4()),secrets.token_urlsafe(32)
            appearance=dict(style='scarf' if role=='visitor' else 'short',shirt=color,pants='#657a8d',skin='#edc6a7',hair='#654738')
            db.execute('INSERT INTO resident_profiles(id,status,display_name,role,appearance_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(rid,'joined',name,role,json.dumps(appearance),stamp(),stamp()))
            db.execute('INSERT INTO participants(id,event_id,profile_id,token,created_at) VALUES(?,?,?,?,?)',(pid,event['id'],rid,digest(token),stamp()))
            db.commit();row=db.execute('SELECT * FROM participants WHERE id=?',(pid,)).fetchone();h.send_json(201,dict(self.progress(row,db),token=token));return
        if path=='/api/events/residents' and method=='GET':
            rows=db.execute("SELECT r.id,r.display_name,r.role,r.appearance_json,p.completed_at FROM resident_profiles r JOIN participants p ON p.profile_id=r.id JOIN events e ON e.id=p.event_id WHERE e.date=? AND e.status='open' ORDER BY p.created_at DESC LIMIT 12",(today(),)).fetchall()
            h.send_json(200,{'profiles':[dict(id=r['id'],displayName=r['display_name'],role=r['role'],appearance=json.loads(r['appearance_json']),completed=bool(r['completed_at'])) for r in rows]});return
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

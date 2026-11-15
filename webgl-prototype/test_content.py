import base64
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from hope_content import ContentService,today

class ContentTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('hope_server',Path(__file__).with_name('hope-server.py'));self.app=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.app)
        self.tmp=tempfile.TemporaryDirectory();self.app.DATA_DIR=Path(self.tmp.name);self.app.DB_PATH=self.app.DATA_DIR/'test.sqlite3';self.app.initialize();self.app.CONTENT=ContentService(self.app.connect,self.app.DATA_DIR,Path(__file__).with_name('education-seed.json'))
        self.app.Handler.log_message=lambda *a:None
        self.server=ThreadingHTTPServer(('127.0.0.1',0),self.app.Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.cookie='';self.token=''
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,path,method='GET',body=None,auth=True,origin=True,extra_headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port);headers={}
        if body is not None:headers['Content-Type']='application/json'
        if auth and self.cookie:headers['Cookie']=self.cookie
        if self.token:headers['Authorization']='Bearer '+self.token
        if origin:headers['Origin']=f'http://127.0.0.1:{self.server.server_port}'
        headers.update(extra_headers or {})
        conn.request(method,path,json.dumps(body) if body is not None else None,headers);r=conn.getresponse();data=r.read();cookie=r.getheader('Set-Cookie');status=r.status
        if cookie:self.cookie=cookie.split(';')[0]
        conn.close()
        try:data=json.loads(data)
        except (ValueError,UnicodeError):pass
        return status,data
    def setup_admin(self):self.assertEqual(self.request('/api/admin/setup','POST',{'password':'test-password-long-enough'})[0],200)
    def article(self):
        status,a=self.request('/api/admin/articles','POST',dict(title='測試 <script>標題',body='衛教內容',stations=[1],reviewer='測試審閱者',attachments=[]));self.assertEqual(status,201);return a
    def test_auth_publication_attachments_revisions_and_persistence(self):
        self.assertEqual(self.request('/api/admin/articles','POST',{},auth=False)[0],401)
        self.assertEqual(self.request('/api/admin/setup','POST',{'password':'test-password-long-enough'},origin=False)[0],403)
        self.setup_admin();a=self.article();path='/api/admin/articles/'+a['id']
        self.assertEqual(self.request('/api/education',auth=False)[1]['articles'],[])
        status,f=self.request(path+'/attachments','POST',{'name':'test.pdf','data':base64.b64encode(b'%PDF-1.4\n%%EOF').decode()});self.assertEqual(status,201)
        self.assertEqual(self.request('/api/files/'+f['id'],auth=False)[0],404)
        self.assertEqual(self.request(path+'/attachments','POST',{'name':'fake.png','data':base64.b64encode(b'<script>alert(1)</script>').decode()})[0],415)
        status,a=self.request(path,'PATCH',{**a,'attachments':[f['id']]});self.assertEqual(status,200)
        status,a=self.request(path+'/publish','POST',{'version':a['version']});self.assertEqual(status,200)
        public=self.request('/api/education',auth=False)[1]['articles'][0];self.assertEqual(public['files'][0]['id'],f['id'])
        status,draft=self.request(path,'PATCH',{**a,'body':'新版草稿','status':'draft'});self.assertEqual(status,200)
        still_public=self.request('/api/education',auth=False)[1]['articles'][0];self.assertEqual(still_public['body'],'衛教內容');self.assertEqual(still_public['version'],public['version'])
        self.assertEqual(self.request(path,'PATCH',a)[0],409)
        self.app.CONTENT=ContentService(self.app.connect,self.app.DATA_DIR,Path(__file__).with_name('education-seed.json'))
        self.assertEqual(self.request('/api/education',auth=False)[1]['articles'][0]['body'],'衛教內容')
        revisions=self.request(path+'/revisions')[1]['revisions'];self.assertTrue(revisions)
        status,restored=self.request(path+'/restore','POST',{'version':draft['version'],'revision':revisions[0]['id']});self.assertEqual(status,200);self.assertEqual(restored['body'],'衛教內容')
        self.assertEqual(self.request(path+'/unpublish','POST',{'version':restored['version']})[0],200)
        self.assertEqual(self.request('/api/files/'+f['id'],auth=False)[0],404)
    def test_event_correct_answers_resume_and_close(self):
        self.setup_admin();status,event=self.request('/api/admin/events','POST',{'title':'測試活動','date':today()});self.assertEqual(status,201)
        status,joined=self.request('/api/events/join','POST',{'code':event['code'],'name':'測試島民','role':'visitor','color':'#abcdef'},auth=False);self.assertEqual(status,201);self.token=joined['token']
        self.assertNotIn('answer',joined['question']);self.assertEqual(self.request('/api/participant/answer','POST',{'index':2,'choice':1})[0],409)
        self.assertFalse(self.request('/api/participant/answer','POST',{'index':0,'choice':1})[1]['correct'])
        self.assertEqual(self.request('/api/participant')[1]['progress'],0)
        for i,answer in enumerate([0,1,1]):
            status,result=self.request('/api/participant/answer','POST',{'index':i,'choice':answer},auth=False);self.assertEqual(status,200);self.assertTrue(result['correct']);self.assertEqual(result['progress'],i+1)
        self.assertTrue(result['completedAt']);self.assertEqual(self.request('/api/participant')[1]['progress'],3)
        self.assertEqual(self.request('/api/participant/answer','POST',{'index':2,'choice':1})[1]['progress'],3)
        self.assertEqual(self.request('/api/admin/events')[1]['events'][0]['completed'],1)
        self.assertEqual(self.request('/api/events/residents')[1]['profiles'][0]['displayName'],'測試島民')
        self.request('/api/admin/events/'+event['id'],'PATCH',{'status':'closed'})
        self.assertEqual(self.request('/api/events/join','POST',{'code':event['code'],'name':'測試'})[0],409)
        self.assertEqual(self.request('/api/events/residents')[1]['profiles'],[])


    def test_qr_event_context_full_appearance_and_retry(self):
        self.assertEqual(self.request('/api/admin/setup','POST',{'password':'qa-test8'})[0],200)
        self.request('/api/admin/logout','POST',{})
        self.assertEqual(self.request('/api/admin/login','POST',{'password':'qa-test8'})[0],200)
        self.assertEqual(self.request('/api/admin/entry','PATCH',{'url':'http://localhost:8001'})[0],400)
        self.assertEqual(self.request('/api/admin/entry','PATCH',{'url':'javascript:alert(1)'})[0],400)
        self.assertEqual(self.request('/api/admin/entry','PATCH',{'url':'http://192.168.1.100:8001'})[1]['url'],'http://192.168.1.100:8001')
        event=self.request('/api/admin/events','POST',{'title':'QR 活動','date':today()})[1]
        context=self.request('/api/events/'+event['id'],auth=False)[1]
        self.assertTrue(context['active']);self.assertNotIn('questions',context)
        self.assertEqual(self.request('/api/events/today')[1]['events'][0]['id'],event['id'])
        appearance=dict(style='bob',shirt='#123456',pants='#234567',hair='#345678',skin='#abcdef')
        payload=dict(eventId=event['id'],name='小晴',role='nurse',appearance=appearance,joinToken='a'*64)
        status,joined=self.request('/api/events/join','POST',payload,auth=False)
        self.assertEqual(status,201);self.assertEqual(joined['appearance'],appearance);self.assertEqual(joined['eventId'],event['id'])
        self.assertEqual(self.request('/api/events/join','POST',payload,auth=False)[1]['id'],joined['id'])
        self.assertEqual(self.request('/api/admin/events')[1]['events'][0]['joined'],1)
        resident=self.request('/api/events/residents')[1]['profiles'][0];self.assertEqual(resident['appearance'],appearance);self.assertEqual(resident['role'],'nurse')
        self.token=joined['token'];self.assertEqual(self.request('/api/participant')[1]['appearance'],appearance)
        bad={**payload,'joinToken':'b'*64,'appearance':{**appearance,'style':'invalid'}}
        self.assertEqual(self.request('/api/events/join','POST',bad)[0],400)
        self.request('/api/admin/events/'+event['id'],'PATCH',{'status':'closed'})
        self.assertFalse(self.request('/api/events/'+event['id'])[1]['active'])
        self.assertEqual(self.request('/api/events/join','POST',{**payload,'joinToken':'c'*64})[0],409)
        self.assertEqual(self.request('/api/events/'+'0'*36)[0],404)


    def test_simple_editor_and_scoped_agent_post(self):
        self.setup_admin()
        status,key=self.request('/api/admin/api-keys','POST',{'label':'測試 Agent'});self.assertEqual(status,201)
        self.assertNotIn('key',self.request('/api/admin/api-keys')[1]['keys'][0])
        self.token=key['key']
        body=dict(title='四欄位 API 測試',category='病理科',body='測試內文',references='參考一\nhttps://example.org/source')
        headers={'Idempotency-Key':'create-article-1'}
        status,a=self.request('/api/agent/articles','POST',body,auth=False,origin=False,extra_headers=headers);self.assertEqual(status,201);self.assertEqual(a['category'],0);self.assertEqual(a['references'],body['references']);self.assertEqual(a['status'],'draft')
        retry=self.request('/api/agent/articles','POST',body,auth=False,origin=False,extra_headers=headers);self.assertEqual(retry[1]['id'],a['id'])
        self.assertEqual(self.request('/api/agent/articles','POST',{**body,'title':'不同內容'},origin=False,extra_headers=headers)[0],409)
        self.assertEqual(self.request('/api/admin/events',auth=False)[0],401)
        status,updated=self.request('/api/agent/articles/'+a['id'],'POST',{**body,'body':'更新內文','version':a['version'],'publish':True},auth=False,origin=False);self.assertEqual(status,200)
        public=self.request('/api/education',auth=False)[1]['articles'][0];self.assertEqual(public['body'],'更新內文');self.assertEqual(public['references'],body['references'])
        self.assertEqual(self.request('/api/agent/articles/'+a['id'],'POST',{**body,'version':a['version']},origin=False)[0],409)
        self.assertEqual(self.request('/api/agent/articles','POST',{**body,'category':'不存在'},origin=False)[0],400)
        self.assertEqual(len(self.request('/api/agent/categories',auth=False,origin=False)[1]['categories']),10)
        self.request('/api/admin/api-keys/'+key['id'],'DELETE')
        self.assertEqual(self.request('/api/agent/articles',auth=False,origin=False)[0],401)
        self.token=''
        self.assertEqual(self.request('/api/agent/articles','POST',body,auth=True,origin=False)[0],401,'admin cookies must not authorize the Agent route')
        status,draft=self.request('/api/admin/articles','POST',body);self.assertEqual(status,201)
        status,old=self.request('/api/admin/articles/'+draft['id'],'PATCH',{**draft,'author':'既有作者','summary':'既有摘要','order':5});self.assertEqual(status,200)
        status,simple=self.request('/api/admin/articles/'+draft['id'],'PATCH',{**body,'title':'簡化編輯','version':old['version']});self.assertEqual(status,200);self.assertEqual(simple['author'],'既有作者');self.assertEqual(simple['summary'],'既有摘要');self.assertEqual(simple['order'],5)
        self.assertEqual(self.request('/api/admin/articles/'+draft['id']+'/publish','POST',{'version':simple['version']})[0],200)


    def test_phone_control_is_owned_shared_bounded_and_releasable(self):
        import math,time
        self.setup_admin();event=self.request('/api/admin/events','POST',{'title':'多人操控測試','date':today()})[1]
        participants=[]
        for name in ['甲','乙']:
            participants.append(self.request('/api/events/join','POST',{'eventId':event['id'],'name':name,'role':'visitor'},auth=False)[1])
        self.token=participants[0]['token'];status,a=self.request('/api/participant/control');self.assertEqual(status,200)
        self.token=participants[1]['token'];b=self.request('/api/participant/control')[1]
        self.assertGreaterEqual(math.hypot(a['position']['x']-b['position']['x'],a['position']['z']-b['position']['z']),.9)
        self.token=participants[0]['token'];start=a['position'];other=b['position'];world=self.app.CONTENT.world
        directions=[(1,0),(-1,0),(0,1),(0,-1)]
        dx,dz=max(directions,key=lambda d:math.dist((start['x'],start['z']),world.move(start['x'],start['z'],*d,.25,[(other['x'],other['z'])])))
        first=self.request('/api/participant/control','POST',{'dx':dx,'dz':dz,'sequence':1})[1]
        self.assertEqual((first['position']['x'],first['position']['z']),(start['x'],start['z']),'starting must not walk through the previous idle interval')
        with self.app.connect() as db:db.execute('UPDATE player_positions SET updated_at=? WHERE profile_id=?',(time.time()-.25,a['profileId']))
        status,moved=self.request('/api/participant/control','POST',{'dx':dx,'dz':dz,'sequence':2,'profileId':b['profileId'],'x':9999});self.assertEqual(status,200)
        distance=math.dist((start['x'],start['z']),(moved['position']['x'],moved['position']['z']));self.assertGreater(distance,0);self.assertLessEqual(distance,.500001)
        self.assertTrue(world.allowed(moved['position']['x'],moved['position']['z']))
        repeated=self.request('/api/participant/control','POST',{'dx':dx,'dz':dz,'sequence':2})[1];self.assertEqual(repeated['position'],moved['position'])
        self.token=participants[1]['token'];self.assertEqual(self.request('/api/participant/control')[1]['position']['x'],other['x'])
        feed=self.request('/api/events/residents')[1]['profiles'];self.assertEqual(len([p for p in feed if p['position']]),2)
        self.token=participants[0]['token'];self.assertEqual(self.request('/api/participant/control','POST',{'dx':2,'dz':0,'sequence':2})[0],400)
        self.assertEqual(self.request('/api/participant/control','POST',{'dx':float('nan'),'dz':0,'sequence':2})[0],400)
        self.assertEqual(self.request('/api/participant/control/release','POST',{})[0],200)
        self.assertEqual(self.request('/api/participant/control','POST',{'dx':1,'dz':0,'sequence':2})[0],409)
        self.request('/api/admin/events/'+event['id'],'PATCH',{'status':'closed'})
        self.assertEqual(self.request('/api/participant/control')[0],409)
        self.token='invalid';self.assertEqual(self.request('/api/participant/control')[0],401)

    def test_phone_capacity_expiry_and_priority_in_display_feed(self):
        self.setup_admin();event=self.request('/api/admin/events','POST',{'title':'容量測試','date':today()})[1]
        users=[]
        for i in range(8):
            user=self.request('/api/events/join','POST',{'eventId':event['id'],'name':str(i)})[1];users.append(user);self.token=user['token']
            self.assertEqual(self.request('/api/participant/control')[0],200 if i<7 else 409)
        # New attendees must not push active controllers out of the visible seven seats.
        for i in range(8):self.request('/api/events/join','POST',{'eventId':event['id'],'name':'新加入'+str(i)})
        feed=self.request('/api/events/residents')[1]['profiles'];self.assertTrue(all(p['position'] for p in feed[:7]))
        with self.app.connect() as db:db.execute('UPDATE player_positions SET updated_at=0')
        self.token=users[-1]['token'];self.assertEqual(self.request('/api/participant/control')[0],200)

    def test_existing_control_positions_survive_realtime_schema_upgrade(self):
        import sqlite3
        from hope_world import initialize_world
        db=sqlite3.connect(':memory:')
        try:
            db.execute('CREATE TABLE player_positions(profile_id TEXT PRIMARY KEY,x REAL,z REAL,heading REAL,sequence INTEGER,updated_at REAL)')
            db.execute("INSERT INTO player_positions VALUES('old',1,2,.5,17,123)")
            initialize_world(db);initialize_world(db)
            row=db.execute('SELECT x,z,sequence,input_dx,input_dz FROM player_positions').fetchone()
            self.assertEqual(row,(1,2,17,0,0))
        finally:db.close()

    def test_resident_stream_pushes_committed_control_stop_and_closed_event(self):
        self.setup_admin();event=self.request('/api/admin/events','POST',{'title':'推送測試','date':today()})[1]
        joined=self.request('/api/events/join','POST',{'eventId':event['id'],'name':'即時島民'})[1];self.token=joined['token']
        owned=self.request('/api/participant/control')[1]
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        conn.request('GET','/api/events/resident-stream');response=conn.getresponse();self.assertEqual(response.status,200)
        def next_event():
            while True:
                line=response.readline()
                if line.startswith(b'data: '):return json.loads(line[6:])
        try:
            initial=next_event();self.assertEqual(initial['profiles'][0]['id'],owned['profileId']);self.assertNotIn(joined['token'],json.dumps(initial))
            self.request('/api/participant/control','POST',{'dx':0,'dz':1,'sequence':1})
            moving=next_event();self.assertEqual(moving['profiles'][0]['position']['sequence'],1);self.assertEqual(moving['profiles'][0]['position']['dz'],1)
            self.request('/api/participant/control','POST',{'dx':0,'dz':0,'sequence':2})
            stopped=next_event();self.assertEqual(stopped['profiles'][0]['position']['sequence'],2);self.assertEqual(stopped['profiles'][0]['position']['dz'],0)
            self.request('/api/admin/events/'+event['id'],'PATCH',{'status':'closed'})
            self.assertEqual(next_event()['profiles'],[])
        finally:response.close();conn.close()

if __name__=='__main__':unittest.main()

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
    def request(self,path,method='GET',body=None,auth=True,origin=True):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port);headers={}
        if body is not None:headers['Content-Type']='application/json'
        if auth and self.cookie:headers['Cookie']=self.cookie
        if self.token:headers['Authorization']='Bearer '+self.token
        if origin:headers['Origin']=f'http://127.0.0.1:{self.server.server_port}'
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

if __name__=='__main__':unittest.main()

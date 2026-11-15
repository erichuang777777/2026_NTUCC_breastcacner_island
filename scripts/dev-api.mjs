// Local cloud-runtime validation. Uses isolated PGlite and filesystem blobs, not production SQLite.
import {createServer} from 'node:http';
import {readFile,writeFile,mkdir,unlink} from 'node:fs/promises';
import path from 'node:path';
import {Readable} from 'node:stream';
import {PGlite} from '@electric-sql/pglite';
import seed from '../webgl-prototype/education-seed.json' with {type:'json'};
import map from '../webgl-prototype/server-assets/walkable-v22.json' with {type:'json'};
import {createApp} from '../server/app.mjs';
import {IslandWorld} from '../server/world.mjs';
const dir=path.resolve(process.env.HOPE_DEV_DATA||'.netlify/hope-dev');await mkdir(dir,{recursive:true});const database=new PGlite(dir+'/postgres');await database.exec(await readFile('netlify/database/migrations/202611150001_initial.sql','utf8'));
let queue=Promise.resolve();const serialize=fn=>{const result=queue.then(fn);queue=result.catch(()=>{});return result;};
const query=(s,a=[])=>database.query(s,a).then(r=>({...r,rowCount:r.affectedRows??r.rows.length}));
const db={query:(s,a)=>serialize(()=>query(s,a)),transaction:fn=>serialize(()=>database.transaction(tx=>fn(async(s,a=[])=>{const r=await tx.query(s,a);return {...r,rowCount:r.affectedRows??r.rows.length};})))};
const blobs={set:async(k,data)=>{const f=path.join(dir,'blobs',k);await mkdir(path.dirname(f),{recursive:true});await writeFile(f,Buffer.from(data));},get:async(k,{type})=>{try{const data=await readFile(path.join(dir,'blobs',k));return type==='stream'?new Blob([data]).stream():data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength);}catch(e){if(e.code==='ENOENT')return null;throw e;}},delete:k=>unlink(path.join(dir,'blobs',k)).catch(e=>{if(e.code!=='ENOENT')throw e;})};
const app=createApp({db,store:()=>blobs,seed,world:new IslandWorld(map)}),publicRoot=path.resolve('public');
const server=createServer(async(req,res)=>{try{const url=new URL(req.url,'http://'+req.headers.host);if(!url.pathname.startsWith('/api/')){const f=path.resolve(publicRoot,'.'+decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname));if(!f.startsWith(publicRoot+path.sep))throw Error('Invalid path');const data=await readFile(f);res.setHeader('Content-Type',({'.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.html':'text/html','.json':'application/json','.glb':'model/gltf-binary','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp'})[path.extname(f)]||'application/octet-stream');res.end(data);return;}const abort=new AbortController();res.on('close',()=>abort.abort());const request=new Request(url,{method:req.method,headers:req.headers,signal:abort.signal,...(['GET','HEAD'].includes(req.method)?{}:{body:Readable.toWeb(req),duplex:'half'})});const response=await app(request,{ip:req.socket.remoteAddress});res.writeHead(response.status,Object.fromEntries(response.headers));if(response.body)Readable.fromWeb(response.body).pipe(res);else res.end();}catch{if(!res.headersSent)res.writeHead(404);res.end('Not found');}});server.listen(Number(process.env.PORT||8002),'127.0.0.1',()=>console.log('Cloud API preview: http://127.0.0.1:'+server.address().port));

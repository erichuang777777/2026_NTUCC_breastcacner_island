import {createWishStore} from './hope-wish-store.js';
// The cloud is authoritative; local mode is used only when a local server explicitly lacks this API.
export function createCloudWishStore(storage,{fetcher=fetch,onChange=()=>{},onCompleted=()=>{}}={}){
 const local=createWishStore(storage);let wishes=[],mode='connecting',persistent=false,seen=new Map(),started=false,busy=false;
 async function request(path,method='GET',data){const r=await fetcher(path,{method,headers:data?{'Content-Type':'application/json'}:{},body:data?JSON.stringify(data):undefined,cache:'no-store',signal:AbortSignal.timeout(5000)});if(r.status===404&&mode==='connecting'&&['localhost','127.0.0.1','::1'].includes(location.hostname)){mode='local';wishes=local.wishes;persistent=local.persistent;return null;}const b=await r.json();if(!r.ok)throw Error(b.error||'願望尚未保存，請重試。');return b;}
 async function refresh(){if(busy||mode==='local')return;busy=true;try{const b=await request('/api/wishes');if(!b){onChange();return;}mode='cloud';persistent=true;const completed=[];for(const w of b.wishes){if(started&&seen.get(w.id)==='lit'&&w.status==='completed')completed.push(w.id);seen.set(w.id,w.status);}wishes=b.wishes;started=true;onChange();for(const id of completed)onCompleted(id);}catch{persistent=false;onChange();}finally{busy=false;}}
 const initial=refresh();
 return {get wishes(){return mode==='local'?local.wishes:wishes;},get persistent(){return mode==='local'?local.persistent:persistent;},get mode(){return mode;},refresh,
  async add(text,island,id){await initial;if(mode==='local')return local.add(text,island,id,{requirePersistence:true});const w={id,text:String(text).trim(),island,status:'lit',createdAt:new Date().toISOString(),canEdit:true};await request('/api/wishes','POST',w);wishes=wishes.filter(item=>item.id!==id);wishes.push(w);seen.set(id,'lit');mode='cloud';persistent=true;return w;},
  async complete(id){await initial;if(mode==='local')return local.complete(id);const w=wishes.find(w=>w.id===id);if(!w||w.status!=='lit'||!w.canEdit)return false;await request('/api/wishes/'+id,'PATCH',{status:'completed'});w.status='completed';seen.set(id,'completed');return true;},
  async archive(id){if(mode==='local')return local.archive(id);const w=wishes.find(w=>w.id===id);if(!w)return false;if(w.canEdit)await request('/api/wishes/'+id,'PATCH',{status:'archived'});w.status='archived';seen.set(id,'archived');return true;}
 };
}

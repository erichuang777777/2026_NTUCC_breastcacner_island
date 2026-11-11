import * as THREE from 'three';
import {characterStyles} from './hope-characters.js?v=16';
import {loadAvatarLibrary,createAvatar} from './hope-avatar.js?v=20';

const $=id=>document.getElementById(id),form=$('profile-form'),role=$('role'),style=$('style'),message=$('message'),list=$('profile-list');
const canvas=$('avatar-preview'),renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(32,1,.1,50);camera.position.set(1.25,1.40,3.25);camera.lookAt(0,.80,0);scene.add(new THREE.HemisphereLight('#fff8e7','#75847a',2.2));
const sun=new THREE.DirectionalLight('#fff0d4',3);sun.position.set(-3,7,5);scene.add(sun);
let avatar=null,editingId=null;
function config(){return {style:style.value,skin:$('skin').value,hair:$('hair').value,shirt:$('shirt').value,pants:$('pants').value};}
let previewAvatar=null,castReady=false;
function drawAvatar(){
 if(!castReady)return;
 previewAvatar?.dispose();previewAvatar=createAvatar(role.selectedIndex,config());avatar=previewAvatar.person;scene.add(avatar);
}
function resize(){const r=canvas.getBoundingClientRect();renderer.setSize(Math.max(1,r.width),Math.max(1,r.height),false);camera.aspect=r.width/Math.max(1,r.height);camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(canvas.parentElement);resize();
let last=performance.now();function frame(now){requestAnimationFrame(frame);const dt=Math.max(0,Math.min(.05,(now-last)/1000));last=now;if(avatar)avatar.rotation.y=Math.sin(now*.00022)*.16;previewAvatar?.update(dt);renderer.render(scene,camera);}requestAnimationFrame(frame);
for(const control of form.querySelectorAll('select,input'))control.addEventListener('input',drawAvatar);
role.addEventListener('change',()=>{const spec=characterStyles[role.selectedIndex];$('role-description').textContent=spec.description||'';if(editingId){drawAvatar();return;}style.value=spec.style==='doctor'?'short':spec.style;$('shirt').value=spec.shirt;$('pants').value=spec.pants;$('hair').value=spec.hair;drawAvatar();});
$('reset-form').onclick=()=>{editingId=null;form.reset();role.dispatchEvent(new Event('change'));message.textContent='已重設角色外觀。';};

function profilePayload(){return {displayName:$('display-name').value,role:role.value,appearance:config()};}
async function request(url,options={}){const response=await fetch(url,{...options,headers:{'content-type':'application/json',...(options.headers||{})}});const body=await response.json();if(!response.ok)throw new Error(body.error||'資料服務目前無法使用。');return body;}
async function refreshProfiles(){try{const {profiles}=await request('/api/profiles?status=draft');$('db-status').innerHTML='<span class="status-dot"></span>共用資料庫已連線';list.replaceChildren();if(!profiles.length){const p=document.createElement('p');p.className='muted';p.textContent='還沒有角色草稿。儲存後會顯示在這裡。';list.append(p);return;}
 for(const p of profiles){const row=document.createElement('article');row.className='profile';const info=document.createElement('div'),name=document.createElement('strong'),meta=document.createElement('small'),actions=document.createElement('div');actions.className='profile-actions';name.textContent=p.displayName||characterStyles.find(x=>x.id===p.role)?.name||'島民';meta.textContent='草稿・尚未加入島嶼';info.append(name,meta);const edit=document.createElement('button');edit.type='button';edit.textContent='編輯';edit.onclick=()=>loadProfile(p);const del=document.createElement('button');del.type='button';del.textContent='刪除';del.onclick=async()=>{if(!confirm('刪除這份尚未加入的角色草稿？'))return;try{await request('/api/profiles/'+p.id,{method:'DELETE'});await refreshProfiles();}catch(e){message.textContent=e.message;}};actions.append(edit,del);row.append(info,actions);list.append(row);}
 }catch(e){$('db-status').textContent='共用資料庫尚未啟動';list.replaceChildren();const p=document.createElement('p');p.className='note';p.textContent='請先啟動希望島共用服務：python3 hope-server.py --port 8001，然後由 http://127.0.0.1:8001/resident-setup.html 開啟此頁。';list.append(p);}}
function loadProfile(p){editingId=p.id;$('display-name').value=p.displayName;role.value=p.role;for(const key of ['style','skin','hair','shirt','pants'])$(key).value=p.appearance[key];$('role-description').textContent=characterStyles[role.selectedIndex]?.description||'';drawAvatar();message.textContent='正在編輯已儲存的草稿。';scrollTo({top:0,behavior:'smooth'});}
form.onsubmit=async e=>{e.preventDefault();message.textContent='正在儲存…';try{const body=JSON.stringify(profilePayload());const result=await request(editingId?'/api/profiles/'+editingId:'/api/profiles',{method:editingId?'PATCH':'POST',body});editingId=result.profile.id;message.textContent='已儲存至共用資料庫。這份角色仍是草稿，尚未加入投影場景。';await refreshProfiles();}catch(error){message.textContent=error.message;}};
role.dispatchEvent(new Event('change'));loadAvatarLibrary().then(()=>{castReady=true;drawAvatar();}).catch(error=>{message.textContent='角色預覽載入失敗，請重新整理。';console.error(error);});refreshProfiles();

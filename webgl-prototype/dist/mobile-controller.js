import {connectResidentFeed} from './hope-resident-feed.js?v=24';
import {gridAllows,createMovementPredictor} from './hope-movement-prediction.js?v=24';
import {createControlPump} from './hope-control-pump.js?v=23';
const $=id=>document.getElementById(id),eventId=new URLSearchParams(location.search).get('event'),token=sessionStorage.getItem(eventId?'hopeEventParticipant:'+eventId:'hopeEventParticipantV1');
let position=null,profileId=null,vector={dx:0,dz:0},sequence=0,ready=false,lastSent=0,stopped=false,pointer=null,povFrame=null,povHeading=0,viewMode='map',predictor=null,displayPosition=null,residents=[],residentFeed=null;
async function api(path,data){
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),2500);
 try{const response=await fetch('/api/'+path,{method:data?'POST':'GET',headers:{Authorization:'Bearer '+token,...(data?{'Content-Type':'application/json'}:{})},body:data?JSON.stringify(data):undefined,cache:'no-store',signal:controller.signal});const body=await response.json();if(!response.ok)throw Object.assign(Error(body.error||'連線暫時中斷。'),{status:response.status});return body;}
 catch(error){if(error.name==='AbortError')throw Error('連線較慢，正在重新連線。');throw error;}
 finally{clearTimeout(timeout);}
}
function showPosition(p,sentAt=performance.now()){position=p;predictor?.acknowledge(p,sentAt);if(!predictor)displayPosition=p;$('position-text').textContent='● 這是你的位置';publishView();}
function setVector(dx,dz){const length=Math.hypot(dx,dz);if(length>1){dx/=length;dz/=length;}vector={dx,dz};const world=worldVector();predictor?.input(world.dx,world.dz);$('stick').style.transform=`translate(${dx*47}px,${dz*47}px)`;}
function stop(){pointer=null;setVector(0,0);send(true);}
function worldVector(){if(viewMode!=='pov')return {...vector};return {dx:-Math.cos(povHeading)*vector.dx-Math.sin(povHeading)*vector.dz,dz:Math.sin(povHeading)*vector.dx-Math.cos(povHeading)*vector.dz};}
const pump=createControlPump({send:async()=>{
 if(!ready||stopped)return;
 const sentAt=performance.now();lastSent=sentAt;
 try{const data=await api('participant/control',{...worldVector(),sequence:++sequence});sequence=Math.max(sequence,data.position.sequence);showPosition(data.position,sentAt);$('connection').textContent='操控已連線';$('message').textContent='';}
 catch(error){$('connection').textContent='等待重新連線';$('message').textContent=error.message;if(error.status===401||error.status===409){ready=false;setVector(0,0);closePOV();$('controls').hidden=true;$('join-prompt').hidden=false;$('join-link').textContent='重新連線';$('join-link').href=location.href;}}
}});
function send(force=false){if(!ready||stopped||document.hidden&&!force)return;const idle=vector.dx===0&&vector.dz===0;if(!force&&idle&&performance.now()-lastSent<1000)return;pump.request(force&&idle);}
function publishView(){if(povFrame&&position)povFrame.contentWindow?.postMessage({type:'hope-pov-state',profileId,position:displayPosition||position},location.origin);}
function publishResidents(){povFrame?.contentWindow?.postMessage({type:'hope-pov-residents',profiles:residents},location.origin);}
function closePOV(){povFrame?.remove();povFrame=null;viewMode='map';$('pov-card').hidden=true;$('map-card').hidden=false;}
function setView(mode){stop();closePOV();viewMode=mode;
 document.querySelectorAll('[data-controller-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.controllerView===mode)));
 $('movement-hint').textContent=mode==='pov'?'往上推前進、往下推後退；拖曳風景轉頭。':'方向依上方地圖：上北、下南。放開就停止。';
 if(mode==='pov'){$('map-card').hidden=true;$('pov-card').hidden=false;$('pov-loading').hidden=false;povHeading=position?.heading||0;povFrame=document.createElement('iframe');povFrame.title='我的角色第一人稱視角';povFrame.src='taiwan-study.html?phone-pov=1';povFrame.onload=publishView;$('pov-card').prepend(povFrame);}
 const labels=mode==='pov'?['前進','向左移動','後退','向右移動']:['向北走','向西走','向南走','向東走'];document.querySelectorAll('[data-dx]').forEach((b,i)=>b.setAttribute('aria-label',labels[i]));
}
for(const button of document.querySelectorAll('[data-controller-view]'))button.onclick=()=>setView(button.dataset.controllerView);
addEventListener('message',event=>{if(event.origin!==location.origin||event.source!==povFrame?.contentWindow)return;if(event.data?.type==='hope-pov-ready'){$('pov-loading').hidden=true;publishView();publishResidents();}if(event.data?.type==='hope-pov-heading'&&Number.isFinite(event.data.heading)){povHeading=event.data.heading;const world=worldVector();predictor?.input(world.dx,world.dz);send(true);}});
function point(event){const r=$('joystick').getBoundingClientRect();setVector((event.clientX-r.left-r.width/2)/55,(event.clientY-r.top-r.height/2)/55);send(true);}
$('joystick').onpointerdown=event=>{if(!ready)return;pointer=event.pointerId;$('joystick').setPointerCapture(pointer);point(event);};
$('joystick').onpointermove=event=>{if(event.pointerId===pointer)point(event);};
for(const name of ['pointerup','pointercancel','lostpointercapture'])$('joystick').addEventListener(name,stop);
for(const button of document.querySelectorAll('[data-dx]')){button.onpointerdown=event=>{button.setPointerCapture(event.pointerId);setVector(Number(button.dataset.dx),Number(button.dataset.dz));send(true);};for(const name of ['pointerup','pointercancel','lostpointercapture'])button.addEventListener(name,stop);}
const directions={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0]};
window.addEventListener('keydown',event=>{if(directions[event.key]&&ready){event.preventDefault();setVector(...directions[event.key]);send();}});window.addEventListener('keyup',event=>{if(directions[event.key])stop();});window.addEventListener('blur',stop);document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
$('release-control').onclick=async()=>{ready=false;stopped=true;setVector(0,0);try{await api('participant/control/release',{});location.href='event-join.html'+(eventId?'?event='+encodeURIComponent(eventId):'');}catch(error){stopped=false;ready=true;$('message').textContent=error.message;}};
async function init(){
 if(!token){$('join-prompt').hidden=false;$('connection').textContent='尚未加入';if(eventId)$('join-link').href='resident-setup.html?event='+encodeURIComponent(eventId);return;}
 try{const data=await api('participant/control');if(eventId&&data.participant.eventId!==eventId)throw Error('參加紀錄不屬於這場活動。');profileId=data.profileId;sequence=data.position.sequence;showPosition(data.position);$('resident-name').textContent=data.participant.name;$('event-title').textContent=data.participant.title;$('my-marker').setAttribute('fill',data.participant.appearance.shirt);$('challenge-link').href='event-join.html?event='+encodeURIComponent(data.participant.eventId);$('controls').hidden=false;ready=true;$('connection').textContent='操控已連線';
 const navigation=await fetch('/api/events/navigation').then(r=>{if(!r.ok)throw Error('導航資料載入失敗');return r.json();}).catch(()=>null);
 if(navigation){predictor=createMovementPredictor({allowed:gridAllows(navigation),others:()=>residents.filter(r=>r.id!==profileId&&r.position).map(r=>r.position)});predictor.acknowledge(position);}
 residentFeed=connectResidentFeed(profiles=>{residents=profiles;publishResidents();});
 const map=await fetch('controller-map.json').then(r=>r.json());for(const points of map.islands){const path=document.createElementNS('http://www.w3.org/2000/svg','polygon');path.setAttribute('points',points.map(p=>p.join(',')).join(' '));path.setAttribute('fill','#c7d5b4');path.setAttribute('stroke','#8fac95');path.setAttribute('stroke-width','.12');$('map-islands').append(path);}
 }catch(error){$('connection').textContent='尚未連線';$('message').textContent=error.message;$('join-prompt').hidden=false;if(error.status===401&&eventId)$('join-link').href='resident-setup.html?event='+encodeURIComponent(eventId);else if(error.status===409){$('join-link').textContent='重新連線';$('join-link').href=location.href;}}
}
function renderController(){requestAnimationFrame(renderController);if(document.hidden||!ready)return;displayPosition=predictor?.sample()||position;if(displayPosition){$('my-marker').setAttribute('cx',displayPosition.x);$('my-marker').setAttribute('cy',displayPosition.z);publishView();}}
requestAnimationFrame(renderController);setInterval(send,60);init();
window.hopeController={audit:()=>({ready,eventId,profileId,position,displayPosition,prediction:!!predictor,transport:residentFeed?.audit(),vector:{...vector},viewMode,povHeading,pump:pump.audit()})};

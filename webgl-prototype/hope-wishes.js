import * as THREE from 'three';
import {pieces} from './taiwan-layout.js?v=15';
import {createCloudWishStore} from './hope-wish-cloud.js';

export function createWishSky({scene,towerPosition,getPlayer,showNight,pulse,screenPoint,setPresentation=()=>{}}){
 let storage;try{storage=localStorage;}catch{storage={getItem:()=>null,setItem:()=>{throw new Error('Storage unavailable');}};}
 const store=createCloudWishStore(storage,{onChange:()=>sync(),onCompleted:id=>{const w=store.wishes.find(w=>w.id===id);if(w)queue.push({id,from:ensureStar(w).position.clone(),demo:false});}}),group=new THREE.Group();group.name='hope-wish-constellation';scene.add(group);
 const canvas=document.createElement('canvas');canvas.width=128;canvas.height=128;const ctx=canvas.getContext('2d');
 const glow=ctx.createRadialGradient(64,64,2,64,64,62);glow.addColorStop(0,'rgba(255,255,255,1)');glow.addColorStop(.18,'rgba(255,245,208,.85)');glow.addColorStop(.48,'rgba(255,232,167,.24)');glow.addColorStop(1,'rgba(255,232,167,0)');ctx.fillStyle=glow;ctx.fillRect(0,0,128,128);
 ctx.beginPath();for(let i=0;i<10;i++){const a=i*Math.PI/5-Math.PI/2,r=i%2?12:30;const x=64+Math.cos(a)*r,y=64+Math.sin(a)*r;i?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.closePath();ctx.fillStyle='#ffffff';ctx.fill();
 const starTexture=new THREE.CanvasTexture(canvas),litMat=new THREE.SpriteMaterial({map:starTexture,color:'#ffe4a6',transparent:true,depthWrite:false,blending:THREE.AdditiveBlending}),archivedMat=new THREE.SpriteMaterial({map:starTexture,color:'#b6dcff',transparent:true,depthWrite:false,blending:THREE.AdditiveBlending}),stars=new Map(),queue=[];
 const skyStars=[];for(let i=0;i<28;i++){const star=new THREE.Sprite(archivedMat.clone());star.position.set(-31+(i*17%63),12+(i%5)*1.3,-30+(i*11%39));star.scale.setScalar(.75+(i%3)*.18);star.userData.base=star.scale.x;group.add(star);skyStars.push(star);}
 const streakSegments=20,streakPositions=new Float32Array((streakSegments+1)*2*3),streakFade=new Float32Array((streakSegments+1)*2),streakIndices=[];
 for(let i=0;i<streakSegments;i++){const a=i*2;streakIndices.push(a,a+1,a+2,a+1,a+3,a+2);}
 const streakGeometry=new THREE.BufferGeometry();streakGeometry.setAttribute('position',new THREE.BufferAttribute(streakPositions,3));streakGeometry.setAttribute('aFade',new THREE.BufferAttribute(streakFade,1));streakGeometry.setIndex(streakIndices);
 const streakMaterial=new THREE.ShaderMaterial({transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,uniforms:{uColor:{value:new THREE.Color('#ffe4a6')}},vertexShader:'attribute float aFade; varying float vFade; void main(){vFade=aFade; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',fragmentShader:'uniform vec3 uColor; varying float vFade; void main(){gl_FragColor=vec4(uColor,vFade);}',side:THREE.DoubleSide});
 const skyStreak=new THREE.Mesh(streakGeometry,streakMaterial);skyStreak.frustumCulled=false;skyStreak.visible=false;group.add(skyStreak);
 const skyHead=new THREE.Sprite(litMat.clone());skyHead.visible=false;skyHead.scale.setScalar(1.25);group.add(skyHead);
 let skyFlight=null,skyCountdown=3,skyLaunched=0;
 const dustPositions=[];for(let i=0;i<240;i++){const a=i*2.39996,r=18+(i%17)*2;dustPositions.push(Math.cos(a)*r,15+(i%19)*.55,Math.sin(a)*r);}
 const dustGeo=new THREE.BufferGeometry();dustGeo.setAttribute('position',new THREE.Float32BufferAttribute(dustPositions,3));group.add(new THREE.Points(dustGeo,new THREE.PointsMaterial({map:starTexture,color:'#ecf2ff',size:2.2,transparent:true,opacity:.65,sizeAttenuation:false,depthWrite:false,blending:THREE.AdditiveBlending})));
 const meteor=new THREE.Mesh(new THREE.SphereGeometry(.20,10,8),new THREE.MeshBasicMaterial({color:'#fff1bc'}));meteor.visible=false;scene.add(meteor);
 const trailGeo=new THREE.BufferGeometry(),trailPositions=new Float32Array(24*3);trailGeo.setAttribute('position',new THREE.BufferAttribute(trailPositions,3));const trail=new THREE.Line(trailGeo,new THREE.LineBasicMaterial({color:'#ffe6a4',transparent:true,opacity:.9,depthWrite:false}));trail.frustumCulled=false;trail.visible=false;scene.add(trail);
 let active=null,isNight=false,clock=0,launched=0,ignition=null,launching=false,saving=false,litFlights=0,launchStage='idle';
 const risingStar=new THREE.Sprite(litMat.clone());risingStar.visible=false;risingStar.material.depthTest=false;scene.add(risingStar);
 const risePositions=new Float32Array(36*3),riseGeo=new THREE.BufferGeometry();riseGeo.setAttribute('position',new THREE.BufferAttribute(risePositions,3));
 const riseDust=new THREE.Points(riseGeo,new THREE.PointsMaterial({map:starTexture,color:'#ffe6b2',size:.15,transparent:true,opacity:.65,depthWrite:false,blending:THREE.AdditiveBlending}));riseDust.visible=false;riseDust.frustumCulled=false;scene.add(riseDust);
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 function hash(id){let h=2166136261;for(const c of id){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;}
 function ensureStar(w){if(stars.has(w.id))return stars.get(w.id);const h=hash(w.id);const star=new THREE.Sprite((w.status==='lit'?litMat:archivedMat).clone());star.position.set(-30+h%61,22+((h>>>8)%14),-65-((h>>>16)%35));group.add(star);stars.set(w.id,star);return star;}
 function sync(){for(const w of store.wishes){const s=ensureStar(w);s.material.color.copy((w.status==='lit'?litMat:archivedMat).color);s.userData.lit=w.status==='lit';s.scale.setScalar(w.status==='lit'?2.1:1.5);}renderList();}
 const dialog=document.querySelector('#wish-dialog'),list=document.querySelector('#wish-list'),summary=document.querySelector('#wish-summary'),note=document.querySelector('#wish-note');
 function renderList(){list.replaceChildren();const lit=store.wishes.filter(w=>w.status==='lit').length;summary.textContent=`${lit} 顆點亮中・${store.wishes.length-lit} 顆已完成`;note.textContent=store.mode==='cloud'?(store.persistent?'願望已與希望星空同步；其他人看不到你的願望文字。':'雲端暫時離線，請等待恢復後再操作。'):store.mode==='local'?'願望保存在這個瀏覽器；星空不顯示願望文字。':'正在連接希望星空…';
  for(const w of [...store.wishes].filter(w=>w.canEdit!==false).reverse()){const row=document.createElement('article'),text=document.createElement('p');text.textContent=w.text;row.append(text);if(w.status==='lit'){const button=document.createElement('button');button.textContent='願望完成';button.onclick=async()=>{button.disabled=true;try{if(!await store.complete(w.id))return;queue.push({id:w.id,from:ensureStar(w).position.clone(),demo:false});sync();dialog.close();showNight();}catch(e){note.textContent=e.message;}finally{button.disabled=false;}};row.append(button);}else{const done=document.createElement('small');done.textContent=w.status==='completed'?'化作流星中':'已留在希望星空';row.append(done);}list.append(row);}
 }
 document.querySelector('#wish-open').onclick=()=>{renderList();dialog.showModal();document.querySelector('#wish-text').focus();};document.querySelector('#wish-close').onclick=()=>dialog.close();
 const form=document.querySelector('#wish-form'),submit=form.querySelector('[type=submit]');
 function finishIgnition(){
  if(ignition){ignition.star.visible=true;ignition.star.userData.arrival=clock;}
  ignition=null;risingStar.visible=false;riseDust.visible=false;launching=false;launchStage='idle';submit.disabled=false;document.querySelector('#wish-open').disabled=false;document.querySelector('#wish-close').disabled=false;setPresentation(false);pulse(1.3);
  document.querySelector('#status').textContent='你的希望星已飛上天空，願望已保存。';
 }
 dialog.addEventListener('cancel',event=>{if(launching)event.preventDefault();});
 form.onsubmit=async e=>{
  e.preventDefault();if(launching||saving)return;
  const input=document.querySelector('#wish-text');if(!input.value.trim())return;const player=getPlayer();let island=0,best=Infinity;
  pieces.forEach((p,i)=>{const d=Math.hypot(player.x-p.center[0],player.z-p.center[1]);if(d<best){best=d;island=i;}});
  const id='wish-'+Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
  let w;saving=true;submit.disabled=true;try{w=await store.add(input.value,island,id);}catch(error){note.textContent=error.message;note.setAttribute('role','alert');submit.disabled=false;return;}finally{saving=false;}submit.disabled=false;
  if(!w){note.textContent='願望尚未保存成功，請確認瀏覽器儲存空間後再試；文字仍為你保留。';note.setAttribute('role','alert');return;}
  launching=true;launchStage='card';submit.disabled=true;document.querySelector('#wish-open').disabled=true;document.querySelector('#wish-close').disabled=true;setPresentation(true);
  sync();const star=ensureStar(w);star.visible=false;const rect=dialog.getBoundingClientRect();
  try{
   await dialog.animate(reduced.matches?[{opacity:1},{opacity:0}]:[{transform:'scale(1)',opacity:1,filter:'brightness(1)'},{transform:'scale(.22)',opacity:.8,filter:'brightness(1.6)',offset:.8},{transform:'scale(.04)',opacity:0,filter:'brightness(2)'}],{duration:reduced.matches?160:650,easing:'cubic-bezier(.45,0,.25,1)'}).finished;
   dialog.close();input.value='';showNight();setPresentation(true);
   const from=screenPoint(rect.left+rect.width/2,rect.top+rect.height/2,24),to=star.position.clone();
   ignition={star,time:0,curve:new THREE.CubicBezierCurve3(from,from.clone().add(new THREE.Vector3(-3,9,-8)),to.clone().add(new THREE.Vector3(5,-4,14)),to)};
   launchStage='rising';litFlights++;risingStar.position.copy(from);risingStar.scale.setScalar(2.3);risingStar.visible=!reduced.matches;riseDust.visible=!reduced.matches;pulse(.5);
   document.querySelector('#status').textContent='願望正在化成星星，飛向希望星空…';
   if(reduced.matches)finishIgnition();
  }catch{star.visible=true;dialog.close();input.value='';showNight();finishIgnition();}
 };
 document.querySelector('#wish-demo').onclick=()=>{dialog.close();showNight();const p=pieces[1].center;queue.push({id:'demo',from:new THREE.Vector3(p[0],10,p[1]),demo:true});};
 function setNight(value){isNight=value;group.visible=value;if(!value){skyFlight=null;skyCountdown=3;skyStreak.visible=false;skyHead.visible=false;skyStars.forEach(s=>s.visible=true);}}
 function update(dt){
  clock+=dt;
  if(ignition){
   ignition.time+=dt;const u=Math.min(1,ignition.time/2.2),t=1-Math.pow(1-u,2);
   risingStar.position.copy(ignition.curve.getPoint(t));risingStar.scale.setScalar(2.3+.4*Math.sin(u*Math.PI));
   for(let i=0;i<36;i++){const lag=Math.max(0,t-i*.006),p=ignition.curve.getPoint(lag);p.x+=Math.sin(i*2.4)*.12*(1-u);p.y+=Math.cos(i*1.7)*.1;risePositions.set(p.toArray(),i*3);}riseGeo.attributes.position.needsUpdate=true;
   if(u>=1)finishIgnition();
  }
  let index=0;for(const star of stars.values()){
   const phase=(clock-index++*.85)%5.6,twinkle=reduced.matches?0:Math.pow(Math.max(0,Math.sin(phase*Math.PI/2.8)),8);
   const arrival=Math.max(0,1-(clock-(star.userData.arrival??-100))/1.2);star.scale.setScalar((star.userData.lit?2.1:1.5)*(1+twinkle*.35+arrival*.7));star.material.opacity=.68+twinkle*.32;
  }
  skyStars.forEach((star,i)=>{const twinkle=reduced.matches?0:Math.pow(Math.max(0,Math.sin(clock*.8-i*.73)),10);star.scale.setScalar(star.userData.base*(1+twinkle*.65));star.material.opacity=.42+twinkle*.58;});
  if(isNight&&!reduced.matches){
   skyCountdown-=dt;
   if(!skyFlight&&skyCountdown<=0){const source=skyStars[(skyLaunched*7+3)%skyStars.length];source.visible=false;skyFlight={source,from:source.position.clone(),time:0};skyLaunched++;}
   if(skyFlight){
    skyFlight.time+=dt;const t=skyFlight.time/2.8;
    const center=u=>skyFlight.from.clone().add(new THREE.Vector3(34*u,-4*u+2*Math.sin(Math.PI*u),12*u));
    const direction=new THREE.Vector3(34,-4,12).normalize(),side=new THREE.Vector3(-direction.z,0,direction.x).normalize();
    for(let i=0;i<=streakSegments;i++){
     const lag=(streakSegments-i)/streakSegments*.13,u=t-lag,clamped=Math.max(0,Math.min(1,u)),p=center(clamped),along=i/streakSegments;
     const endFade=Math.max(0,Math.min(1,u*10,(1-u)*8)),edge=.13+.87*Math.sin(Math.PI*along);
     const halfWidth=(.025+.09*along)*Math.max(.1,endFade);
     for(let edgeIndex=0;edgeIndex<2;edgeIndex++){
      const vertex=(i*2+edgeIndex),sign=edgeIndex?1:-1;
      streakPositions.set([p.x+side.x*halfWidth*sign,p.y+side.y*halfWidth*sign,p.z+side.z*halfWidth*sign],vertex*3);
      streakFade[vertex]=edge*Math.max(0,endFade)*(u<0?0.01:1)*(edgeIndex===0?.78:1);
     }
    }
    streakGeometry.attributes.position.needsUpdate=true;streakGeometry.attributes.aFade.needsUpdate=true;streakGeometry.computeBoundingSphere();
    skyStreak.visible=true;skyHead.position.copy(center(Math.min(1,t)));skyHead.material.opacity=Math.max(0,Math.min(1,(1-t)*8));skyHead.visible=t<=1.08;
    if(t>1.32){skyFlight.source.visible=true;skyFlight=null;skyCountdown=5+(skyLaunched%3)*2;skyStreak.visible=false;skyHead.visible=false;}
   }
  }else if(skyFlight){skyFlight.source.visible=true;skyFlight=null;skyStreak.visible=false;skyHead.visible=false;}
  if(!active&&queue.length){active={...queue.shift(),time:0};launched++;meteor.visible=!reduced.matches;trail.visible=!reduced.matches;pulse(.6);}
  if(!active)return;active.time+=dt;const t=Math.min(1,active.time/(reduced.matches?.8:3.2)),to=towerPosition;
  const position=u=>new THREE.Vector3().lerpVectors(active.from,to,u).add(new THREE.Vector3(0,Math.sin(u*Math.PI)*3,0));meteor.position.copy(position(t));
  for(let i=0;i<24;i++){const p=position(Math.max(0,t-i*.008));trailPositions.set(p.toArray(),i*3);}trailGeo.attributes.position.needsUpdate=true;pulse(Math.sin(t*Math.PI)*1.4);
  if(t>=1){if(!active.demo){store.archive(active.id).then(()=>sync()).catch(()=>{note.textContent='完成狀態已保存，正在等待星空同步。';});}meteor.visible=false;trail.visible=false;active=null;pulse(1.8);}
 }
 setInterval(()=>{if(!document.hidden)store.refresh();},2500);sync();setNight(false);return {setNight,update,audit:()=>({total:store.wishes.length,lit:store.wishes.filter(w=>w.status==='lit').length,archived:store.wishes.filter(w=>w.status==='archived').length,persistent:store.persistent,ignition:launching,launchStage,litFlights,meteor:!!active,queued:queue.length,launched,night:isNight,twinkling:!reduced.matches,ambientMeteor:!!skyFlight,ambientLaunched:skyLaunched,wishStarSize:2.1})};
}

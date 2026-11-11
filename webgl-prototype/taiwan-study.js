import * as THREE from 'three';
import {pieces,joins,mapPoint,seamAt,onLand,bandV,routeClearance,WORLD_SCALE,SHORE_JOIN_RADIUS,insidePolygon} from './taiwan-layout.js?v=15';
import {characterStyles} from './hope-characters.js?v=16';
import {loadAvatarLibrary,createAvatar} from './hope-avatar.js?v=20';
import {createLandmarkGardens} from './hope-landmark-gardens.js?v=18';
import {buildLandscapes,themes} from './hope-landscapes.js?v=20';
import {createCrowd} from './hope-crowd.js?v=20';
import {createEnvironment} from './hope-environment.js?v=18';
import {createWishSky} from './hope-wishes.js?v=15';
import {educationStations,challengeQuestions} from './hope-education.js?v=17';
import {loadPublishedEducation,readingKey,appendArticle} from './hope-education-live.js?v=20';
educationStations.forEach(s=>s.items=[]);
if(new URLSearchParams(location.search).get('projection')==='1')document.body.dataset.projection='true';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';

const scene=new THREE.Scene();scene.background=new THREE.Color('#c8dfdc');scene.fog=new THREE.Fog('#c8dfdc',110,250);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;document.body.prepend(renderer.domElement);
const camera=new THREE.PerspectiveCamera(38,1,.1,350);camera.position.set(11,10,16);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,1.5,0);controls.enableDamping=true;controls.minDistance=2.5;controls.maxDistance=140;controls.maxPolarAngle=Math.PI*.47;controls.enablePan=true;controls.screenSpacePanning=true;
let cameraPanMode=false,cameraPanPointer=null;const cameraPanButton=document.querySelector('#camera-pan');cameraPanButton.onclick=()=>{cameraPanMode=!cameraPanMode;controls.mouseButtons.LEFT=cameraPanMode?null:THREE.MOUSE.ROTATE;cameraPanButton.setAttribute('aria-pressed',String(cameraPanMode));cameraPanButton.textContent=cameraPanMode?'平移中・點此結束':'平移鏡頭';renderer.domElement.style.cursor=cameraPanMode?'grab':'';};renderer.domElement.addEventListener('pointerdown',e=>{if(!cameraPanMode||e.button!==0)return;cameraPanPointer={id:e.pointerId,x:e.clientX,y:e.clientY};renderer.domElement.setPointerCapture(e.pointerId);renderer.domElement.style.cursor='grabbing';e.preventDefault();});renderer.domElement.addEventListener('pointermove',e=>{if(!cameraPanPointer||cameraPanPointer.id!==e.pointerId)return;const dx=e.clientX-cameraPanPointer.x,dy=e.clientY-cameraPanPointer.y;cameraPanPointer.x=e.clientX;cameraPanPointer.y=e.clientY;const scale=2*controls.target.distanceTo(camera.position)*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))/renderer.domElement.clientHeight,right=new THREE.Vector3().setFromMatrixColumn(camera.matrix,0),up=new THREE.Vector3().setFromMatrixColumn(camera.matrix,1),shift=right.multiplyScalar(-dx*scale).add(up.multiplyScalar(dy*scale));camera.position.add(shift);controls.target.add(shift);e.preventDefault();});function finishCameraPan(e){if(cameraPanPointer&&cameraPanPointer.id===e.pointerId){cameraPanPointer=null;renderer.domElement.style.cursor=cameraPanMode?'grab':'';}}renderer.domElement.addEventListener('pointerup',finishCameraPan);renderer.domElement.addEventListener('pointercancel',finishCameraPan);
const hemi=new THREE.HemisphereLight('#ecf6ff','#a5aa88',1.65);scene.add(hemi);
const sun=new THREE.DirectionalLight('#fff0d5',2.6);sun.position.set(-24,38,27);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-39,right:39,top:42,bottom:-42,near:1,far:150});sun.shadow.normalBias=.025;scene.add(sun);
const fill=new THREE.DirectionalLight('#d8ebff',.85);fill.position.set(7,5,-7);scene.add(fill);
const mats={};const material=(key,color,rough=.8)=>mats[key]??(mats[key]=new THREE.MeshStandardMaterial({color,roughness:rough}));
const grass=material('grass','#98ae78'),rock=material('rock','#9c9d8f'),sand=material('sand','#ddc7a4'),wood=material('wood','#a97d59'),leaf=material('leaf','#7e9a65'),pink=material('blossom','#e5b0bd');
function mesh(geo,mat,parent=scene,x=0,y=0,z=0){const o=new THREE.Mesh(geo,mat);o.position.set(x,y,z);o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;}
function ball(parent,mat,x,y,z,sx,sy=sx,sz=sx){const o=mesh(new THREE.SphereGeometry(1,sx<.12?12:20,sx<.12?8:14),mat,parent,x,y,z);o.scale.set(sx,sy,sz);return o;}
function box(parent,mat,x,y,z,w,h,d,r=.05){return mesh(new RoundedBoxGeometry(w,h,d,2,r),mat,parent,x,y,z);}
function cylinder(parent,mat,x,y,z,top,bottom,h,n=64){return mesh(new THREE.CylinderGeometry(top,bottom,h,n),mat,parent,x,y,z);}
const island=new THREE.Group();island.name='taiwan-ten-islands';scene.add(island);
const baseY=.7,topY=.7;
const [towerX,towerZ]=pieces[4].center;
const spawn=mapPoint(seamAt(bandV(3,.60))/2,bandV(3,.60));
const hospitalPoint=[3.75,-2];
const hospitalRadius=4.2;
const colliders=[{x:towerX,z:towerZ,r:1.44},{x:hospitalPoint[0],z:hospitalPoint[1],r:hospitalRadius,halfX:3.52,halfZ:2.5}],lamps=[];
const islandLabels=[];
const hospitalNightMaterials=[],hospitalLights=[];let illuminatedHospitalWindows=0;
const islandColors=['#a5b68c','#c2bd98','#9fb9a1','#c7b0b3','#a7b880','#aab8c2','#c3bd8b','#a9bcb0','#bab393','#bdc79b'];
function terrain(points,mat,bottom,height,bevel=.035){
 const shape=new THREE.Shape();points.forEach(([x,z],i)=>i?shape.lineTo(x,-z):shape.moveTo(x,-z));shape.closePath();
 const geo=new THREE.ExtrudeGeometry(shape,{depth:height,bevelEnabled:true,bevelSize:bevel,bevelThickness:.025,bevelSegments:1,steps:1,curveSegments:1});geo.rotateX(-Math.PI/2);
 return mesh(geo,mat,island,0,bottom,0);
}
for(const p of pieces){
 terrain(p.points,rock,-.55,.75,.03);terrain(p.points,sand,.20,.36,.045);
 terrain(p.points,material('island-'+p.id,islandColors[p.id-1]),.56,.12,.025);
 // A subdued numbered marker identifies the ten land pieces without naming medical stages.
 const canvas=document.createElement('canvas');canvas.width=128;canvas.height=128;const ctx=canvas.getContext('2d');
 ctx.fillStyle='#fff9e8';ctx.beginPath();ctx.arc(64,64,43,0,Math.PI*2);ctx.fill();ctx.fillStyle='#65756b';ctx.font='500 42px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(String(p.id).padStart(2,'0'),64,65);
 const label=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(canvas),transparent:true,depthTest:true}));label.position.set(p.center[0],.95,p.center[1]+.65);label.scale.set(1,1,1);scene.add(label);islandLabels.push(label);
}
for(const j of joins){const [x,z]=j.point;cylinder(island,sand,x,.40,z,j.r,j.r+.04,.52,32);cylinder(island,grass,x,.606,z,j.r,j.r,.14,32);}
// Navigation corridors remain reserved, but no path meshes cover the natural terrain.

// Trees sit inside the curved coast; their trunks share the same collision map as walking.
for(const p of pieces)for(let k=0;k<6;k++){
 const v=bandV(p.row,.13+k*.14),u=p.col?seamAt(v)+(1-seamAt(v))*.76:seamAt(v)*.20;
 const [x,z]=mapPoint(u,v);if(!onLand(x,z)||routeClearance(x,z)<.72||colliders.some(c=>Math.hypot(x-c.x,z-c.z)<c.r+.7))continue;
 const tree=new THREE.Group();tree.position.set(x,.7,z);tree.scale.setScalar(.48+(p.id%3)*.06);island.add(tree);
 cylinder(tree,wood,0,.6,0,.10,.15,1.2,10);
 for(const [a,b,c,r] of [[0,1.55,0,.62],[-.42,1.34,.04,.48],[.4,1.45,.06,.48],[.03,1.9,-.05,.41]])ball(tree,p.id%3===0?pink:leaf,a,b,c,r,r*.88,r);
 colliders.push({x,z,r:.17});
}
for(const p of pieces){const [x,z]=p.center;if(p.id===5)continue;const m=new THREE.MeshStandardMaterial({color:'#fff0ba',emissive:'#ffc76e',emissiveIntensity:1});cylinder(island,wood,x,1.0,z,.025,.035,.6,8);box(island,m,x,1.36,z,.13,.18,.13,.02);lamps.push(m);}
const sea=mesh(new THREE.PlaneGeometry(300,300,120,120),material('sea','#60a8b3',.42),scene,0,-.59,0);sea.rotation.x=-Math.PI/2;sea.castShadow=false;

const characterTools={material,ball,box,mesh,cylinder};
const landscape=buildLandscapes({island,material,mesh,box,ball,cylinder,colliders,createCharacter:()=>null,towerX,towerZ});
const environment=createEnvironment({scene,island,sea,mesh,ball,box,cylinder,material,colliders});
await loadAvatarLibrary().catch(error=>{document.querySelector('#loading').textContent='角色模型載入失敗，請重新整理。';throw error;});
let activeCharacter=0,avatar=createAvatar(0),person=avatar.person;
scene.add(person);person.position.set(spawn[0],.7,spawn[1]);
function changeCharacter(index,moveCamera=true){
 const position=person.position.clone(),heading=person.rotation.y;avatar.dispose();
 activeCharacter=index;avatar=createAvatar(index);person=avatar.person;person.position.copy(position);person.rotation.y=heading;scene.add(person);avatar.update(0);
 if(moveCamera)setView('person');
}
const gardens=createLandmarkGardens({scene,island,material,mesh,ball,box,cylinder,colliders,hospitalPoint,towerX,towerZ});
// Physical footprint uses the same shapes as visible geometry.
function heightAt(x,z){return onLand(x,z)?.7:null;}
function allowed(x,z,y){const h=heightAt(x,z);return h!==null&&Math.abs(h-y)<.14&&!colliders.some(c=>c.halfX?Math.abs(x-c.x)<c.halfX+.24&&Math.abs(z-c.z)<c.halfZ+.24:Math.hypot(x-c.x,z-c.z)<c.r+.24);}
function move(dx,dz,dt){const n=Math.hypot(dx,dz);if(n<.01)return false;dx/=n;dz/=n;const parts=Math.max(1,Math.ceil(dt*1.6/.04));let moved=false;
 for(let i=0;i<parts;i++){const nx=person.position.x+dx*1.6*dt/parts,nz=person.position.z+dz*1.6*dt/parts;
 if(allowed(nx,person.position.z,person.position.y)){person.position.x=nx;person.position.y=heightAt(nx,person.position.z);moved=true;}
 if(allowed(person.position.x,nz,person.position.y)){person.position.z=nz;person.position.y=heightAt(person.position.x,nz);moved=true;}}
 if(moved){const angle=Math.atan2(dx,dz),delta=Math.atan2(Math.sin(angle-person.rotation.y),Math.cos(angle-person.rotation.y));person.rotation.y+=delta*Math.min(1,dt*12);}return moved;
}
let tower,hospital,hospitalHeight=0,wishSky,night=false,view='campus',followedResident=null,lanternPulse=0;const lantern=new THREE.PointLight('#ffc577',0,7,2);lantern.position.set(towerX,6.2,towerZ);scene.add(lantern);

try{
 const loader=new GLTFLoader();loader.setMeshoptDecoder(MeshoptDecoder);const [gltf,campus]=await Promise.all([loader.loadAsync('assets/poster-lighthouse-tower-v01.glb'),loader.loadAsync('assets/ntucc-blender-v07.glb')]);
 tower=gltf.scene;tower.name='hope-lighthouse';tower.scale.setScalar(1.1);tower.position.set(towerX,topY,towerZ);scene.add(tower);
 const bounds=new THREE.Box3().setFromObject(campus.scene),size=bounds.getSize(new THREE.Vector3()),center=bounds.getCenter(new THREE.Vector3()),scale=7.0/Math.max(size.x,size.z);
 hospital=new THREE.Group();hospital.name='ntu-cancer-center';campus.scene.position.set(-center.x,-bounds.min.y,-center.z);hospital.add(campus.scene);hospital.scale.setScalar(scale);hospital.position.set(hospitalPoint[0],.7,hospitalPoint[1]);hospitalHeight=size.y*scale;scene.add(hospital);
 // Reuse a few night materials so window lighting survives static mesh batching.
 const nightVariants=new Map();
 campus.scene.traverse(o=>{
  if(!o.isMesh||Array.isArray(o.material))return;
  const name=o.name,mat=o.material;
  let color=null,strength=0;
  if(name.includes('wing-glass')||name.includes('core-window')){
   const hash=[...name].reduce((n,c)=>(n*31+c.charCodeAt(0))>>>0,0);
   if(hash%5<3){color='#ffd797';strength=1.4;illuminatedHospitalWindows++;}
  }else if(mat.name.includes('canopy-glass')){color='#ffe0a8';strength=.7;}
  else if(mat.name.endsWith('-sign')||mat.name.endsWith('-identity-mark')){color='#fff0d0';strength=1.8;}
  else if(name.includes('main-curved-tower')){color='#83a7b5';strength=.16;}
  if(!color)return;
  const key=mat.uuid+color+strength;
  if(!nightVariants.has(key)){const copy=mat.clone();copy.emissive.set(color);copy.emissiveIntensity=0;nightVariants.set(key,copy);hospitalNightMaterials.push({material:copy,strength});}
  o.material=nightVariants.get(key);
 });
 for(const [dx,dz,power] of [[-2.1,2.3,7],[1,2.1,6]]){const light=new THREE.PointLight('#ffd6a0',0,5,2);light.position.set(hospitalPoint[0]+dx,1.5,hospitalPoint[1]+dz);light.userData.nightIntensity=power;scene.add(light);hospitalLights.push(light);}
 for(const root of [tower,hospital])root.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
 // The plaza is at ground level; it is not a bridge or a separate scene.
 // The detailed hospital asset includes its own paved arrival plaza.
 document.querySelector('#loading').hidden=true;
}catch(e){document.querySelector('#loading').textContent='模型載入失敗，請重新整理。';throw e;}
// Keep authoring parts separate above; batch static meshes by material for WebGL.
scene.updateMatrixWorld(true);
const batches=new Map(),originals=[];
for(const root of [island,tower,hospital])root.traverse(o=>{
 if(!o.isMesh||o.isInstancedMesh||Array.isArray(o.material))return;
 let g=o.geometry.clone();if(g.index)g=g.toNonIndexed();g.applyMatrix4(o.matrixWorld);
 for(const key of Object.keys(g.attributes))if(!['position','normal','uv'].includes(key))g.deleteAttribute(key);
 if(!g.attributes.normal)g.computeVertexNormals();if(!g.attributes.uv)g.setAttribute('uv',new THREE.BufferAttribute(new Float32Array(g.attributes.position.count*2),2));
 const key=o.material.uuid+':'+o.castShadow+':'+o.receiveShadow,group=batches.get(key)||{material:o.material,cast:o.castShadow,receive:o.receiveShadow,geometries:[]};group.geometries.push(g);batches.set(key,group);originals.push(o);
});
for(const {material:mat,cast,receive,geometries} of batches.values()){const merged=mergeGeometries(geometries);if(!merged)throw new Error('Static mesh merge failed');const batch=mesh(merged,mat);batch.castShadow=cast;batch.receiveShadow=receive;geometries.forEach(g=>g.dispose());}
originals.forEach(o=>o.removeFromParent());
const keys=new Set();window.addEventListener('keydown',e=>{if(e.target.closest?.('input,textarea,select,[contenteditable]')||document.querySelector('#wish-dialog').open||educationDialog.open)return;if(e.key.toLowerCase()==='e'&&stationIndexNearPlayer()>=0){e.preventDefault();openEducation(stationIndexNearPlayer());return;}if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','w','a','s','d'].includes(e.key)){e.preventDefault();keys.add(e.key);}});window.addEventListener('keyup',e=>keys.delete(e.key));window.addEventListener('blur',()=>keys.clear());
for(const b of document.querySelectorAll('[data-key]')){b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(b.dataset.key);});for(const ev of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(ev,()=>keys.delete(b.dataset.key));}
function characterCameraOffset(){
 const target=person.position.clone().add(new THREE.Vector3(0,.8,0)),ray=new THREE.Raycaster(),obstacles=scene.children.filter(o=>o.isMesh&&!o.isInstancedMesh&&o!==sea);
 for(const height of [1.2,2.0,2.8])for(const angle of [.15,-.6,.65,-1.2,1.2,Math.PI]){
  const offset=new THREE.Vector3(Math.sin(angle)*3.4,height,Math.cos(angle)*3.4),end=target.clone().add(offset);
  const clear=[.3,1.2].every(y=>{const from=person.position.clone().add(new THREE.Vector3(0,y,0)),direction=end.clone().sub(from),distance=direction.length();ray.set(from,direction.normalize());ray.far=distance;return !ray.intersectObjects(obstacles,false).some(hit=>hit.distance<distance-.15);});
  if(clear){person.rotation.y=angle;return offset;}
 }return new THREE.Vector3(0,3.2,3.4);
}
function overviewOffset(){
 const direction=new THREE.Vector3(camera.aspect>1.25?.90:.20,.92,.52).normalize(),right=new THREE.Vector3(direction.z,0,-direction.x).normalize(),up=new THREE.Vector3().crossVectors(direction,right),pts=pieces.flatMap(p=>p.points.flatMap(([x,z])=>[new THREE.Vector3(x,0,z),new THREE.Vector3(x,6.8,z)]));
 const span=axis=>{const values=pts.map(p=>p.dot(axis));return Math.max(...values)-Math.min(...values);};
 const halfFov=Math.tan(THREE.MathUtils.degToRad(camera.fov/2)),distance=(Math.max(span(up)/(2*halfFov),span(right)/(2*halfFov*camera.aspect))+span(direction)*.20)*1.15;
 return direction.multiplyScalar(distance);
}
function setView(name){followedResident=null;document.querySelector('#stop-follow').hidden=true;view=name;islandLabels.forEach(label=>label.visible=name==='island');document.querySelector('#zone').value='';document.querySelector('#status').textContent=name==='person'?characterStyles[activeCharacter].name:'十座照護小島，沿著相接的岸邊自由探索。';const target=name==='person'?person.position.clone().add(new THREE.Vector3(0,.8,0)):name==='campus'?new THREE.Vector3(.2,1.6,-2):name==='tower'?new THREE.Vector3(towerX,4.0,towerZ):name==='hospital'?new THREE.Vector3(hospitalPoint[0],hospitalHeight*.45+.7,hospitalPoint[1]):new THREE.Vector3(-.4,1,0);const offset=name==='campus'?new THREE.Vector3(19,19,27):name==='person'?characterCameraOffset():name==='tower'?new THREE.Vector3(5,4,11):name==='hospital'?new THREE.Vector3(10,8,13):overviewOffset();controls.target.copy(target);camera.position.copy(target).add(offset);controls.update();document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));
const zoneSelect=document.querySelector('#zone'),characterSelect=document.querySelector('#character');
for(const [i,theme] of themes.entries()){const option=document.createElement('option');option.value=i;option.textContent=String(i+1).padStart(2,'0')+' '+theme.name;zoneSelect.append(option);}
for(const [i,spec] of characterStyles.entries()){const option=document.createElement('option');option.value=i;option.textContent=spec.name;characterSelect.append(option);}
const educationDialog=document.querySelector('#education-dialog'),educationStationSelect=document.querySelector('#education-station'),educationList=document.querySelector('#education-list'),educationDetail=document.querySelector('#education-detail'),educationProgress=document.querySelector('#education-progress'),educationDone=(()=>{try{return new Set(JSON.parse(localStorage.getItem('hopeIslandEducationDoneV1')||'[]'));}catch{return new Set();}})();
educationStations.forEach((station,i)=>{const o=document.createElement('option');o.value=i;o.textContent=String(i+1).padStart(2,'0')+' '+station.name;educationStationSelect.append(o);});
function stationIndexNearPlayer(){let best=-1,distance=Infinity;landscape.anchors.forEach((a,i)=>{const d=Math.hypot(person.position.x-a.point[0],person.position.z-a.point[1]);if(d<distance){best=i;distance=d;}});return distance<4.4?best:-1;}
let challengeIndex=0;const challengeKey='hopeIslandThreeQuestionChallengeV1',challengeComplete=localStorage.getItem(challengeKey)==='true';
function updateStationProgress(){const station=educationStations[Number(educationStationSelect.value)],read=station.items.filter(item=>educationDone.has(readingKey(station,item))).length;educationProgress.textContent=`已閱讀 ${read}／${station.items.length} 篇文章・自由瀏覽，不計活動闖關進度`;}
function renderEducationList(){const index=Number(educationStationSelect.value),station=educationStations[index];educationDetail.hidden=true;educationList.hidden=false;educationList.replaceChildren();updateStationProgress();if(!station.items.length){const empty=document.createElement('p');empty.textContent='本科目前尚無已發布文章，請稍後再來，或選擇其他科別。';educationList.append(empty);}station.items.forEach((item,i)=>{const button=document.createElement('button'),title=document.createElement('span'),meta=document.createElement('small');button.type='button';title.textContent=item.title;meta.textContent=educationDone.has(readingKey(station,item))?'已閱讀・可再次查看':'閱讀衛教文章';button.append(title,meta);button.onclick=()=>openEducationLesson(index,i);educationList.append(button);});}
function openEducationLesson(index,itemIndex){educationStationSelect.value=String(index);renderEducationList();const station=educationStations[index],item=station.items[itemIndex];educationList.hidden=true;educationDetail.hidden=false;educationDetail.replaceChildren();appendArticle(educationDetail,item);const read=document.createElement('button');read.type='button';read.textContent=educationDone.has(readingKey(station,item))?'已讀，返回清單':'標記已讀並返回清單';read.onclick=()=>{educationDone.add(readingKey(station,item));try{localStorage.setItem('hopeIslandEducationDoneV1',JSON.stringify([...educationDone]));}catch{}renderEducationList();};educationDetail.append(read);}
function renderChallenge(index=challengeIndex){challengeIndex=index;educationList.hidden=true;educationDetail.hidden=false;educationDetail.replaceChildren();const title=document.createElement('h3'),copy=document.createElement('p');if(index>=challengeQuestions.length){try{localStorage.setItem(challengeKey,'true');}catch{}title.textContent='三題全數答對，闖關完成';copy.className='education-copy';copy.textContent='你已完成三題理解闖關。這些題目用來幫助整理討論方向，不代表個人篩檢或治療建議。';const back=document.createElement('button');back.type='button';back.textContent='返回自由瀏覽';back.onclick=renderEducationList;educationDetail.append(title,copy,back);document.querySelector('#challenge-progress').textContent='三題理解闖關：已通關';return;}const question=challengeQuestions[index];title.textContent=`三題理解闖關・第 ${index+1}／${challengeQuestions.length} 題`;copy.className='education-copy';copy.textContent=question.prompt;const options=document.createElement('div');options.className='quiz-options';const feedback=document.createElement('p');feedback.className='quiz-feedback';feedback.setAttribute('role','status');question.choices.forEach((choice,i)=>{const button=document.createElement('button');button.type='button';button.textContent=choice;button.onclick=()=>{if(i!==question.answer){feedback.textContent='這題還不正確，請再選一次；三題都答對才會通關。';return;}feedback.textContent=question.explanation;for(const source of question.sources||[]){const link=document.createElement('a');link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent=source.label;link.style.display='block';link.style.marginTop='8px';feedback.append(document.createElement('br'),link);}options.querySelectorAll('button').forEach(option=>option.disabled=true);const next=document.createElement('button');next.type='button';next.textContent=index+1===challengeQuestions.length?'完成闖關':'前往下一題';next.onclick=()=>renderChallenge(index+1);educationDetail.append(next);};options.append(button);});document.querySelector('#challenge-progress').textContent=challengeComplete?'三題理解闖關：已通關，可重新作答':`三題理解闖關：第 ${index+1}／${challengeQuestions.length} 題・三題都答對才通關`;educationDetail.append(title,copy,options,feedback);}
async function openEducation(index=stationIndexNearPlayer()){if(index<0)index=Number(zoneSelect.value||0);educationStationSelect.value=String(index);educationDetail.hidden=true;educationList.hidden=false;educationList.textContent='正在載入已發布文章…';if(!educationDialog.open)educationDialog.showModal();keys.clear();try{await loadPublishedEducation(educationStations);if(educationDialog.open)renderEducationList();}catch(error){educationList.textContent=error.message;}}

educationStationSelect.onchange=renderEducationList;document.querySelector('#quiz-start').textContent=challengeComplete?'重玩三題闖關':'開始三題闖關';document.querySelector('#quiz-start').onclick=()=>renderChallenge(0);document.querySelector('#education-open').onclick=()=>openEducation(0);document.querySelector('#station-open').onclick=()=>openEducation(Number(zoneSelect.value||Math.max(0,stationIndexNearPlayer())));document.querySelector('#station-enter').onclick=()=>openEducation(stationIndexNearPlayer());document.querySelector('#education-close').onclick=()=>educationDialog.close();
function updateEducationButton(){const index=stationIndexNearPlayer(),button=document.querySelector('#station-enter');button.hidden=index<0;if(index>=0){button.textContent='閱讀本站';button.title='自由瀏覽'+themes[index].name+'衛教內容';document.querySelector('#station-enter').onclick=()=>openEducation(index);document.querySelector('#station-open').textContent=themes[index].name+'清單';}else document.querySelector('#station-open').textContent=zoneSelect.value===''?'全部衛教':'本站衛教';}
zoneSelect.onchange=()=>{followedResident=null;document.querySelector('#stop-follow').hidden=true;if(zoneSelect.value===''){setView('island');updateEducationButton();return;}const index=Number(zoneSelect.value),anchor=landscape.anchors[index];view='zone';islandLabels.forEach(label=>label.visible=false);controls.target.set(anchor.point[0],.7+anchor.scale*1.2,anchor.point[1]);camera.position.copy(controls.target).add(new THREE.Vector3(3.5,4.4,6).multiplyScalar(Math.max(1,anchor.scale/1.1)));controls.update();document.querySelector('#status').textContent=themes[index].name+'｜點擊建築或開啟衛教清單';document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed','false'));updateEducationButton();};
characterSelect.onchange=()=>changeCharacter(Number(characterSelect.value));
educationDialog.addEventListener('close',updateEducationButton);
let stationPointer=null;renderer.domElement.addEventListener('pointerdown',e=>{if(cameraPanMode){stationPointer=null;return;}stationPointer=[e.clientX,e.clientY];});renderer.domElement.addEventListener('pointerup',e=>{if(cameraPanMode||e.button!==0||!stationPointer||Math.hypot(e.clientX-stationPointer[0],e.clientY-stationPointer[1])>7){stationPointer=null;return;}stationPointer=null;const r=renderer.domElement.getBoundingClientRect(),ndc=new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),ray=new THREE.Raycaster();ray.setFromCamera(ndc,camera);const hit=ray.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0,1,0),-.7),new THREE.Vector3());const resident=crowd.samples().map(a=>{const p=new THREE.Vector3(a.x,1.15,a.z).project(camera),sx=r.left+(p.x+1)*r.width/2,sy=r.top+(-p.y+1)*r.height/2;return {...a,screenDistance:Math.hypot(e.clientX-sx,e.clientY-sy),depth:p.z};}).filter(a=>a.depth>=-1&&a.depth<=1).sort((a,b)=>a.screenDistance-b.screenDistance).find(a=>a.screenDistance<42);if(resident){followResident(resident);return;}if(!hit)return;let best=-1,distance=Infinity;landscape.anchors.forEach((a,i)=>{const d=Math.hypot(hit.x-a.point[0],hit.z-a.point[1]);if(d<distance){best=i;distance=d;}});if(best>=0&&distance<Math.max(2.4,landscape.anchors[best].scale*2.1)){zoneSelect.value=String(best);zoneSelect.dispatchEvent(new Event('change'));openEducation(best);return;}if(followedResident!==null)setView('island');});
document.querySelector('#stop-follow').onclick=()=>{residentFollowSelect.value='';setView('island');};

document.querySelector('#reset').onclick=()=>{keys.clear();person.position.set(spawn[0],.7,spawn[1]);person.rotation.y=0;setView('island');};
function setNight(value){night=value;document.body.dataset.night=String(night);scene.background.set(night?'#243f52':'#c8dfdc');scene.fog.color.copy(scene.background);hemi.intensity=night?.58:1.65;sun.intensity=night?.20:2.6;fill.intensity=night?.4:.85;lantern.intensity=night?8:0;lamps.forEach(m=>m.emissiveIntensity=night?3:1);hospitalNightMaterials.forEach(({material,strength})=>material.emissiveIntensity=night?strength:0);hospitalLights.forEach(light=>light.intensity=night?light.userData.nightIntensity:0);document.querySelector('#night').setAttribute('aria-pressed',String(night));document.querySelector('#night').textContent=night?'回到日光':'點亮夜色';environment.setNight(night);gardens.setNight(night);wishSky?.setNight(night);}
document.querySelector('#night').onclick=()=>setNight(!night);
document.querySelector('#avatar-wave').onclick=()=>{setView('person');avatar.wave();crowd.greet();};
const residentEvents=[];
function logResidentEvent(event){const station=themes[event.station];if(!station||!Number.isInteger(event.resident))return;const verb=event.type==='conversation'?'與身旁島民交流':event.type==='arrived'?'抵達並開始衛教':'結束閱讀，繼續散步',totalMinutes=(8*60+event.simMinute)%1440,hour=Math.floor(totalMinutes/60),minute=totalMinutes%60,row=document.createElement('p');row.textContent=`${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')}・居民 ${String(event.resident+1).padStart(2,'0')} ${verb}：${station.name}`;residentEvents.unshift(row.textContent);if(residentEvents.length>8)residentEvents.length=8;const panel=document.querySelector('#resident-log');panel.replaceChildren(...residentEvents.map(text=>{const p=document.createElement('p');p.textContent=text;return p;}));}
const crowd=createCrowd({scene,allowed,spawn,stations:landscape.anchors,onStationEvent:logResidentEvent,makeCharacter:(index,appearance={})=>createAvatar(index,appearance, {castShadow:false}),getPlayer:()=>person.position});
const residentFollowSelect=document.querySelector('#resident-follow');function updateResidentFollowOptions(){const count=Number(document.querySelector('#population').value);residentFollowSelect.replaceChildren(new Option('選擇島民',''));for(let i=0;i<count;i++)residentFollowSelect.add(new Option('島民 '+String(i+1).padStart(2,'0'),String(i)));if(followedResident!==null&&followedResident>=count){followedResident=null;document.querySelector('#stop-follow').hidden=true;view='island';}}function followResident(resident){if(!resident)return;followedResident=resident.id;residentFollowSelect.value=String(resident.id);view='resident';islandLabels.forEach(label=>label.visible=false);document.querySelector('#stop-follow').hidden=false;document.querySelector('#status').textContent='正在跟隨 '+(resident.name||'島民 '+String(resident.id+1).padStart(2,'0'));const target=new THREE.Vector3(resident.x,1.35,resident.z),obstacles=scene.children.filter(o=>o.isMesh&&!o.isInstancedMesh&&o!==sea),ray=new THREE.Raycaster(),candidates=[[5,4.5,7],[-5,4.5,7],[5,4.5,-7],[-5,4.5,-7],[0,5.5,9],[9,5.5,0],[-9,5.5,0]];let offset=new THREE.Vector3(0,6,10);for(const values of candidates){const candidate=new THREE.Vector3(...values),distance=candidate.length();ray.set(target,candidate.clone().normalize());ray.far=distance-.35;if(!ray.intersectObjects(obstacles,false).length){offset=candidate;break;}}controls.target.copy(target);camera.position.copy(target).add(offset);controls.update();}residentFollowSelect.onchange=()=>{const resident=crowd.samples().find(a=>a.id===Number(residentFollowSelect.value));if(resident)followResident(resident);else if(followedResident!==null)setView('island');};updateResidentFollowOptions();document.querySelector('#population').onchange=e=>{crowd.setCount(e.target.value);updateResidentFollowOptions();};
let guestProfiles=[];
async function syncEventResidents(){try{const response=await fetch('/api/events/residents',{cache:'no-store'});if(!response.ok)return;guestProfiles=(await response.json()).profiles;const wanted=Math.max(Number(document.querySelector('#population').value),guestProfiles.length);crowd.setCount(wanted);crowd.setGuests(guestProfiles);}catch{}}
syncEventResidents();setInterval(syncEventResidents,8000);
wishSky=createWishSky({scene,towerPosition:new THREE.Vector3(towerX,6.2,towerZ),getPlayer:()=>person.position,showNight:()=>{setNight(true);setView('island');},pulse:strength=>{lanternPulse=Math.max(lanternPulse,strength);}});
document.querySelector('#wish-open').addEventListener('click',()=>keys.clear());
function resize(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);if(view==='island'&&tower)setView('island');}addEventListener('resize',resize);resize();setView('campus');
let last=performance.now(),phase=0,frames=0,frameTime=0,fps=0,worldTime=0;
function animate(now){requestAnimationFrame(animate);const elapsed=(now-last)/1000,dt=Math.max(0,Math.min(elapsed,.05));last=now;frameTime+=elapsed;frames++;if(frameTime>=1){fps=frames/frameTime;frames=0;frameTime=0;const a=crowd.audit();document.querySelector('#crowd-status').textContent=`${a.count} 位島民・${a.moving} 位移動中`;}
 let x=Number(keys.has('d')||keys.has('ArrowRight'))-Number(keys.has('a')||keys.has('ArrowLeft')),z=Number(keys.has('s')||keys.has('ArrowDown'))-Number(keys.has('w')||keys.has('ArrowUp'));
 const forward=new THREE.Vector3();camera.getWorldDirection(forward);forward.y=0;forward.normalize();const right=new THREE.Vector3(-forward.z,0,forward.x);const previousPosition=person.position.clone();move(right.x*x-forward.x*z,right.z*x-forward.z*z,dt);
 avatar.update(dt,person.position.distanceTo(previousPosition)/Math.max(dt,.001));
 if(view==='person'){const next=person.position.clone().add(new THREE.Vector3(0,.8,0)),delta=next.clone().sub(controls.target);controls.target.copy(next);camera.position.add(delta);}
 if(view==='resident'&&followedResident!==null){const resident=crowd.samples().find(a=>a.id===followedResident);if(resident){const next=new THREE.Vector3(resident.x,1.45,resident.z),delta=next.clone().sub(controls.target);controls.target.copy(next);camera.position.add(delta);}}
 worldTime+=dt;crowd.update(dt,worldTime);updateEducationButton();environment.update(dt,worldTime);gardens.update(dt,worldTime,lanternPulse);wishSky.update(dt);lanternPulse=Math.max(0,lanternPulse-dt*.8);lantern.intensity=(night?8:0)+lanternPulse*5;
 controls.update();renderer.render(scene,camera);
}
requestAnimationFrame(animate);
window.hopeStudy={audit:()=>({ready:!!tower&&!!hospital,singleScene:true,worldScale:WORLD_SCALE,areaMultiplier:WORLD_SCALE**2,hospital:{present:!!hospital,position:hospitalPoint,height:hospitalHeight,nightLighting:night,illuminatedWindows:night?illuminatedHospitalWindows:0},crowd:crowd.audit(),education:{stations:educationStations.length,units:educationStations.reduce((n,s)=>n+s.items.length,0),completedReadings:[...educationDone].filter(id=>id.includes(':read:')).length,completedChallenges:[...educationDone].filter(id=>id.endsWith(':quiz')).length,visibleResidentEvents:residentEvents.length},environment:{...environment.audit(),carnationBeds:environment.audit().carnationBeds+gardens.audit().carnationBeds,gardens:gardens.audit()},avatar:avatar.audit(),wishes:wishSky.audit(),islands:pieces.length,bridges:0,shoreJoins:joins.length,person:person.position.toArray(),heading:person.rotation.y,view,night,fps:Math.round(fps),drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,colliders:colliders.length,landmarks:landscape.anchors,npcModels:landscape.npcModels,character:characterStyles[activeCharacter].id,walkable:allowed(person.position.x,person.position.z,person.position.y)}),move,heightAt,allowed,pieces,joins,onLand,changeCharacter,crowd,wishSky,setNight,getAvatar:()=>avatar,setView,makeCharacter:index=>createAvatar(index).person};

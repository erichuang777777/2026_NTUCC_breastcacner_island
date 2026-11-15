import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const $=id=>document.getElementById(id),canvas=$('portrait');
let ready=false,model,config,clay=false,angle=0,half=1,target=new THREE.Vector3();
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
const scene=new THREE.Scene();scene.background=new THREE.Color('#e0e7df');
scene.add(new THREE.HemisphereLight('#fffaf2','#9da9a4',2.8));
for(const [x,y,z,power] of [[-3,4,5,1.1],[3,2,3,1.1]]){const l=new THREE.DirectionalLight('#fff6eb',power);l.position.set(x,y,z);scene.add(l);}
const camera=new THREE.OrthographicCamera(-1,1,1,-1,.001,1000);
const controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.minZoom=.25;controls.maxZoom=5;
const clayMaterial=new THREE.MeshStandardMaterial({color:'#c9b6a0',roughness:.9});
function resize(){const r=canvas.getBoundingClientRect(),aspect=r.width/Math.max(1,r.height);renderer.setSize(r.width,r.height,false);camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half;camera.updateProjectionMatrix();}
function reset(){camera.zoom=1;controls.target.copy(target);const distance=Math.max(half*5,.1);camera.position.copy(target).add(new THREE.Vector3(Math.sin(angle)*distance,0,Math.cos(angle)*distance));controls.update();resize();}
function setAngle(value){angle=value;reset();document.querySelectorAll('[data-angle]').forEach(b=>b.setAttribute('aria-pressed',String(Math.abs(Number(b.dataset.angle)-value)<1e-6)));}
function setClay(value){clay=value;model?.traverse(o=>{if(!o.isMesh)return;o.material=clay?clayMaterial:o.userData.originalMaterial;o.visible=clay&&!config.hideInClay.includes(o.name)?o.userData.originalVisible:clay?false:o.userData.originalVisible;});$('clay').setAttribute('aria-pressed',String(value));$('clay').textContent=value?'顯示材質':'檢查素模';}
document.querySelectorAll('[data-angle]').forEach(b=>b.onclick=()=>{if(ready)setAngle(Number(b.dataset.angle));});
$('clay').onclick=()=>{if(ready)setClay(!clay);};$('reset').onclick=()=>{if(ready)setAngle(config.initialAngle);};
$('capture').onclick=()=>{renderer.render(scene,camera);canvas.toBlob(blob=>{if(!blob)return;const a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download=`portrait-${angle.toFixed(2)}-${clay?'clay':'material'}.png`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});};
canvas.addEventListener('keydown',e=>{if(!ready)return;if(['ArrowLeft','ArrowRight','Home'].includes(e.key)){e.preventDefault();setAngle(e.key==='Home'?config.initialAngle:angle+(e.key==='ArrowLeft'?-.15:.15));}});
new ResizeObserver(resize).observe(canvas.parentElement);
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
window.portraitStudy={audit:()=>({ready,clay,angle,assetSHA256:config?.assetSHA256,drawTriangles:renderer.info.render.triangles}),setAngle,setClay};
try{
 const response=await fetch('./viewer.json',{cache:'no-store'});if(!response.ok)throw new Error('viewer.json 載入失敗');config=await response.json();
 $('title').textContent=config.label;$('note').textContent=config.note;
 $('reference').src=config.reference;const ph=config.photo;$('reference').style.transform=`translate(${ph.xPercent}%,${ph.yPercent}%) scale(${ph.scale})`;
 const loaded=await new GLTFLoader().loadAsync(config.model);model=loaded.scene;model.rotation.set(...config.rotation);
 model.traverse(o=>{if(o.isMesh){o.userData.originalMaterial=o.material;o.userData.originalVisible=o.visible;}});scene.add(model);
 const box=new THREE.Box3().setFromObject(model),size=box.getSize(new THREE.Vector3());target.copy(config.camera.target?new THREE.Vector3(...config.camera.target):box.getCenter(new THREE.Vector3()));
 const aspect=canvas.clientWidth/Math.max(1,canvas.clientHeight);half=config.camera.halfHeight??Math.max(size.y,size.x/aspect)*.6;
 if(!Number.isFinite(half)||half<=0)throw new Error('模型或相機尺度無效');camera.far=Math.max(1000,half*30);
 setAngle(config.initialAngle);ready=true;$('capture').disabled=false;$('status').textContent='已載入。請先校準照片與模型尺度，再判讀比例。';
}catch(error){$('status').textContent=`無法載入：${error.message}`;console.error(error);}

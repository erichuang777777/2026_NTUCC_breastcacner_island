// Appended in module scope by scene_capture_server.py; never loaded by the normal site.
window.__captureFreeze = !window.__captureLookdev;
const captureButton = document.createElement('button');
captureButton.textContent = window.__captureLookdev ? '擷取 lookdev 四個鏡位' : '匯出 GLB 與四個鏡位';
captureButton.style.cssText = 'position:fixed;z-index:9999;top:8px;left:8px';
document.body.append(captureButton);
captureButton.onclick = async () => {
 if (window.__captureLookdev) return captureLookdevShots();
 captureButton.disabled = true;
 const upload = async (path, body) => {
  const response = await fetch('/__capture/' + path, {method:'POST', body});
  if (!response.ok) throw new Error(`Upload ${path}: ${response.status}`);
 };
 const json = (path, value) => upload(path, new Blob([JSON.stringify(value,null,2)], {type:'application/json'}));
 try {
  const {GLTFExporter} = await import('three/addons/exporters/GLTFExporter.js');
  if (!tower || !hospital) throw new Error('Landmarks not ready');
  crowd.setCount(0); person.visible=false;
  controls.enableDamping=false;
  renderer.setPixelRatio(1); renderer.setSize(1920,1080,false);
  camera.aspect=1920/1080; camera.updateProjectionMatrix();
  // Assign stable unique names so Blender can restore day/night material states.
  const objects=[], materials=new Map(), omitted=[];
  scene.traverse(o=>{
   objects.push(o);
   o.name=`capture_${objects.length}_${o.name || o.type}`;
   for(const m of [o.material].flat().filter(Boolean)) if(!materials.has(m.uuid)) {
    m.name=`capture_mat_${materials.size}`; materials.set(m.uuid,m);
   }
  });
  const effectiveVisible=o=>{for(let p=o;p;p=p.parent)if(!p.visible)return false;return true;};
  const state=()=>({objects:Object.fromEntries(objects.map(o=>[o.name,effectiveVisible(o)])),
   materials:Object.fromEntries([...materials.values()].filter(m=>m.emissive).map(m=>[m.name,{color:m.emissive.toArray(),strength:m.emissiveIntensity}])),
   lights:objects.filter(o=>o.isPointLight).map(o=>({name:o.name,position:o.getWorldPosition(new THREE.Vector3()).toArray(),color:o.color.toArray(),intensity:o.intensity,distance:o.distance}))});
  setNight(false); const day=state(); setNight(true); const nightState=state(); setNight(false);
  // Export a detached static world snapshot. Bake instances; retain night-only geometry.
  const exported=new THREE.Scene();
  scene.updateMatrixWorld(true);
  for(const o of objects) {
   if(!day.objects[o.name]&&!nightState.objects[o.name])continue;
   if(o.isSprite||o.isPoints||o.isLine||[o.material].flat().some(m=>m?.isShaderMaterial)||o.isSkinnedMesh){
    omitted.push({name:o.name,type:o.type,reason:'Sprite/points/line/shader/skinning requires a separate baking path'});continue;
   }
   if(!o.isMesh)continue;
   const count=o.isInstancedMesh?o.count:1;
   for(let i=0;i<count;i++){
    const copy=new THREE.Mesh(o.geometry,o.material);copy.name=o.name+(o.isInstancedMesh?`_instance_${i}`:'');
    copy.matrixAutoUpdate=false;copy.matrix.copy(o.matrixWorld);
    if(o.isInstancedMesh){const m=new THREE.Matrix4();o.getMatrixAt(i,m);copy.matrix.multiply(m);}
    if(o.isInstancedMesh && o.instanceColor){
     if(Array.isArray(o.material))throw new Error('Instanced multi-material color baking is unsupported');
     copy.material=o.material.clone();const color=new THREE.Color();o.getColorAt(i,color);copy.material.color.multiply(color);
    }
    copy.userData.captureSource=o.name; exported.add(copy);
   }
  }
  const marker=new THREE.Object3D();marker.name='capture_axis_probe';marker.position.set(1,2,3);exported.add(marker);
  const glb=await new GLTFExporter().parseAsync(exported,{binary:true,onlyVisible:true,trs:false});
  if(!(glb instanceof ArrayBuffer))throw new Error('Expected binary GLB');
  await upload('exports/taiwan-study-scene-v01.glb',new Blob([glb]));
  const config=await (await fetch('/scene/shots.json')).json();
  const landmarks=[['hospital',[...hospitalPoint.slice(0,1),.7,hospitalPoint[1]]],['lighthouse',[towerX,.7,towerZ]]];
  for(let i=0;i<config.shots.length;i++){
   const shot=config.shots[i];setNight(shot.timeOfDay==='night');
   setView(['campus','hospital','tower','island'][i]);
   if(i===3){islandLabels.forEach(o=>o.visible=false);camera.position.copy(controls.target).add(overviewOffset().multiplyScalar(1.08));controls.update();}
   camera.updateMatrixWorld(true);renderer.render(scene,camera);
   Object.assign(shot,{aspect:camera.aspect,fov:camera.getEffectiveFOV(),camera:{position:camera.getWorldPosition(new THREE.Vector3()).toArray(),target:controls.target.toArray(),up:camera.up.toArray(),near:camera.near,far:camera.far},webSource:i===3?'custom: island overviewOffset × 1.08, labels hidden':shot.webSource,
    landmarkPixels:Object.fromEntries(landmarks.map(([key,p])=>{const v=new THREE.Vector3(...p).project(camera);return [key,{world:p,pixel:[(v.x+1)*960,(1-v.y)*540],ndcZ:v.z}];}))});
   const png=await new Promise(resolve=>renderer.domElement.toBlob(resolve,'image/png'));
   if(!png)throw new Error('Canvas PNG encoding failed');await upload(`captures/web/${shot.id}.png`,png);
  }
  config.status='captured from live camera; canvas-only 1920×1080; animation frozen; characters omitted';
  config.capturedAt=new Date().toISOString();
  await json('captures/shots-capture.json',config);
  await json('captures/export-manifest.json',{three:THREE.REVISION,bytes:glb.byteLength,meshes:exported.children.length-1,omitted,states:{day,night:nightState},limitations:['Sprite stars, points, lines and shader beams are omitted from GLB but remain in web captures.','S04 is a static night wide shot; no meteor event is triggered.','No DOM UI is included.'],toneMapping:renderer.toneMapping,exposure:renderer.toneMappingExposure});
  captureButton.textContent='完成：GLB、JSON、四張 PNG 已儲存';
 }catch(error){captureButton.textContent='失敗：'+error.message;console.error(error);}
};


// lookdev 分支不命名場景物件、不匯出 GLB／JSON，擷取後恢復互動。
async function captureLookdevShots() {
 captureButton.disabled=true;
 if (!tower || !hospital) { captureButton.textContent='地標尚未載入，請稍後再試'; captureButton.disabled=false; return; }
 const saved={night,view,position:camera.position.clone(),target:controls.target.clone(),
  aspect:camera.aspect,ratio:renderer.getPixelRatio(),size:renderer.getSize(new THREE.Vector2()),
  damping:controls.enableDamping,labels:islandLabels.map(o=>o.visible)};
 window.__captureFreeze=true;
 // 讓已排程的動畫回呼停止；避免恢復時出現兩條動畫鏈。
 await new Promise(resolve=>requestAnimationFrame(resolve));
 try {
  const response=await fetch('/scene/shots.json');
  if(!response.ok) throw new Error('無法載入鏡位');
  const config=await response.json();
  controls.enableDamping=false;
  renderer.setPixelRatio(1);renderer.setSize(1920,1080,false);
  camera.aspect=1920/1080;camera.updateProjectionMatrix();
  for(let i=0;i<config.shots.length;i++) {
   const shot=config.shots[i];setNight(shot.timeOfDay==='night');
   setView(['campus','hospital','tower','island'][i]);
   if(i===3){islandLabels.forEach(o=>o.visible=false);camera.position.copy(controls.target).add(overviewOffset().multiplyScalar(1.08));controls.update();}
   camera.updateMatrixWorld(true);renderer.render(scene,camera);
   const png=await new Promise(resolve=>renderer.domElement.toBlob(resolve,'image/png'));
   if(!png)throw new Error('Canvas PNG encoding failed');
   const upload=await fetch(`/__capture/captures/web-lookdev/${shot.id}.png`,{method:'POST',body:png});
   if(!upload.ok)throw new Error(`Upload ${shot.id}: ${upload.status}`);
  }
  captureButton.textContent='完成：lookdev 四張 PNG 已儲存';
 } catch(error) { captureButton.textContent='失敗：'+error.message;console.error(error); }
 finally {
  setNight(saved.night);setView(saved.view);
  camera.position.copy(saved.position);controls.target.copy(saved.target);controls.update();
  controls.enableDamping=saved.damping;islandLabels.forEach((o,i)=>o.visible=saved.labels[i]);
  renderer.setPixelRatio(saved.ratio);renderer.setSize(saved.size.x,saved.size.y,false);
  camera.aspect=saved.aspect;camera.updateProjectionMatrix();
  last=performance.now();window.__captureFreeze=false;requestAnimationFrame(animate);
  captureButton.disabled=false;
 }
}

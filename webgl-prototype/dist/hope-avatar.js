import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone} from 'three/addons/utils/SkeletonUtils.js';
import {characterStyles,filmCharacterStyles} from './hope-characters.js?v=22';

const directorSpec={id:'director_wu',name:'院長',style:'short'};
const templates=new Map(),loads=new Map(),loader=new GLTFLoader();
export function loadAvatarLibrary({includeFilm=false}={}){
 const groups=[{styles:characterStyles,version:'v05',kind:'resident'},...(includeFilm?[{styles:filmCharacterStyles,version:'v06',kind:'film'},{styles:[directorSpec],version:'director-v16',kind:'director'}]:[])];
 return Promise.all(groups.flatMap(({styles,version,kind})=>styles.map(spec=>{
  const key=kind+':'+spec.id;
  if(!loads.has(key))loads.set(key,loader.loadAsync(`assets/characters/${version}/${spec.id}.glb`).then(gltf=>templates.set(key,gltf)).catch(error=>{loads.delete(key);throw error;}));
  return loads.get(key);
 })));
}
const shadowCanvas=document.createElement('canvas');shadowCanvas.width=64;shadowCanvas.height=64;
const ctx=shadowCanvas.getContext('2d'),gradient=ctx.createRadialGradient(32,32,3,32,32,31);gradient.addColorStop(0,'rgba(25,45,37,.28)');gradient.addColorStop(.5,'rgba(25,45,37,.13)');gradient.addColorStop(1,'rgba(25,45,37,0)');ctx.fillStyle=gradient;ctx.fillRect(0,0,64,64);
const shadowTexture=new THREE.CanvasTexture(shadowCanvas),shadowGeometry=new THREE.PlaneGeometry(.70,.52);shadowGeometry.rotateX(-Math.PI/2);
const shadowMaterial=new THREE.MeshBasicMaterial({map:shadowTexture,transparent:true,depthWrite:false});
const solePosition=new THREE.Vector3(),actorPosition=new THREE.Vector3();

export function createAvatar(index=0,appearance={},options={}){
 const styles=options.director?[directorSpec]:options.film?filmCharacterStyles:characterStyles,spec=styles[index]||styles[0],template=templates.get((options.director?'director:':options.film?'film:':'resident:')+spec.id);
 if(!template)throw new Error('角色模型尚未載入：'+spec.id);
 const person=new THREE.Group();person.name='hope-avatar-'+spec.id;
 const model=clone(template.scene);person.add(model);person.userData.sharedAvatar=true;
 const style=appearance.style||spec.style,headStyle=style==='mask'?'cap':style==='doctor'?'short':style;
 const ownMaterials=new Map(),bones={},visibleParts=[];
 model.traverse(o=>{
  if(o.isBone)bones[o.name]=o;
  // glTF material groups may be exported as child meshes under the named object.
  if(o.name.startsWith('cast_')){const part=o.name.replace(/^cast_/, '').replace(/_\d+$/,'');o.visible=part==='body'||part===headStyle||(part==='mask'&&style==='mask');if(o.visible)visibleParts.push(part);}
  if(!o.isMesh)return;o.castShadow=options.castShadow!==false;o.receiveShadow=false;o.frustumCulled=false;
  const recolor=m=>{
   if(ownMaterials.has(m.uuid))return ownMaterials.get(m.uuid);
   const copy=m.clone(),key=copy.name.replace(/\.\d+$/,'');
   const color=appearance[key]||(key==='headscarf'?(options.film?appearance.hair:appearance.shirt):null);
   if(color)copy.color.set(color);ownMaterials.set(m.uuid,copy);return copy;
  };
  o.material=Array.isArray(o.material)?o.material.map(recolor):recolor(o.material);
 });
 const shadow=new THREE.Mesh(shadowGeometry,shadowMaterial);shadow.position.y=.012;person.add(shadow);
 const booklet=new THREE.Group();booklet.name='education-booklet';booklet.position.set(0,.57,.20);model.add(booklet);
 const paperMaterial=new THREE.MeshStandardMaterial({color:'#fff5df',roughness:.85}),coverMaterial=new THREE.MeshStandardMaterial({color:'#71998c',roughness:.85});
 const cover=new THREE.Mesh(new THREE.BoxGeometry(.35,.024,.17),coverMaterial),paper=new THREE.Mesh(new THREE.BoxGeometry(.33,.016,.15),paperMaterial);paper.position.y=.017;booklet.add(cover,paper);booklet.visible=false;
 const mixer=new THREE.AnimationMixer(model),actions={};
 for(const clip of template.animations){const name=clip.name.toLowerCase().split('|').at(-1);if(['idle','walk','wave','read','talk','nod','stretch','wish'].includes(name))actions[name]=mixer.clipAction(clip);}
 if(!actions.idle||!actions.walk)throw new Error('角色缺少共用動作');
 let current='idle',gesture=0,gestureType='wave',elapsed=0,lastSpeed=0;
 actions.idle.play();
 model.updateMatrixWorld(true);
 const soles=['L','R'].map(side=>{
  const bone=bones['foot'+side]||bones['foot.'+side]||model.getObjectByName('foot_'+side);
  if(!bone)return null;
  const marker=new THREE.Object3D();marker.position.copy(bone.worldToLocal(new THREE.Vector3(side==='L'?-.092:.092,0,.04)));bone.add(marker);return marker;
 }).filter(Boolean);
 const eyes=['L','R'].map(s=>bones['eye'+s]||bones['eye.'+s]||model.getObjectByName('eye_'+s)).filter(Boolean);
 function update(dt,speed=0,activity='idle',phase=0){
  elapsed+=dt;lastSpeed=speed;gesture=Math.max(0,gesture-dt);
  const desired=speed>.025?'walk':gesture>0?gestureType:activity==='reading'?'read':actions[activity]?activity:'idle';
  if(desired!==current&&actions[desired]){actions[current]?.fadeOut(.18);actions[desired].reset().fadeIn(.18).play();current=desired;}
  // The same authored stride and measured movement drive both players and residents.
  actions.walk.timeScale=THREE.MathUtils.clamp(speed/.64,.25,2.8);
  mixer.update(dt);booklet.visible=current==='read';
  const blinkTime=(elapsed+phase)%4.7,blink=blinkTime>4.48?Math.max(.07,Math.abs(blinkTime-4.59)/.11):1;
  for(const eye of eyes)eye.scale.y=blink;
  model.position.y=0;model.updateMatrixWorld(true);person.getWorldPosition(actorPosition);
  if(soles.length){const footY=Math.min(...soles.map(s=>s.getWorldPosition(solePosition).y));model.position.y=THREE.MathUtils.clamp(actorPosition.y-footY,-.2,.2);}
 }
 function wave(){gesture=2.5;gestureType='wave';}
 function dispose(){mixer.stopAllAction();mixer.uncacheRoot(model);ownMaterials.forEach(m=>m.dispose());paperMaterial.dispose();coverMaterial.dispose();cover.geometry.dispose();paper.geometry.dispose();person.removeFromParent();}
 update(0);
 return {person,model,update,wave,dispose,audit:()=>({asset:options.director?'blender-director-v16':options.film?'blender-film-v06':'blender-cast-v05',kind:options.director?'director':options.film?'film':'resident',role:spec.id,style,visibleParts,appearance:{...appearance},action:current,speed:+lastSpeed.toFixed(3),bones:Object.keys(bones).length,footMarkers:soles.length,blinkBones:eyes.length,groundCorrection:model.position.y,animations:Object.keys(actions)})};
}

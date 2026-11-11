import * as THREE from 'three';
import {onLand,routeClearance} from './taiwan-layout.js?v=15';

export function createLandmarkGardens({scene,island,material,mesh,ball,box,cylinder,colliders,hospitalPoint,towerX,towerZ}){
 const leaves=material('hero-sage','#73936c'),soil=material('hero-soil','#a59b76'),stone=material('hero-limestone','#e5dac2'),petals=['#d8859b','#efb9c3','#f0d9ac'].map((c,i)=>material('hero-petal-'+i,c));
 const lights=[],beds=[],reduced=matchMedia('(prefers-reduced-motion: reduce)');
 function occupied(x,z,r){return colliders.some(c=>c.halfX?Math.abs(x-c.x)<c.halfX+r+.15&&Math.abs(z-c.z)<c.halfZ+r+.15:Math.hypot(x-c.x,z-c.z)<c.r+r+.2);}
 function safe(x,z,r){return routeClearance(x,z)>.55+r&&!occupied(x,z,r)&&Array.from({length:8},(_,i)=>onLand(x+Math.cos(i*Math.PI/4)*r,z+Math.sin(i*Math.PI/4)*r)).every(Boolean);}
 function bed(x,z,index){
  const garden=new THREE.Group();garden.name='carnation-garden-'+index;garden.position.set(x,.7,z);island.add(garden);
  cylinder(garden,stone,0,.055,0,.37,.34,.11,24);cylinder(garden,soil,0,.116,0,.33,.33,.025,24);
  for(let j=0;j<7;j++){
   const a=j*2.4,r=j===0?0:.22,fx=Math.cos(a)*r,fz=Math.sin(a)*r,h=.24+(j%3)*.065;
   cylinder(garden,leaves,fx,.13+h/2,fz,.009,.014,h,6);
   const leaf=ball(garden,leaves,fx+.055,.15+h*.42,fz,.082,.018,.03);leaf.rotation.z=.45;
   for(let k=0;k<6;k++){const t=k*Math.PI/3;const p=ball(garden,petals[(index+j)%3],fx+Math.cos(t)*.045,h+.13,fz+Math.sin(t)*.045,.052,.035,.043);p.rotation.y=t;}
   ball(garden,petals[(index+j+1)%3],fx,h+.151,fz,.035,.026,.035);
  }
  colliders.push({x,z,r:.37});beds.push([x,z]);
 }
 for(const [cx,cz,minR,maxR,count] of [[...hospitalPoint,3.6,7,12],[towerX,towerZ,1.95,4.6,10]]){
  let made=0;
  for(let k=0;k<160&&made<count;k++){const a=k*2.39996,r=minR+(k%7)/6*(maxR-minR),x=cx+Math.cos(a)*r,z=cz+Math.sin(a)*r;if(safe(x,z,.40)){bed(x,z,beds.length);made++;}}
 }
 // Low, legible arrival signage gives the hospital a human-scale entrance.
 function plaque(text,sub,x,y,z,w){
  const c=document.createElement('canvas');c.width=1024;c.height=256;const ctx=c.getContext('2d');ctx.fillStyle='#365b60';ctx.fillRect(0,0,1024,256);ctx.fillStyle='#fff4db';ctx.textAlign='center';ctx.font='600 66px sans-serif';ctx.fillText(text,512,105);ctx.font='28px sans-serif';ctx.fillStyle='#d5e7dc';ctx.fillText(sub,512,176);
  const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
  const m=new THREE.MeshStandardMaterial({map:t,roughness:.72,emissiveMap:t,emissive:'#ffffff',emissiveIntensity:.1});
  box(island,stone,x,y,z,w+.11,w*.25+.09,.08,.025);const sign=mesh(new THREE.PlaneGeometry(w,w*.25),m,island,x,y,z+.045);sign.castShadow=false;lights.push(m);
 }
 plaque('臺大癌醫中心','每一步，都有我們同行',hospitalPoint[0]-1.9,1.20,hospitalPoint[1]+2.5,1.5);
 for(const dx of [-2.45,-1.35])cylinder(island,stone,hospitalPoint[0]+dx,.94,hospitalPoint[1]+2.5,.025,.025,.48,10);
 // Ground lanterns belong beside the gardens, away from the connected shore corridors.
 for(let i=0;i<beds.length;i+=3){const [x,z]=beds[i],glow=new THREE.MeshStandardMaterial({color:'#fff0ca',emissive:'#ffcd83',emissiveIntensity:.25,roughness:.45});cylinder(island,stone,x,.80,z,.09,.12,.20,12);ball(island,glow,x,.95,z,.09,.13,.09);lights.push(glow);}
 const beacon=new THREE.Group();beacon.name='hope-lighthouse-beacon';beacon.position.set(towerX,6.2,towerZ);scene.add(beacon);
 const beamMaterial=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,blending:THREE.AdditiveBlending,uniforms:{strength:{value:0}},vertexShader:'varying vec3 p;varying vec3 viewP;varying vec3 viewN;void main(){p=position;vec4 v=modelViewMatrix*vec4(position,1.);viewP=v.xyz;viewN=normalMatrix*normal;gl_Position=projectionMatrix*v;}',fragmentShader:'varying vec3 p;varying vec3 viewP;varying vec3 viewN;uniform float strength;void main(){float d=clamp((7.5-p.y)/15.,0.,1.);float facing=pow(abs(dot(normalize(viewN),normalize(-viewP))),2.);float a=pow(1.-d,2.)*smoothstep(0.,.12,d)*facing*strength;gl_FragColor=vec4(1.,.83,.53,a);}' });
 for(const direction of [1,-1]){const beam=new THREE.Mesh(new THREE.ConeGeometry(2.2,15,32,1,true),beamMaterial);beam.rotation.z=direction*Math.PI/2;beam.position.x=direction*7.5;beacon.add(beam);}
 let night=false;
 function setNight(value){night=value;beamMaterial.uniforms.strength.value=night?.06:0;lights.forEach(m=>m.emissiveIntensity=night?1.6:.12);}
 function update(dt,t,pulse=0){beacon.rotation.y=reduced.matches?.4:t*.11;beamMaterial.uniforms.strength.value=night?.06+pulse*.025:0;}
 return {setNight,update,audit:()=>({carnationBeds:beds.length,hospitalSign:true,beacon:night})};
}

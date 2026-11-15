import * as THREE from 'three';
export function createCelestial(scene){
 function texture(moon){
  const canvas=document.createElement('canvas');canvas.width=canvas.height=256;const c=canvas.getContext('2d');
  const glow=c.createRadialGradient(128,128,48,128,128,125);glow.addColorStop(0,moon?'#e5efff80':'#ffe3a580');glow.addColorStop(1,'#ffffff00');c.fillStyle=glow;c.fillRect(0,0,256,256);
  const disk=c.createRadialGradient(108,104,0,128,128,63);disk.addColorStop(0,moon?'#fff9e5':'#fffbe3');disk.addColorStop(1,moon?'#b9c9d9':'#ffd180');c.fillStyle=disk;c.beginPath();c.arc(128,128,62,0,Math.PI*2);c.fill();
  if(moon){c.save();c.clip();for(const [x,y,r] of [[100,109,13],[144,91,8],[151,141,18],[112,156,9],[87,142,6],[135,174,5]]){c.fillStyle='#8295ab35';c.beginPath();c.ellipse(x,y,r,r*.8,-.4,0,Math.PI*2);c.fill();}c.restore();}
  return new THREE.CanvasTexture(canvas);
 }
 const sun=new THREE.Sprite(new THREE.SpriteMaterial({map:texture(false),transparent:true,depthWrite:false,depthTest:true,fog:false,toneMapped:false}));
 const moon=new THREE.Sprite(new THREE.SpriteMaterial({map:texture(true),transparent:true,depthWrite:false,depthTest:true,fog:false,toneMapped:false}));
 sun.name='day-cycle-sun';moon.name='day-cycle-moon';scene.add(sun,moon);
 const uniforms={zenith:{value:new THREE.Color('#76b6d0')},horizon:{value:new THREE.Color('#d9eaf0')}};
 const dome=new THREE.Mesh(new THREE.SphereGeometry(440,48,24),new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,uniforms,vertexShader:'varying vec3 direction; void main(){direction=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',fragmentShader:'varying vec3 direction; uniform vec3 zenith; uniform vec3 horizon; void main(){float t=smoothstep(-0.03,0.75,normalize(direction).y);gl_FragColor=vec4(mix(horizon,zenith,t),1.0);\n#include <colorspace_fragment>\n}',fog:false,toneMapped:false}));
 dome.name='world-sky-dome';dome.renderOrder=-10;scene.add(dome);
 const dayTop=new THREE.Color('#76b6d0'),nightTop=new THREE.Color('#071326'),dayHorizon=new THREE.Color('#d9eaf0'),nightHorizon=new THREE.Color('#29445b'),dusk=new THREE.Color('#d49b80');
 let projections={};
 function update(state,camera){
  uniforms.zenith.value.copy(nightTop).lerp(dayTop,state.daylight);uniforms.horizon.value.copy(nightHorizon).lerp(dayHorizon,state.daylight).lerp(dusk,state.twilight*.55);
  for(const [object,isMoon] of [[sun,false],[moon,true]]){
   const elevation=state.elevation*(isMoon?-1:1),a=state.angle+(isMoon?Math.PI:0);
   object.material.opacity=Math.max(0,Math.min(1,elevation/.12));object.visible=elevation>0;
   // World-space orbit on the far dome. Camera changes never reposition the bodies.
   object.position.set(Math.sin(a)*.10,Math.cos(a)*.13,-.9).normalize().multiplyScalar(410);
   object.scale.setScalar(isMoon?23:25);
   if(camera){camera.updateMatrixWorld();const p=object.position.clone().project(camera);projections[isMoon?"moonScreen":"sunScreen"]={x:p.x,y:p.y,inFrame:object.visible&&Math.abs(p.x)<1&&Math.abs(p.y)<1&&p.z>-1&&p.z<1};}
  }
 }
 return {update,sunDirection:()=>sun.position.clone().normalize(),audit:()=>({worldSpace:true,...projections,domeRadius:440,sunVisible:sun.visible,moonVisible:moon.visible,sunPosition:sun.position.toArray(),moonPosition:moon.position.toArray()})};
}

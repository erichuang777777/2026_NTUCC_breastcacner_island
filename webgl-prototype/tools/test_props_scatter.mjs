// 無伺服器／WebGL：使用真實 GLB 結構與島形，替身只涵蓋 Three.js 算圖介面。
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
import vm from 'node:vm';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');
const uri=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const coastURI=uri(read('../taiwan-coastline.js'));
const layout=await import(uri(read('../taiwan-layout.js').replace("'./taiwan-coastline.js?v=15'",JSON.stringify(coastURI))));
const manifest=JSON.parse(read('../../art-source/props/export/v02/manifest.json'));
const source=read('./props_scatter_hook.js');
class Matrix {clone(){return new Matrix();}multiplyMatrices(a,b){this.inputs=[a,b];return this;}}
class Object3D {constructor(){this.position={set(){}};this.rotation={set(){}};this.scale={setScalar(){}};this.matrix=new Matrix();}updateMatrix(){}}
class Group {constructor(){this.visible=true;this.children=[];}add(o){this.children.push(o);}}
class InstancedMesh {constructor(g,m,count){this.geometry=g;this.material=m;this.count=count;this.visible=true;this.instanceMatrix={};this.matrices=[];}setMatrixAt(i,m){assert.equal(m.inputs.length,2);this.matrices[i]=m.clone();}computeBoundingBox(){}computeBoundingSphere(){}}
class Geometry {
 constructor(count,values=[]) {this.index={count};const data=Float32Array.from(values);this.attributes={position:{data,count:data.length/3,getX:i=>data[i*3],getY:i=>data[i*3+1],getZ:i=>data[i*3+2],setXYZ(i,x,y,z){assert([x,y,z].every(Number.isFinite));data.set([x,y,z],i*3);}}};}
 computeVertexNormals(){}clone(){return new Geometry(this.index.count,this.attributes.position.data);}applyMatrix4(){return this;}dispose(){}
}
const mergeGeometries=gs=>new Geometry(gs.reduce((n,g)=>n+g.index.count,0),gs.flatMap(g=>Array.from(g.attributes.position.data)));
class GLTFLoader {async loadAsync(url){
 const buffer=readFileSync(new URL('../../'+url.replace(/^\//,''),import.meta.url));
 const glb=JSON.parse(buffer.subarray(20,20+buffer.readUInt32LE(12)).toString());
 const binary=28+buffer.readUInt32LE(12);
 const positions=p=>{const a=glb.accessors[p.attributes.POSITION],v=glb.bufferViews[a.bufferView],offset=binary+(v.byteOffset||0)+(a.byteOffset||0);return Array.from({length:a.count*3},(_,i)=>buffer.readFloatLE(offset+Math.floor(i/3)*(v.byteStride||12)+i%3*4));};
 const materials=glb.materials.map(m=>({name:m.name,clone(){return {...this};}}));
 const meshes=glb.meshes.flatMap(m=>m.primitives.map(p=>({isMesh:true,
  geometry:new Geometry(glb.accessors[p.indices].count,positions(p)),matrixWorld:new Matrix(),
  material:materials[p.material]})));
 return {scene:{updateMatrixWorld(){},traverse:fn=>meshes.forEach(fn)}};
}}
async function run() {
 const scene=new Group(),colliders=JSON.parse(read('../../art-source/captures/web-props/stats.json')).obstacles;
 let fail=false;
 const renderer={shadowMap:{},info:{autoReset:true,render:{calls:0,triangles:0},reset(){this.render={calls:0,triangles:0};}},render(){
  if(fail)throw Error('mock GPU failure');
  this.info.render.calls+=100;this.info.render.triangles+=1000;
  const root=scene.children[0];if(root?.visible)for(const m of root.children)if(m.visible&&m.count){
   this.info.render.calls+=4;this.info.render.triangles+=4*m.count*m.geometry.index.count/3;
  }
 }};
 const context=vm.createContext({...layout,modules:{GLTFLoader,mergeGeometries,coastline:layout.coastline,routes:layout.routes},
  THREE:{Group,Object3D,Matrix4:Matrix,InstancedMesh},scene,colliders,renderer,camera:{},
  window:{hopeStudy:{},__lookdev:{quality:'high'},__propsObstacles:colliders},night:false,
  setNight(value){context.night=value;},towerX:layout.pieces[4].center[0],towerZ:layout.pieces[4].center[1],
  hospitalPoint:[3.75,-2],landscape:{anchors:[]},console:{table(){},warn(){}},
  fetch:async()=>({ok:true,json:async()=>manifest})});
 const executable=source.replace(/import\('[^']+'\)/g,'Promise.resolve(modules)');
 await vm.runInContext(`(async()=>{${executable}})()`,context);
 const api=context.window.__propsScatter;
 assert(context.window.__captureProps);
 const placements=scene.children[0].children;
 assert(placements.length>0);assert(placements.every(m=>m.matrices.length===m.count));
 assert(Object.values(api.inventory()).every(a=>a.instances<=a.requested));
 assert(api.report([]).totalGeometryTriangles<=api.params.limits.triangles);
 const glow=placements.find(m=>m.material.name==='hope-prop-lamp-glow');
 assert(glow,'至少有一盞路燈');context.window.hopeStudy.setNight(true);assert.equal(glow.material.emissiveIntensity,4);
 context.setNight(false);assert.equal(glow.material.emissiveIntensity,.15);
 const report=api.report([]);
 for(const [id,points] of Object.entries(report.placements))for(const p of points) {
  if(id.startsWith('rock-')||id==='foam-ring'||id==='path-straight'||id==='path-curve')continue;
  assert(layout.onLand(p.x,p.z));

  for(const c of colliders){
   const d=Math.hypot(Math.max(0,Math.abs(p.x-c.x)-(c.halfX??c.r)),Math.max(0,Math.abs(p.z-c.z)-(c.halfZ??c.r)));
   if(id==='path-plaza')assert(Math.abs(p.x-c.x)>=c.halfX+.6*p.scale+api.params.clearance || Math.abs(p.z-c.z)>=c.halfZ+.6*p.scale+api.params.clearance);else assert(d>=p.r+api.params.clearance);
  }
 }
 // 構圖契約：完整廣場、群組數量、家具朝向、岩石與浪花成對。
 for(const plaza of report.plazas) {
  assert.equal(plaza.tiles,plaza.cols*plaza.rows);
  assert.equal(plaza.centers.length,plaza.tiles);
  for(const [x,z] of plaza.centers)assert(report.placements['path-plaza'].some(p=>Math.hypot(p.x-x,p.z-z)<1e-6));
 }
 for(const group of report.groups) {
  const members=report.placements[group.id].filter(p=>p.group===group.group);
  assert.equal(members.length,group.count);assert(group.count>=(group.id==='tree-round'?3:2)&&group.count<=5);
 }
 for(const id of ['lamp','bench'])for(let route=0;route<report.paths.length;route++)assert(report.placements[id].some(p=>p.route===route),'各步道均有街道家具');
 for(const p of report.placements.bench) {
  const dx=p.anchor[0]-p.x,dz=p.anchor[1]-p.z;
  assert((Math.sin(p.rotation)*dx+Math.cos(p.rotation)*dz)/Math.hypot(dx,dz)>.999,'長椅朝向步道');
 }
 for(const p of report.placements.lamp)assert(Math.abs(Math.hypot(p.x-p.anchor[0],p.z-p.anchor[1])-.9)<1e-6);
 const rocks=[...report.placements['rock-shore-a'],...report.placements['rock-shore-b']];
 for(const p of report.placements['foam-ring'])assert(rocks.some(r=>Math.hypot(p.x-r.x,p.z-r.z)<.041));
 for(const mesh of placements.filter(m=>/^props-path-(straight|curve)/.test(m.name))) {
  const v=mesh.geometry.attributes.position;
  assert(v.count>0,'使用真實 GLB 頂點測試變形');
  for(let i=0;i<v.count;i++) {
   const x=v.getX(i),z=v.getZ(i);assert(layout.onLand(x,z),'曲線鋪面不得浮在海上');
   for(const c of colliders)assert(Math.abs(x-c.x)>=c.halfX || Math.abs(z-c.z)>=c.halfZ,'曲線鋪面不得進入障礙物');
  }
 }
 const initial=JSON.stringify(report.placements),pair=api.measurePair();
 assert.equal(pair.baseline.calls,100);assert(pair.added.calls>0);assert.equal(renderer.info.autoReset,true);
 assert.equal(api.root.visible,true);
 fail=true;assert.throws(()=>api.measurePair(),/mock GPU/);assert.equal(renderer.info.autoReset,true);assert.equal(api.root.visible,true);fail=false;
 assert(pair.added.calls>80,'多 pass 計數超過 80 仍保留全部道具');
 assert.deepEqual(api.report([]).placements,report.placements);
 assert(api.assertBudget().instancedMeshes<=80);
 for(const [id,range] of Object.entries(api.params.targets))assert(report.assets[id].instances===range[2],`${id}: ${report.assets[id].instances}`);
 for(const path of report.paths){assert(path.connected,path.name);for(let i=1;i<path.points.length;i++)assert(Math.hypot(path.points[i][0]-path.points[i-1][0],path.points[i][1]-path.points[i-1][1])<=.800001);}
 for(const d of Object.values(report.diagnostics))assert.equal(d.candidates,d.accepted+Object.values(d.rejected).reduce((n,v)=>n+v,0));
 for(const a of manifest.assets)assert(report.assets[a.id].instancedMeshes<=a.materials.length,'同材質子網格已合併');
 console.log(JSON.stringify({counts:Object.fromEntries(Object.entries(report.assets).map(([id,a])=>[id,a.instances])),budget:api.assertBudget(),paths:report.paths.map(p=>({name:p.name,connected:p.connected}))}));
 if(process.argv.includes('--report')) {
  const folder=new URL('../../art-source/lookdev/props-round3/',import.meta.url);mkdirSync(folder,{recursive:true});
  writeFileSync(new URL('stats-layout.json',folder),JSON.stringify({...report,validation:'CPU placement and actual GLB vertex checks; obstacles reused from round2; not a WebGL capture'},null,2));
 }
 return initial;
}
// 合批前擷取：保留建築和大型物件，忽略小物、島形與整區群組。
const object=(name,w,h,d,y=.7)=>({name,isGroup:true,bounds:{min:{x:-w/2,y,z:-d/2},max:{x:w/2,y:y+h,z:d/2}}});
const objects=[object('specialty-building-0',2,3,2),object('',1,2,1),object('small',.2,.3,.2),object('zone',30,1,30),object('ground',20,.2,20,0)];
class Box3 {
 setFromObject(o){Object.assign(this,o.bounds);return this;}
 getSize(){return {x:this.max.x-this.min.x,y:this.max.y-this.min.y,z:this.max.z-this.min.z};}
 isEmpty(){return false;}
}
const obstacleContext=vm.createContext({window:{},scene:{updateMatrixWorld(){},traverse(fn){objects.forEach(fn);}},island:{children:objects},THREE:{Box3,Vector3:class {}}});
vm.runInContext(read('./props_obstacles_hook.js'),obstacleContext);
assert.equal(obstacleContext.window.__propsObstacles.length,2);
assert.equal(obstacleContext.window.__propsObstacles[1].name,'large-object-1');
assert.equal(await run(),await run(),'相同種子應產生相同實例數');
console.log('道具：真實 GLB 三角形數、島形配置、固定種子、子網格矩陣、日夜同步、整幀計數／復原、合併材質、連續步道與獨立幾何預算通過（非 WebGL）。');

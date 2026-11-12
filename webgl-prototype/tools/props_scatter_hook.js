// 僅供 --lookdev --props 注入；所有可調散佈參數集中於此。
const PROPS_SCATTER_PARAMS = {
 seed: 20261112, baseURL: '/art-source/props/export/v02/',
 groundY: .702, seaY: -.43, clearance: .08, routeHalfWidth: .4, instanceGap: .04,
 grid: {step: .65, jitter: .45}, vegetationScale: [.85, 1.05],
 path: {module: .8, centralPlaza: [-.4, 0]},
 coast: {spacing: 2.55, offset: .7, scale: [.8, 1.3], foamOffset: 1.1},
 lamp: {day: .15, night: 4}, limits: {triangles: 1500000, instancedMeshes: 80},
 targets: {'shrub-cluster':[150,300,200], 'flowerbed-round':[40,80,50],
  'flowerbed-long':[20,40,25], 'tree-round':[60,120,80],
  'rock-shore-a':[20,40,30], 'rock-shore-b':[20,40,30], 'foam-ring':[40,80,60],
  lamp:[30,50,40], bench:[20,40,30], signpost:[6,10,8]}

};
{
 const P=PROPS_SCATTER_PARAMS;
 const [{GLTFLoader},{coastline,routes},{mergeGeometries}]=await Promise.all([
  import('three/addons/loaders/GLTFLoader.js'),import('./taiwan-layout.js?v=15'),import('three/addons/utils/BufferGeometryUtils.js')
 ]);
 const response=await fetch(P.baseURL+'manifest.json');
 if(!response.ok)throw new Error(`道具 manifest 載入失敗：${response.status}`);
 const manifest=await response.json(), loader=new GLTFLoader();
 const assets=await Promise.all(manifest.assets.map(async a=>{
  if(!/^[a-z0-9-]+\.glb$/.test(a.file))throw new Error('不合法的道具檔名');
  const gltf=await loader.loadAsync(P.baseURL+a.file), children=[], groups=new Map();
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(o=>{if(o.isMesh){
   if(o.isSkinnedMesh || Array.isArray(o.material))throw new Error(`不支援的子網格：${a.id}`);
   if(!groups.has(o.material))groups.set(o.material,[]);
   groups.get(o.material).push(o.geometry.clone().applyMatrix4(o.matrixWorld));
  }});
  for(const [material,geometries] of groups) {
   const geometry=mergeGeometries(geometries,false);
   if(!geometry)throw new Error(`同材質幾何無法合併：${a.id}/${material.name}`);
   children.push({geometry,material:material.clone(),matrix:new THREE.Matrix4()});
   geometries.forEach(g=>g.dispose());
  }
  const triangles=children.reduce((n,o)=>n+(o.geometry.index?.count??o.geometry.attributes.position.count)/3,0);
  if(!children.length || triangles!==a.triangles)throw new Error(`道具三角形數不符 manifest：${a.id}`);
  return {...a,triangles,children,placements:[],meshes:[]};
 }));
 const byId=Object.fromEntries(assets.map(a=>[a.id,a]));
 let state=P.seed>>>0;
 const random=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;};
 const between=([a,b])=>a+(b-a)*random();
 const occupied=[], pathPoints=[], reductions=[], paths=[], obstacles=[];
 const diagnostics=Object.fromEntries(assets.map(a=>[a.id,{candidates:0,accepted:0,rejected:{}}]));
 obstacles.push(...window.__propsObstacles);
 const colliderDistance=(x,z,c)=>Math.hypot(Math.max(0,Math.abs(x-c.x)-c.halfX),Math.max(0,Math.abs(z-c.z)-c.halfZ));
 const landDisk=(x,z,r)=>onLand(x,z)&&Array.from({length:12},(_,i)=>{
  const a=i*Math.PI/6;return onLand(x+Math.cos(a)*r,z+Math.sin(a)*r);
 }).every(Boolean);
 const segmentDistance=(x,z,a,b)=>{
  const dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));
  return Math.hypot(x-a[0]-t*dx,z-a[1]-t*dz);
 };
 const mainRoutes=routes.slice(-2);
 const routeDistance=(x,z)=>Math.min(...mainRoutes.flatMap(line=>line.slice(1).map((p,i)=>segmentDistance(x,z,line[i],p))),
  ...paths.flatMap(line=>line.points.slice(1).map((p,i)=>segmentDistance(x,z,line.points[i],p))));
 let geometryTriangles=0,meshCount=0;
 function add(id,x,z,rotation=0,scale=1,kind='decor') {
  const a=byId[id],r=Math.hypot(a.dimensions[0],a.dimensions[2])*scale/2,d=diagnostics[id];
  d.candidates++;
  const reject=reason=>{d.rejected[reason]=(d.rejected[reason]||0)+1;return false;};
  if(kind!=='coast') {
   if(!landDisk(x,z,r))return reject('shore');
   const obstacle=obstacles.find(c=>colliderDistance(x,z,c)<r+P.clearance);
   if(obstacle)return reject(`${obstacle.type}:${obstacle.name}`);
   if(kind!=='path') {
    if(routeDistance(x,z)<r+P.routeHalfWidth)return reject('main-route');
    if(occupied.some(o=>Math.hypot(x-o.x,z-o.z)<r+o.r+P.instanceGap))return reject('prop');
   }
  }
  if(geometryTriangles+a.triangles>P.limits.triangles)return reject('geometry-budget');
  if(!a.placements.length && meshCount+a.children.length>P.limits.instancedMeshes)return reject('mesh-budget');
  if(!a.placements.length)meshCount+=a.children.length;
  geometryTriangles+=a.triangles;d.accepted++;
  a.placements.push({x,z,rotation,scale,y:kind==='coast'?P.seaY:P.groundY,r});
  if(kind!=='coast')occupied.push({x,z,r});
  if(kind==='path')pathPoints.push([x,z]);
  return true;
 }
 const points=pieces.flatMap(p=>p.points),xs=points.map(p=>p[0]),zs=points.map(p=>p[1]);
 const minX=Math.min(...xs),maxX=Math.max(...xs),minZ=Math.min(...zs),maxZ=Math.max(...zs);
 // 四向網格搜尋避開建築；每格一片縮為 0.8 的廣場磚，轉角也沒有斷口。
 const m=P.path.module, tileScale=m/1.2, tileRadius=m/Math.SQRT2;
 const nodes=new Map(),key=(i,j)=>`${i},${j}`;
 for(let i=Math.floor(minX/m);i<=Math.ceil(maxX/m);i++)for(let j=Math.floor(minZ/m);j<=Math.ceil(maxZ/m);j++) {
  const x=i*m,z=j*m;
  if(landDisk(x,z,tileRadius)&&!obstacles.some(c=>colliderDistance(x,z,c)<tileRadius+P.clearance))nodes.set(key(i,j),{i,j,point:[x,z]});
 }
 const nearest=point=>[...nodes.values()].sort((a,b)=>Math.hypot(a.point[0]-point[0],a.point[1]-point[1])-Math.hypot(b.point[0]-point[0],b.point[1]-point[1]))[0];
 const frontage=(name,fallback)=>{
  const b=obstacles.find(o=>o.name===name);return b?[b.x,b.z+b.halfZ+tileRadius+P.clearance]:fallback;
 };
 const entrance=frontage('ntu-cancer-center',[hospitalPoint[0],hospitalPoint[1]+3.2]);
 const towerEntry=frontage('hope-lighthouse',[towerX,towerZ+2.2]);
 const paved=new Set();
 function pave(point) {
  const k=point.join(',');if(paved.has(k))return true;
  if(!add('path-plaza',...point,0,tileScale,'path'))return false;
  paved.add(k);return true;
 }
 function connect(name,from,to) {
  const start=nearest(from),end=nearest(to),queue=start?[start]:[],previous=new Map();
  if(start)previous.set(key(start.i,start.j),null);
  for(let head=0;head<queue.length;head++) {
   const n=queue[head];if(n===end)break;
   for(const [di,dj] of [[1,0],[-1,0],[0,1],[0,-1]]) {
    const k=key(n.i+di,n.j+dj),next=nodes.get(k);
    if(next&&!previous.has(k)){previous.set(k,n);queue.push(next);}
   }
  }
  const line=[];
  if(end&&previous.has(key(end.i,end.j)))for(let n=end;n;n=previous.get(key(n.i,n.j)))line.push(n.point);
  line.reverse();
  const result={name,from,to,points:line,connected:line.length>0};
  paths.push(result);
  if(!line.length)result.reason='沒有可連通的陸地網格，請檢查建築／岸線包圍盒';
  for(const p of line)if(!pave(p)){result.connected=false;result.reason='鋪面遭避讓或幾何預算排除';}
 }
 connect('醫院入口 → 中央廣場',entrance,P.path.centralPlaza);
 connect('中央廣場 → 燈塔',P.path.centralPlaza,towerEntry);
 const plazas=[{name:'中央廣場',point:P.path.centralPlaza},...obstacles.filter(o=>o.name.startsWith('specialty-building-')).map(o=>({name:o.name,point:frontage(o.name)}))];
 const plazaStats=plazas.map(p=>{
  const center=nearest(p.point);let tiles=0;
  if(center)for(let dx=-1;dx<=1;dx++)for(let dz=0;dz<2;dz++)if(pave([center.point[0]+dx*m,center.point[1]+dz*m]))tiles++;
  return {...p,tiles,reason:tiles<6?'部分鋪面被岸線或實際物件包圍盒排除':null};
 });
 const candidates=[];
 for(let x=minX;x<=maxX;x+=P.grid.step)for(let z=minZ;z<=maxZ;z+=P.grid.step)
  candidates.push([x+(random()-.5)*P.grid.jitter,z+(random()-.5)*P.grid.jitter]);
 for(let i=candidates.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[candidates[i],candidates[j]]=[candidates[j],candidates[i]];}
 const nearPath=([x,z])=>Math.min(...pathPoints.map(p=>Math.hypot(x-p[0],z-p[1])),...plazas.map(p=>Math.hypot(x-p.point[0],z-p.point[1])));
 const ordered=[...candidates].sort((a,b)=>nearPath(a)-nearPath(b));
 // 先放大件花圃與樹，再以灌木填空；先滿足每類下限，再增加至目標。
 const decorOrder=['flowerbed-long','tree-round','flowerbed-round','shrub-cluster','lamp','bench','signpost'];
 for(const targetIndex of [0,2])for(const id of decorOrder) {
  const preferred=['lamp','bench','signpost','flowerbed-round','flowerbed-long'].includes(id)?ordered:candidates;
  for(const [x,z] of preferred) {
   if(byId[id].placements.length>=P.targets[id][targetIndex])break;
   add(id,x,z,random()*Math.PI*2,between(P.vegetationScale));
  }
 }
 // 依海岸線弧長取樣，以 onLand 判定法線朝外；不用原點放射縮放。
 let next=0,traveled=0,coastIndex=0;
 for(let i=0;i<coastline.length;i++) {
  const a=coastline[i],b=coastline[(i+1)%coastline.length],dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz);
  if(!length)continue;
  while(next<traveled+length) {
   const t=(next-traveled)/length,x=a[0]+t*dx,z=a[1]+t*dz;
   let nx=-dz/length,nz=dx/length;
   if(insidePolygon(x+nx*.15,z+nz*.15,coastline)){nx=-nx;nz=-nz;}
   const px=x+nx*P.coast.offset,pz=z+nz*P.coast.offset;
   if(!onLand(px,pz) && coastIndex<P.targets['foam-ring'][2]) {
    add(coastIndex++%2?'rock-shore-a':'rock-shore-b',px,pz,random()*Math.PI*2,between(P.coast.scale),'coast');
    add('foam-ring',px+nx*P.coast.foamOffset,pz+nz*P.coast.foamOffset,random()*Math.PI*2,between(P.coast.scale),'coast');
   }
   next+=P.coast.spacing;
  }
  traveled+=length;
 }
 const requested=Object.fromEntries(assets.map(a=>[a.id,a.placements.length]));
 const root=new THREE.Group();root.name='props-scatter-v02-round2';
 const transform=new THREE.Object3D(),matrix=new THREE.Matrix4();
 for(const a of assets)for(const child of a.children) {
  if(!a.placements.length)continue;
  const instanced=new THREE.InstancedMesh(child.geometry,child.material,a.placements.length);
  instanced.name=`props-${a.id}-${a.meshes.length}`;
  instanced.castShadow=!a.id.startsWith('path-')&&a.id!=='foam-ring';instanced.receiveShadow=true;
  a.placements.forEach((p,i)=>{
   transform.position.set(p.x,p.y,p.z);transform.rotation.set(0,p.rotation,0);transform.scale.setScalar(p.scale);transform.updateMatrix();
   instanced.setMatrixAt(i,matrix.multiplyMatrices(transform.matrix,child.matrix));
  });
  instanced.instanceMatrix.needsUpdate=true;instanced.computeBoundingBox();instanced.computeBoundingSphere();
  a.meshes.push(instanced);root.add(instanced);
 }
 scene.add(root);
 const glow=assets.flatMap(a=>a.children.map(c=>c.material)).filter(m=>m.name===manifest.lamp_emission_material);
 const syncNight=()=>glow.forEach(m=>{m.emissiveIntensity=night?P.lamp.night:P.lamp.day;});
 const previousSetNight=setNight;
 setNight=function(value){previousSetNight(value);syncNight();};
 // hopeStudy 原本持有舊函式參照，也同步替換。
 window.hopeStudy.setNight=setNight;syncNight();
 function inventory() {
  return Object.fromEntries(assets.map(a=>[a.id,{requested:requested[a.id],instances:a.meshes[0]?.count??0,
   trianglesPerInstance:a.triangles,triangles:a.triangles*(a.meshes[0]?.count??0),
   instancedMeshes:a.meshes.filter(m=>m.count>0).length,
   targetRange:P.targets[a.id]?.slice(0,2)??null,
   belowMinimumReason:P.targets[a.id] && a.placements.length<P.targets[a.id][0]
    ? {message:'候選點不足或幾何預算限制；詳見排除計數',rejected:diagnostics[a.id].rejected}:null}]));
 }
 function measure(visible) {
  const autoReset=renderer.info.autoReset,wasVisible=root.visible;
  try {
   root.visible=visible;renderer.info.autoReset=false;renderer.info.reset();
   renderer.shadowMap.needsUpdate=true;renderer.render(scene,camera);
   return {calls:renderer.info.render.calls,triangles:renderer.info.render.triangles};
  } finally {renderer.info.autoReset=autoReset;root.visible=wasVisible;}
 }
 function measurePair() {
  const baseline=measure(false),withProps=measure(true);
  return {baseline,withProps,added:{calls:withProps.calls-baseline.calls,triangles:withProps.triangles-baseline.triangles}};
 }
 function budget() {
  const values=Object.values(inventory());
  return {triangles:values.reduce((n,a)=>n+a.triangles,0),instancedMeshes:root.children.length};
 }
 function assertBudget() {
  const b=budget();
  if(b.triangles>P.limits.triangles || b.instancedMeshes>P.limits.instancedMeshes)throw new Error('道具幾何預算超標');
  return b;
 }
 window.__propsScatter={params:P,root,inventory,measurePair,reductions,assertBudget,
  report:shots=>({version:'v02-round2',seed:P.seed,quality:window.__lookdev.quality,params:P,
   countMethod:'Budget: prop InstancedMesh objects and instances × geometry triangles only. renderer.info before/after includes all render passes and is informational.',
   assets:inventory(),totalGeometryTriangles:budget().triangles,totalInstancedMeshes:budget().instancedMeshes,
   candidateGridPoints:candidates.length,diagnostics,obstacles,paths,plazas:plazaStats,
   placements:Object.fromEntries(assets.map(a=>[a.id,a.placements])),reductions,shots})};
 assertBudget();
 window.__captureProps=true;
 console.table(inventory());
}

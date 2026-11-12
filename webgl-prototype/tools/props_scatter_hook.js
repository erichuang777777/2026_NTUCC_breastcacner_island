// 僅供 --lookdev --props 注入；所有可調散佈參數集中於此。
const PROPS_SCATTER_PARAMS = {
 seed: 20261112, baseURL: '/art-source/props/export/v02/',
 groundY: .702, seaY: -.43, clearance: .08, routeHalfWidth: .62, instanceGap: .04,
 vegetationScale: [.85, 1.05],
 path: {module: 1.2, centralPlaza: [-2.4, 2.4]},
 coast: {spacing: 2.55, offset: .12, scale: [.8, 1.3], foamOffset: .04},
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
 const occupied=[], reductions=[], paths=[], obstacles=[];
 const radius=(a,scale)=> (['tree-round','shrub-cluster','flowerbed-round'].includes(a.id)?Math.max(a.dimensions[0],a.dimensions[2]):Math.hypot(a.dimensions[0],a.dimensions[2]))*scale/2;
 const plant=id=>id==='shrub-cluster'||id?.startsWith('flowerbed-');
 // 低矮植栽可以進入樹冠投影，但仍須避開樹幹。
 const propOverlap=(a,b)=>{
  const ar=a.id==='tree-round'&&plant(b.id) ? .14 : a.r,br=b.id==='tree-round'&&plant(a.id) ? .14 : b.r;
  return Math.hypot(a.x-b.x,a.z-b.z)<ar+br+P.instanceGap;
 };
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
 const routeDistance=(x,z)=>Math.min(...paths.flatMap(line=>line.points.slice(1).map((p,i)=>segmentDistance(x,z,line.points[i],p))));
 let geometryTriangles=0,meshCount=0;
 function add(id,x,z,rotation=0,scale=1,kind='decor') {
  const a=byId[id],r=radius(a,scale),d=diagnostics[id];
  d.candidates++;
  const reject=reason=>{d.rejected[reason]=(d.rejected[reason]||0)+1;return false;};
  if(kind!=='coast'&&kind!=='ribbon') {
   if(kind==='path'? !clearTile(x,z,.6*scale): !landDisk(x,z,r))return reject('shore');
   const obstacle=obstacles.find(c=>colliderDistance(x,z,c)<r+P.clearance);
   if(obstacle&&kind!=='path')return reject(`${obstacle.type}:${obstacle.name}`);
   if(kind!=='path') {
    if(routeDistance(x,z)<r+P.routeHalfWidth)return reject('main-route');
    if(occupied.some(o=>propOverlap({id,x,z,r},o)))return reject('prop');
   }
  }
  if(geometryTriangles+a.triangles>P.limits.triangles)return reject('geometry-budget');
  if(!a.placements.length && meshCount+a.children.length>P.limits.instancedMeshes)return reject('mesh-budget');
  if(!a.placements.length)meshCount+=a.children.length;
  geometryTriangles+=a.triangles;d.accepted++;
  a.placements.push({x,z,rotation,scale,y:kind==='coast'?P.seaY:P.groundY,r});
  if(kind!=='coast'&&kind!=='ribbon')occupied.push({id,x,z,r});
  return true;
 }
 const points=pieces.flatMap(p=>p.points),xs=points.map(p=>p[0]),zs=points.map(p=>p[1]);
 const minX=Math.min(...xs),maxX=Math.max(...xs),minZ=Math.min(...zs),maxZ=Math.max(...zs);
 // 網格只供避障搜尋；簡化控制點後以 Catmull–Rom 與弧長重新取樣。
 function clearTile(x,z,half) {
  for(let i=0;i<=6;i++)for(let j=0;j<=6;j++)if(!onLand(x-half+i*half/3,z-half+j*half/3))return false;
  return !obstacles.some(c=>Math.abs(x-c.x)<c.halfX+half+P.clearance&&Math.abs(z-c.z)<c.halfZ+half+P.clearance);
 }
 const m=P.path.module, tileRadius=m/Math.SQRT2;
 const clear=(x,z,r)=>landDisk(x,z,r)&&!obstacles.some(c=>colliderDistance(x,z,c)<r+P.clearance);
 const frontage=(name,fallback)=>{
  const b=obstacles.find(o=>o.name===name);return b?[b.x,b.z+b.halfZ+tileRadius+P.clearance]:fallback;
 };
 const entrance=frontage('ntu-cancer-center',[hospitalPoint[0],hospitalPoint[1]+3.2]);
 const towerEntry=frontage('hope-lighthouse',[towerX,towerZ+2.2]);
 const navigation=.4,nodes=new Map(),key=(i,j)=>`${i},${j}`;
 for(let i=Math.floor(minX/navigation);i<=Math.ceil(maxX/navigation);i++)for(let j=Math.floor(minZ/navigation);j<=Math.ceil(maxZ/navigation);j++) {
  const point=[i*navigation,j*navigation];
  if(clear(...point,.72))nodes.set(key(i,j),{i,j,point});
 }
 const nearest=point=>[...nodes.values()].sort((a,b)=>Math.hypot(a.point[0]-point[0],a.point[1]-point[1])-Math.hypot(b.point[0]-point[0],b.point[1]-point[1]))[0];
 const safeLine=(a,b)=>Array.from({length:Math.ceil(Math.hypot(a[0]-b[0],a[1]-b[1])/.1)+1},(_,i,)=>i).every((i,_,all)=>clear(a[0]+(b[0]-a[0])*i/(all.length-1||1),a[1]+(b[1]-a[1])*i/(all.length-1||1),.72));
 const catmull=(controls,t,tension=.25)=>{
  const q=Math.min(controls.length-1-1e-9,Math.max(0,t)*(controls.length-1)),i=Math.floor(q),u=q-i;
  const a=controls[Math.max(0,i-1)],b=controls[i],c=controls[i+1],d=controls[Math.min(controls.length-1,i+2)];
  return [0,1].map(k=>(2*u**3-3*u*u+1)*b[k]+(u**3-2*u*u+u)*(c[k]-a[k])*tension+(-2*u**3+3*u*u)*c[k]+(u**3-u*u)*(d[k]-b[k])*tension);
 };
 function arcLine(points) {
  const distances=[0];for(let i=1;i<points.length;i++)distances.push(distances[i-1]+Math.hypot(points[i][0]-points[i-1][0],points[i][1]-points[i-1][1]));
  const length=distances.at(-1);
  const at=s=>{s=Math.max(0,Math.min(length,s));let i=1;while(i<distances.length-1&&distances[i]<s)i++;
   const t=(s-distances[i-1])/(distances[i]-distances[i-1]||1);return points[i].map((v,k)=>points[i-1][k]+(v-points[i-1][k])*t);};
  const frame=s=>{const point=at(s),a=at(s-.03),b=at(s+.03),angle=Math.atan2(b[0]-a[0],b[1]-a[1]);return {point,angle,nx:Math.cos(angle),nz:-Math.sin(angle)};};
  return {length,at,frame};
 }
 const pathWarps=new Map();
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
  const raw=[];
  if(end&&previous.has(key(end.i,end.j)))for(let n=end;n;n=previous.get(key(n.i,n.j)))raw.push(n.point);
  raw.reverse();if(raw.length<2)throw new Error(`路線無法連通：${name}`);
  const controls=[raw[0]];
  for(let i=0;i<raw.length-1;) {let j=raw.length-1;while(j>i+1&&!safeLine(raw[i],raw[j]))j--;controls.push(raw[j]);i=j;}
  let sampled;
  for(const tension of [.4,.25,.1,.03]) {
   sampled=Array.from({length:601},(_,i)=>catmull(controls,i/600,tension));
   if(sampled.every(p=>clear(...p,.64)))break;
  }
  if(!sampled.every(p=>clear(...p,.64)))throw new Error(`曲線避障失敗：${name}`);
  const arc=arcLine(sampled),result={name,from,to,controls,points:sampled,connected:true,length:arc.length};paths.push(result);
  // 每段共用同一弧長函式與法線，左右邊界接續；最後一段縮短至端點。
  for(let start=0;start<arc.length;start+=m) {
   const end=Math.min(arc.length,start+m),f=arc.frame((start+end)/2),a=arc.frame(start).angle,b=arc.frame(end).angle;
   const turn=Math.abs(Math.atan2(Math.sin(b-a),Math.cos(b-a))),id=turn>.10?'path-curve':'path-straight';
   // 以實際帶寬避障；原始彎道的包圍圓不適用於沿線變形後的短段。
   if(!add(id,...f.point,f.angle,1,'ribbon'))throw new Error(`鋪面預算不足：${name}`);
   const p=byId[id].placements.at(-1);p.r=.64;p.route=name;p.start=start;p.end=end;
   pathWarps.set(p,{arc,start,end});
  }
 }
 connect('醫院入口 → 中央廣場',entrance,P.path.centralPlaza);
 connect('中央廣場 → 燈塔',P.path.centralPlaza,towerEntry);
 const plazas=[{name:'中央廣場',point:paths[0].points.at(-1)},...obstacles.filter(o=>o.name.startsWith('specialty-building-')).map(o=>({name:o.name,point:frontage(o.name)}))];
 const plazaStats=plazas.map(p=>{
  // 先驗證完整矩形；尺寸不合才整體縮小，絕不逐片排除。
  for(const [cols,rows,scale] of [[3,2,1],[2,2,1],[2,1,1],[2,2,.65],[2,1,.65],[2,2,.5],[2,1,.5],[1,1,.5]])for(const shift of [0,-.4,.4,.8,1.2,1.6])for(const lateral of [0,-.4,.4,-.8,.8,-1.2,1.2,-1.6,1.6,-2,2]) {
   const tiles=Array.from({length:cols*rows},(_,i)=>[p.point[0]+lateral+(i%cols-(cols-1)/2)*m*scale,p.point[1]+Math.floor(i/cols)*m*scale+shift]);
   if(!tiles.every(t=>clearTile(...t,.6*scale)))continue;
   tiles.forEach(t=>{if(!add('path-plaza',...t,0,scale,'path'))throw new Error('廣場鋪面預算不足');});
   return {...p,cols,rows,scale,tiles:tiles.length,centers:tiles,reason:cols<3?'整體縮小以避開障礙物':null};
  }
  throw new Error(`找不到完整廣場：${p.name}`);
 });
 for(const [i,line] of mainRoutes.entries())connect(`${i?'東':'西'}側園區步道`,line[0],line.at(-1));
 const routeArcs=paths.map(p=>arcLine(p.points));
 const candidates=[];
 function along(spacing,offset,phase=0) {
  const out=[];for(const [route,arc] of routeArcs.entries())for(let s=phase,index=0;s<arc.length;s+=spacing,index++) {
   const f=arc.frame(s),side=index%2?1:-1;
   out.push({x:f.point[0]+f.nx*offset*side,z:f.point[1]+f.nz*offset*side,rotation:f.angle,side,route,s,anchor:f.point});
  }return out;
 }
 // 先保留街道家具的位置，照明沿路每 1.8 單位交錯，不使用空地候選點。
 for(const [id,spacing,offset,phase] of [['lamp',1.8,.9,0],['bench',.6,1.1,.3],['signpost',2.4,1.1,.3]]) {
  const furnitureCandidates=along(spacing,offset,phase),length=routeArcs.reduce((n,a)=>n+a.length,0),placed=routeArcs.map(()=>0);
  const quota=routeArcs.map(a=>Math.max(1,Math.floor(P.targets[id][2]*a.length/length)));
  for(const fill of [false,true])for(const c of furnitureCandidates) {
   if(byId[id].placements.length>=P.targets[id][2])break;
   if(!fill&&placed[c.route]>=quota[c.route])continue;
   if(add(id,c.x,c.z,id==='bench'?c.rotation-c.side*Math.PI/2:c.rotation,.95)) {
    Object.assign(byId[id].placements.at(-1),{route:c.route,station:c.s,side:c.side,anchor:c.anchor});placed[c.route]++;
   }
  }
 }
 const groups=[];
 function plantGroup(id,items,minSize) {
  const a=byId[id],remaining=P.targets[id][2]-a.placements.length;
  if(remaining<minSize)return false;
  const accepted=[];
  for(const c of items) {
   const r=radius(a,c.scale);
   if(!clear(c.x,c.z,r)||routeDistance(c.x,c.z)<r+P.routeHalfWidth||[...occupied,...accepted].some(o=>propOverlap({...c,id,r},o)))continue;
   accepted.push({...c,id,r});
   if(accepted.length===Math.min(5,remaining))break;
  }
  while(remaining>accepted.length&&remaining-accepted.length<minSize)accepted.pop();
  if(accepted.length<minSize)return false;
  const group=groups.length;
  for(const c of accepted) {if(!add(id,c.x,c.z,c.rotation,c.scale))throw new Error('植栽群組預算不足');byId[id].placements.at(-1).group=group;}
  groups.push({id,group,count:accepted.length,center:[accepted[0].x,accepted[0].z]});return true;
 }
 // 先選帶狀範圍內的群組中心，再由近到遠填入 2–5 個鄰近位置。
 for(let x=minX;x<=maxX;x+=.48)for(let z=minZ;z<=maxZ;z+=.48)candidates.push([x,z]);
 const nearestFrame=(x,z)=>{
  let best={distance:Infinity};
  for(const arc of routeArcs)for(let s=0;s<=arc.length;s+=.5) {
   const f=arc.frame(s),distance=Math.hypot(x-f.point[0],z-f.point[1]);
   if(distance<best.distance)best={...f,distance};
  }return best;
 };
 const edgeDistance=(x,z,polygon)=>Math.min(...polygon.map((p,i)=>segmentDistance(x,z,p,polygon[(i+1)%polygon.length])));
 const vista=(x,z)=>[entrance,towerEntry].some(p=>z>p[1]-.5&&z<p[1]+5&&Math.abs(x-p[0])<2.6);
 const seeds=candidates.filter(p=>clear(...p,.3)).map(([x,z])=>({x,z,frame:nearestFrame(x,z),edge:Math.min(...pieces.map(p=>edgeDistance(x,z,p.points)))}));
 // 固定種子打散群組中心的順序，群組內保留緊密排列。
 for(let i=seeds.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[seeds[i],seeds[j]]=[seeds[j],seeds[i]];}
 for(const id of ['flowerbed-long','tree-round','flowerbed-round','shrub-cluster']) {
  const tree=id==='tree-round',long=id==='flowerbed-long',minSize=tree?3:2;
  for(const c of seeds) {
   if(byId[id].placements.length>=P.targets[id][2])break;
   if(tree?(c.edge>4||vista(c.x,c.z)):(c.frame.distance>(id==='shrub-cluster'?6:4.5)&&!obstacles.some(o=>o.type==='building'&&colliderDistance(c.x,c.z,o)<2.5)))continue;
   if(groups.some(g=>g.id===id&&Math.hypot(c.x-g.center[0],c.z-g.center[1])<(tree?2.7:long?2.5:id==='shrub-cluster'?1:1.9)))continue;
   const scale=id==='shrub-cluster'?.85:.9,spacing=tree?1:long?1.55:id==='flowerbed-round'?.76:.69;
   const angle=c.frame.angle,items=[];
   // 花圃長軸沿切線；樹和灌木採交錯雙列的小群，不鋪滿整片草地。
   for(const [u,v] of [[0,0],[1,0],[-1,0],[.5,1],[-.5,1],[.5,-1],[-.5,-1],[0,2],[0,-2],[1,1],[-1,-1]]) {
    const x=c.x+Math.sin(angle)*u*spacing+Math.cos(angle)*v*spacing,z=c.z+Math.cos(angle)*u*spacing-Math.sin(angle)*v*spacing;
    if(tree&&vista(x,z))continue;
    items.push({x,z,rotation:long?angle+Math.PI/2:random()*Math.PI*2,scale});
   }
   plantGroup(id,items,minSize);
  }
 }
 for(const id of ['tree-round','shrub-cluster'])for(const g of groups.filter(g=>g.id===id)) {
  if(byId[id].placements.length>=P.targets[id][2])break;
  const members=byId[id].placements.filter(p=>p.group===g.group);
  const nearby=seeds.filter(c=>(id!=='tree-round'||!vista(c.x,c.z))&&Math.hypot(c.x-g.center[0],c.z-g.center[1])<2&&members.some(p=>Math.hypot(c.x-p.x,c.z-p.z)<1.25));
  for(const c of nearby) {
   if(g.count>=5||byId[id].placements.length>=P.targets[id][2])break;
   if(add(id,c.x,c.z,c.frame.angle,id==='tree-round'?.9:.85)) {byId[id].placements.at(-1).group=g.group;g.count++;}
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
   if(coastIndex<P.targets['foam-ring'][2]) {
    add(coastIndex++%2?'rock-shore-a':'rock-shore-b',px,pz,random()*Math.PI*2,between(P.coast.scale),'coast');
    const rock=byId[coastIndex%2?'rock-shore-b':'rock-shore-a'].placements.at(-1);
    add('foam-ring',px+nx*P.coast.foamOffset,pz+nz*P.coast.foamOffset,rock.rotation,rock.scale,'coast');
   }
   next+=P.coast.spacing;
  }
  traveled+=length;
 }
 const requested=Object.fromEntries(assets.map(a=>[a.id,a.placements.length]));
 const root=new THREE.Group();root.name='props-scatter-v02-round3';
 const transform=new THREE.Object3D(),matrix=new THREE.Matrix4();
 for(const a of assets)for(const child of a.children) {
  if(!a.placements.length)continue;
  const ribbon=a.id==='path-straight'||a.id==='path-curve';
  let geometry=child.geometry;
  if(ribbon) {
   const warped=a.placements.map(p=>{
    const {arc,start,end}=pathWarps.get(p),g=child.geometry.clone(),position=g.attributes.position;
    for(let i=0;i<position.count;i++) {
     const x=position.getX(i),z=position.getZ(i);
     const u=a.id==='path-curve'?Math.atan2(z+1.2,x+1.2)/(Math.PI/2):(z+.6)/1.2;
     const offset=a.id==='path-curve'?1.8-Math.hypot(x+1.2,z+1.2):x;
     const f=arc.frame(start+Math.max(0,Math.min(1,u))*(end-start));
     position.setXYZ(i,f.point[0]+f.nx*offset,position.getY(i)+P.groundY,f.point[1]+f.nz*offset);
    }
    g.computeVertexNormals();return g;
   });
   geometry=mergeGeometries(warped,false);warped.forEach(g=>g.dispose());
  }
  const instanced=new THREE.InstancedMesh(geometry,child.material,ribbon?1:a.placements.length);
  instanced.name=`props-${a.id}-${a.meshes.length}`;
  instanced.castShadow=!a.id.startsWith('path-')&&a.id!=='foam-ring';instanced.receiveShadow=true;
  (ribbon?[{x:0,y:0,z:0,rotation:0,scale:1}]:a.placements).forEach((p,i)=>{
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
  return Object.fromEntries(assets.map(a=>[a.id,{requested:requested[a.id],instances:a.placements.length,
   trianglesPerInstance:a.triangles,triangles:a.triangles*a.placements.length,
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
  report:shots=>({version:'v02-round3',seed:P.seed,quality:window.__lookdev.quality,params:P,
   countMethod:'instances counts logical asset placements. Curved paving is vertex-warped and merged per material into one identity InstancedMesh; decor remains instanced. Budget counts actual geometry triangles and InstancedMesh objects; renderer.info includes all render passes.',
   assets:inventory(),totalGeometryTriangles:budget().triangles,totalInstancedMeshes:budget().instancedMeshes,
   candidateGridPoints:nodes.size,diagnostics,obstacles,paths,plazas:plazaStats,groups,
   placements:Object.fromEntries(assets.map(a=>[a.id,a.placements])),reductions,shots})};
 assertBudget();
 window.__captureProps=true;
 console.table(inventory());
}

// Players, route search and local avoidance share the same terrain/collider predicate.
export function buildWalkGrid({pieces,allowed,spawn,step=.4}){
 const points=pieces.flatMap(p=>p.points),minX=Math.min(...points.map(p=>p[0]))-1,minZ=Math.min(...points.map(p=>p[1]))-1;
 const width=Math.ceil((Math.max(...points.map(p=>p[0]))-minX+1)/step),height=Math.ceil((Math.max(...points.map(p=>p[1]))-minZ+1)/step),size=width*height;
 const positions=Array.from({length:size},(_,k)=>[minX+k%width*step,minZ+Math.floor(k/width)*step]);
 const valid=new Uint8Array(size),directions=[[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]],edges=new Int32Array(size*8).fill(-1);
 const point=k=>positions[k];
 const navigable=(x,z)=>allowed(x,z,.7)&&[[.07,0],[-.07,0],[0,.07],[0,-.07]].every(([dx,dz])=>allowed(x+dx,z+dz,.7));
 function segment(a,b,blocked=null,terrainCheck=true,clearance=false){
  const n=Math.max(1,Math.ceil(Math.hypot(a[0]-b[0],a[1]-b[1])/.08));
  for(let i=1;i<=n;i++){const x=a[0]+(b[0]-a[0])*i/n,z=a[1]+(b[1]-a[1])*i/n;if((terrainCheck&&!(clearance?navigable(x,z):allowed(x,z,.7)))||blocked?.(x,z))return false;}
  return true;
 }
 for(let k=0;k<size;k++)valid[k]=navigable(...point(k))?1:0;
 for(let k=0;k<size;k++)if(valid[k]){
  const x=k%width,z=Math.floor(k/width);
  directions.forEach(([dx,dz],slot)=>{const nx=x+dx,nz=z+dz,n=nz*width+nx;if(nx>=0&&nx<width&&nz>=0&&nz<height&&valid[n]&&segment(point(k),point(n),null,true,true))edges[k*8+slot]=n;});
 }
 const candidates=Array.from({length:size},(_,k)=>k).filter(k=>valid[k]);
 function closest(list,x,z,predicate){
  const squared=k=>(point(k)[0]-x)**2+(point(k)[1]-z)**2;
  let best=-1,distance=Infinity;for(const k of list){const d=squared(k);if(d<distance){best=k;distance=d;}}
  if(!predicate||best<0||predicate(...point(best)))return best;
  // Check nearby cells first; never trace long segments across the whole island to find a start.
  return list.map(k=>({k,d:squared(k)})).sort((a,b)=>a.d-b.d).find(({k})=>predicate(...point(k)))?.k??-1;
 }
 const start=closest(candidates,...spawn);if(start<0)throw new Error('No walkable starting point.');
 const connected=new Uint8Array(size),nodes=[start];connected[start]=1;
 for(let i=0;i<nodes.length;i++)for(let j=0;j<8;j++){const n=edges[nodes[i]*8+j];if(n>=0&&!connected[n]){connected[n]=1;nodes.push(n);}}
 // Nearest must stay in the spawn component, even if an isolated valid cell is closer.
 const nearest=(x,z,predicate=null)=>closest(nodes,x,z,predicate);
 function route(from,to,{blocked=null}={}){
  if(!connected[from]||!connected[to]||blocked?.(...point(to)))return [];
  const blockedCells=blocked?new Uint8Array(size):null;
  if(blocked)for(const k of nodes)blockedCells[k]=blocked(...point(k))?1:0;
  const parent=new Int32Array(size).fill(-1),queue=[from];parent[from]=from;
  for(let i=0;i<queue.length&&parent[to]===-1;i++)for(let j=0;j<8;j++){
   const current=queue[i],n=edges[current*8+j];
   if(n<0||parent[n]!==-1||blockedCells?.[n])continue;
   if(blocked&&!segment(point(current),point(n),blocked,false))continue;
   parent[n]=current;queue.push(n);
  }
  if(parent[to]===-1)return [];
  const path=[to];while(path.at(-1)!==from)path.push(parent[path.at(-1)]);path.reverse();
  const simplified=[path[0]];
  for(let i=0;i<path.length-1;){let j=Math.min(i+12,path.length-1);while(j>i+1&&!segment(point(path[i]),point(path[j]),blocked,true,true))j--;simplified.push(path[j]);i=j;}
  return simplified;
 }
 return {point,nearest,route,segment,clearSegment:(a,b,blocked)=>segment(a,b,blocked,true,true),nodes,connected,step};
}

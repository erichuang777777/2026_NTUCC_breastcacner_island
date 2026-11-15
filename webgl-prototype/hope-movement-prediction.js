// Use the same walk grid, speed and substeps as the authoritative server.
export function gridAllows(data){const cells=new Set(data.walkable);return (x,z)=>{const ix=Math.floor((x-data.origin[0])/data.step),iz=Math.floor((z-data.origin[1])/data.step);return ix>=0&&ix<data.width&&iz>=0&&iz<data.height&&cells.has(iz*data.width+ix);};}
export function movePredicted(p,input,seconds,allowed,others=[]){
 let {x,z}=p;let {dx,dz}=input;const length=Math.hypot(dx,dz);if(length>1){dx/=length;dz/=length;}
 const distance=2*Math.max(0,Math.min(.25,seconds)),steps=Math.max(1,Math.ceil(distance/.06));
 const free=(x,z)=>allowed(x,z)&&others.every(o=>Math.hypot(x-o.x,z-o.z)>=.58);
 for(let i=0;i<steps;i++){const sx=dx*distance/steps,sz=dz*distance/steps;if(free(x+sx,z+sz)){x+=sx;z+=sz;}else if(free(x+sx,z)){x+=sx;}else if(free(x,z+sz)){z+=sz;}}
 return {...p,x,z};
}
export function createMovementPredictor({allowed,others=()=>[],now=()=>performance.now()}){
 let anchor=null,anchorTime=0,visual=null,history=[{time:0,dx:0,dz:0}],offset={x:0,z:0},lastFrame=now();
 function predicted(time){
  if(!anchor)return null;let p={...anchor},cursor=anchorTime,input=history[0],end=Math.min(time,anchorTime+250);
  for(const entry of history){if(entry.time<=cursor){input=entry;continue;}if(entry.time>end)break;p=movePredicted(p,input,(entry.time-cursor)/1000,allowed,others());cursor=entry.time;input=entry;}
  if(end>cursor)p=movePredicted(p,input,(end-cursor)/1000,allowed,others());return p;
 }
 function input(dx,dz){const time=now(),previous=history.at(-1);if(previous.dx===dx&&previous.dz===dz)return;
  // An idle heartbeat may be old; start prediction immediately at the stationary point.
  if(anchor&&previous.dx===0&&previous.dz===0&&time-anchorTime>250){anchor={...visual};anchorTime=time;history=[{time,dx:0,dz:0}];}
  history.push({time,dx,dz});if(history.length>120)history.splice(0,history.length-120);
 }
 function acknowledge(position,sentAt=now()){
  if(anchor&&position.sequence<anchor.sequence)return;
  anchor={...position};anchorTime=sentAt;
  const prior=history.filter(e=>e.time<=sentAt).at(-1)||{time:sentAt,dx:0,dz:0};history=[prior,...history.filter(e=>e.time>sentAt)];
  const target=predicted(now());offset=visual&&Math.hypot(visual.x-target.x,visual.z-target.z)<1?{x:visual.x-target.x,z:visual.z-target.z}:{x:0,z:0};if(!visual)visual=target;
 }
 function sample(){const time=now(),dt=Math.max(0,(time-lastFrame)/1000);lastFrame=time;const target=predicted(time);if(!target)return null;const decay=Math.exp(-28*dt);offset.x*=decay;offset.z*=decay;
  const next={...target,x:target.x+offset.x,z:target.z+offset.z};visual=allowed(next.x,next.z)&&others().every(o=>Math.hypot(next.x-o.x,next.z-o.z)>=.58)?next:target;return {...visual};
 }
 return {input,acknowledge,sample};
}

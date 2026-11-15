import {movePredicted} from './hope-movement-prediction.js?v=24';
import {buildWalkGrid} from './hope-navigation.js?v=19';
import {pieces,insidePolygon,routeClearance} from './taiwan-layout.js?v=15';

const SEPARATION=.56,SLOT_SPACING=1.12;
export function createCrowd({scene,allowed,spawn,makeCharacter,getPlayer,stations=[],onStationEvent=()=>{},terrain=pieces,circulation=routeClearance}){
 const grid=buildWalkGrid({pieces:terrain,allowed,spawn}),actors=[];
 const destinations=terrain.map(p=>grid.nodes.filter(k=>insidePolygon(...grid.point(k),p.points)));
 if(destinations.some(a=>!a.length)||!stations.length)throw new Error('Crowd navigation needs reachable islands and stations.');
 const gap=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
 let seed=72351,moving=0,arrivals=0,distance=0,reroutes=0,yields=0,conversations=0;
 const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 // Stop in open frontage, not at one doorway or on the reserved circulation line.
 const stationSlots=stations.map((station,i)=>{
  const radius=Math.max(1.5,station.scale*1.8),candidates=grid.nodes.filter(k=>{
   const p=grid.point(k),d=gap(p,station.point);
   return d>=radius&&d<radius+4.5&&Array.from({length:8},(_,j)=>j*Math.PI/4).every(a=>allowed(p[0]+Math.cos(a)*.8,p[1]+Math.sin(a)*.8,.7));
  });
  candidates.sort((a,b)=>{const score=k=>gap(grid.point(k),station.point)+(insidePolygon(...grid.point(k),terrain[i].points)?0:2)+(circulation(...grid.point(k))<.8?3:0);return score(a)-score(b);});
  const slots=[];for(const k of candidates)if(slots.every(s=>gap(grid.point(s),grid.point(k))>=SLOT_SPACING)){slots.push(k);if(slots.length===8)break;}
  if(!slots.length)throw new Error('No open visitor space for '+station.name);
  return slots;
 });
 function obstacle(actor){
  const player=getPlayer(),others=actors.filter(b=>b!==actor).map(b=>[b.x,b.z]);
  if(player)others.push([player.x,player.z]);
  return (x,z)=>others.some(p=>Math.hypot(p[0]-x,p[1]-z)<SEPARATION);
 }
 function available(actor,k){
  const p=grid.point(k);
  return !obstacle(actor)(...p)&&actors.every(b=>b===actor||b.goal===null||gap(p,grid.point(b.goal))>=SLOT_SPACING);
 }
 function pathTo(actor,to,dynamic=true){
  const blocked=dynamic?obstacle(actor):null,origin=[actor.x,actor.z];
  const from=grid.nearest(...origin,(x,z)=>grid.segment(origin,[x,z],blocked));
  return from<0?[]:grid.route(from,to,{blocked});
 }
 function follow(actor,path,purpose='station'){
  actor.path=path;actor.cursor=0;actor.purpose=purpose;actor.blocked=0;if(purpose==='station'||purpose==='depart')actor.destinationPurpose=purpose;
 }
 function plan(actor){
  actor.goal=null;actor.activityStarted=false;actor.wait=0;actor.tripTime=0;actor.reassignedAt=actor.stall;
  for(let offset=0;offset<stations.length;offset++){
   const index=(actor.nextStation+offset)%stations.length;
   const slots=stationSlots[index].filter(k=>available(actor,k));
   slots.sort((a,b)=>gap([actor.x,actor.z],grid.point(a))-gap([actor.x,actor.z],grid.point(b)));
   for(const to of slots){
    // Static initial routes are cheap; local occupancy is handled before each move.
    const path=pathTo(actor,to,false);if(!path.length)continue;
    actor.goal=to;actor.station=index;follow(actor,path);actor.retry=0;return true;
   }
  }
  follow(actor,[]);actor.retry=1+random();return false;
 }
 function reroute(actor){
  reroutes++;const path=pathTo(actor,actor.goal);
  if(path.length){follow(actor,path,actor.destinationPurpose);return;}
  // A persistent retreat lets an opposing resident pass in a narrow opening.
  const blocker=actors.filter(b=>b!==actor).sort((a,b)=>Math.hypot(a.x-actor.x,a.z-actor.z)-Math.hypot(b.x-actor.x,b.z-actor.z))[0];
  const blocked=obstacle(actor);
  const options=grid.nodes.filter(k=>{const p=grid.point(k),d=gap(p,[actor.x,actor.z]);return d>.65&&d<2.8&&available(actor,k)&&grid.clearSegment([actor.x,actor.z],p,blocked);});
  options.sort((a,b)=>{
   const score=k=>{const p=grid.point(k);return (blocker?-gap(p,[blocker.x,blocker.z]):0)+gap(p,[actor.x,actor.z])*.25;};return score(a)-score(b);
  });
  if(options.length){follow(actor,[options[0]],'yield');yields++;return;}
  actor.retry=.8+random()*.6;
 }
 function depart(actor){
  actor.goal=null;actor.activityStarted=false;actor.tripTime=0;actor.reassignedAt=actor.stall;
  const options=grid.nodes.filter(k=>{const p=grid.point(k),d=gap(p,[actor.x,actor.z]);return d>1.8&&d<4.5&&available(actor,k)&&stationSlots.every(slots=>slots.every(s=>gap(p,grid.point(s))>1.2));});
  options.sort((a,b)=>gap(grid.point(a),[actor.x,actor.z])-gap(grid.point(b),[actor.x,actor.z]));
  for(const k of options.slice(0,12)){const path=pathTo(actor,k);if(path.length){actor.goal=k;follow(actor,path,'depart');return;}}
  plan(actor);
 }
 function setCount(count){
  count=Math.max(6,Math.min(12,Math.round(Number(count)||8)));
  while(actors.length>count)actors.pop().avatar.dispose();
  while(actors.length<count){
   const free=grid.nodes.filter(k=>!obstacle(null)(...grid.point(k))&&actors.every(a=>gap(grid.point(k),[a.x,a.z])>=.9));
   if(!free.length)break;const p=grid.point(free[Math.floor(random()*free.length)]);
   const id=actors.length,actor={id,role:id%6,x:p[0],z:p[1],heading:random()*6.28,speed:.75+random()*.35,wait:0,blocked:0,stall:0,tripTime:0,retry:0,travelled:0,completed:0,path:[],cursor:0,walking:false,frameDistance:0,nextStation:id%stations.length,goal:null,activityStarted:false};
   actor.avatar=makeCharacter(actor.role);scene.add(actor.avatar.person);actors.push(actor);plan(actor);
  }draw(0);
 }
 function draw(dt){
  for(const a of actors){const person=a.avatar.person;person.position.set(a.x,.7,a.z);
   const turn=Math.atan2(Math.sin(a.heading-person.rotation.y),Math.cos(a.heading-person.rotation.y));person.rotation.y+=turn*Math.min(1,dt*9);
   a.avatar.update(dt,a.frameDistance/Math.max(dt,.001),a.socialTimer>0?a.socialAction:a.activityStarted?(a.wait<3&&a.id%3===0?'stretch':'reading'):'idle',a.id*.63);
  }
 }
 function update(dt,t,render=true){
  // Bound the integration step even after a background tab resumes.
  dt=Math.min(.1,Math.max(0,dt));moving=0;
  for(const a of actors){
   a.frameDistance=0;a.walking=false;
   if(a.remote){
    const before=[a.x,a.z];a.remoteAge=(a.remoteAge||0)+dt;
    const input={dx:a.remote.dx||0,dz:a.remote.dz||0},target=movePredicted(a.remote,input,Math.min(.12,a.remoteAge),(x,z)=>allowed(x,z,.7),actors.filter(b=>b!==a&&b.remote).map(b=>b.remote));
    const alpha=input.dx===0&&input.dz===0?1:1-Math.exp(-40*dt);a.x+=(target.x-a.x)*alpha;a.z+=(target.z-a.z)*alpha;a.heading=a.remote.heading;
    a.frameDistance=gap(before,[a.x,a.z]);a.walking=a.frameDistance>.001;if(a.walking)moving++;a.stall=0;continue;
   }
   a.socialCooldown=Math.max(0,(a.socialCooldown||0)-dt);
   if(a.socialTimer>0){a.socialTimer-=dt;continue;}
   if(a.activityStarted){
    if(!a.socialCooldown&&a.wait>5){
     const partner=actors.find(b=>b!==a&&b.activityStarted&&!b.socialTimer&&!b.socialCooldown&&Math.hypot(a.x-b.x,a.z-b.z)>1.12&&Math.hypot(a.x-b.x,a.z-b.z)<2.35);
     if(partner){a.socialTimer=partner.socialTimer=4.2;a.socialCooldown=partner.socialCooldown=75;a.socialAction='talk';partner.socialAction='nod';a.heading=Math.atan2(partner.x-a.x,partner.z-a.z);partner.heading=a.heading+Math.PI;conversations++;onStationEvent({type:'conversation',resident:a.id,station:a.station,simMinute:Math.floor(t*.25)});continue;}
    }
    a.wait-=dt;if(a.wait>0)continue;
    onStationEvent({type:'completed',resident:a.id,station:a.station,simMinute:Math.floor(t*.25)});
    arrivals++;a.completed++;a.nextStation=(a.station+[1,3,7,9][a.id%4])%stations.length;depart(a);continue;
   }
   a.stall+=dt;a.tripTime+=dt;a.retry=Math.max(0,a.retry-dt);
   if(a.goal===null){if(!a.retry)plan(a);continue;}
   // Don't spend forever pursuing one occupied approach. Keep the reservation until reassigned.
   if(a.tripTime>120||a.stall-a.reassignedAt>12){a.nextStation=(a.station+1)%stations.length;plan(a);continue;}
   while(a.cursor<a.path.length&&gap([a.x,a.z],grid.point(a.path[a.cursor]))<.025)a.cursor++;
   if(a.cursor>=a.path.length){
    if(a.purpose==='depart'){a.goal=null;a.retry=.5+random();a.path=[];a.purpose='station';continue;}
    if(a.purpose==='yield'){if(!a.retry){a.retry=.7+random();follow(a,[],'resume');}continue;}
    if(a.purpose==='resume'||!a.path.length){if(!a.retry)reroute(a);continue;}
    if(gap([a.x,a.z],grid.point(a.goal))>.08){if(!a.retry)reroute(a);continue;}
    a.activityStarted=true;a.wait=12+a.id%4*3;a.stall=0;
    const station=stations[a.station];a.heading=Math.atan2(station.point[0]-a.x,station.point[1]-a.z);
    onStationEvent({type:'arrived',resident:a.id,station:a.station,simMinute:Math.floor(t*.25)});continue;
   }
   const target=grid.point(a.path[a.cursor]),dx=target[0]-a.x,dz=target[1]-a.z,len=Math.hypot(dx,dz),travel=Math.min(len,a.speed*dt);
   const nx=a.x+dx/len*travel,nz=a.z+dz/len*travel,blocked=obstacle(a);
   if(grid.segment([a.x,a.z],[nx,nz],blocked)){
    a.frameDistance=travel;a.x=nx;a.z=nz;a.heading=Math.atan2(dx,dz);a.walking=true;a.blocked=0;a.stall=0;a.travelled+=travel;moving++;distance+=travel;
   }else{
    a.blocked+=dt;
    if(a.blocked>.65+a.id*.035&&!a.retry){a.retry=1.1+random()*.5;reroute(a);}
   }
  }
  if(render)draw(dt);
 }
 function setGuests(profiles){
  for(let i=0;i<actors.length;i++){
   const a=actors[i],guest=profiles[i],signature=guest?JSON.stringify({...guest,position:undefined}):'';
   const wasRemote=!!a.remote,samePerson=a.guestId===guest?.id;if(a.remote?.sequence!==guest?.position?.sequence||!samePerson)a.remoteAge=0;a.remote=guest?.position||null;a.guestId=guest?.id;
   if(a.remote){a.goal=null;a.path=[];a.activityStarted=false;a.socialTimer=0;if(!wasRemote||!samePerson){a.x=a.remote.x;a.z=a.remote.z;}}
   else if(wasRemote){a.goal=null;a.retry=0;a.purpose='station';}
   if(a.guestSignature===signature)continue;
   if(!guest&&!a.guestSignature){a.guestSignature='';continue;}
   const role=guest?Math.max(0,['visitor','scarf','doctor','nurse','surgeon','scrub'].indexOf(guest.role)):a.role;
   a.avatar.dispose();a.avatar=makeCharacter(role,guest?.appearance||{}, {film:guest?.kind==='film'});scene.add(a.avatar.person);a.guestSignature=signature;a.guestName=guest?.displayName||'';a.guestKind=guest?.kind==='film'?'film':guest?'participant':null;
   if(guest?.completed)a.avatar.wave?.();
  }
  draw(0);
 }
 function greet(){const p=getPlayer();for(const a of actors)if(a.activityStarted&&Math.hypot(a.x-p.x,a.z-p.z)<3){a.heading=Math.atan2(p.x-a.x,p.z-a.z);a.avatar.wave?.();}}
 const audit=()=>({count:actors.length,moving,arrivals,distance:Math.round(distance*10)/10,invalid:actors.filter(a=>!allowed(a.x,a.z,.7)).length,reachableIslands:destinations.filter(a=>a.length).length,sharedRig:true,conversations,guests:actors.filter(a=>a.guestKind==='participant').length,controlled:actors.filter(a=>a.remote).length,filmCast:actors.filter(a=>a.guestKind==='film').length,reading:actors.filter(a=>a.activityStarted).length,longestStall:+Math.max(0,...actors.map(a=>a.stall)).toFixed(2),stationSlots:stationSlots.map(s=>s.length),reserved:actors.filter(a=>a.goal!==null).length,reroutes,yields,overlaps:actors.reduce((n,a,i)=>n+actors.slice(i+1).filter(b=>Math.hypot(a.x-b.x,a.z-b.z)<SEPARATION-.001).length,0)});
 setCount(8);
 return {update,setCount,setGuests,greet,audit,grid,samples:()=>actors.map(a=>({id:a.id,name:a.guestName||null,kind:a.guestKind||'resident',controlled:!!a.remote,target:a.remote?{...a.remote}:null,x:a.x,z:a.z,heading:a.heading,travelled:a.travelled,completed:a.completed,stall:a.stall,station:a.station,goal:a.goal===null?null:grid.point(a.goal),state:a.activityStarted?'reading':a.purpose,avatar:a.avatar.audit()}))};
}

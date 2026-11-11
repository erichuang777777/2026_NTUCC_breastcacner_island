import test from 'node:test';
import assert from 'node:assert/strict';
import {createCrowd} from './hope-crowd.js';
import {buildWalkGrid} from './hope-navigation.js';
const terrain=[{points:[[-7,-7],[7,-7],[7,7],[-7,7]]}];
const avatar=()=>({person:{position:{set(){}},rotation:{y:0}},update(){},dispose(){},audit(){return {};}});
test('12 residents share a station without sharing its occupied stopping points',()=>{
 let player={x:40,z:40},crowd;const visits=new Set();
 const events=[],lastCompletion=new Map();let simTime=0;
 const allowed=(x,z)=>Math.abs(x)<6.8&&Math.abs(z)<6.8&&!(Math.abs(x)<1.2&&Math.abs(z)<1.2);
 crowd=createCrowd({scene:{add(){}},allowed,terrain,circulation:()=>2,spawn:[-5,-5],makeCharacter:avatar,getPlayer:()=>player,stations:[{name:'測試站',point:[0,0],scale:1}],onStationEvent:e=>{
  const a=crowd.samples().find(a=>a.id===e.resident);
  assert.ok(Math.hypot(a.x-a.goal[0],a.z-a.goal[1])<.08,'must physically reach reserved position');
  if(e.type==='completed'){visits.add(e.resident);lastCompletion.set(e.resident,simTime);}events.push(e);
 }});
 crowd.setCount(12);
 // The player occupies one requested destination throughout the first minute.
 const goal=crowd.samples()[0].goal;player={x:goal[0],z:goal[1]};
 for(let i=0;i<3600;i++){
  simTime=i*.1;if(i===600)player={x:40,z:40};crowd.update(.1,i*.1,false);
  if(i%10===0){const audit=crowd.audit();assert.equal(audit.invalid,0);assert.equal(audit.overlaps,0);
   const goals=crowd.samples().filter(a=>a.goal);for(let j=0;j<goals.length;j++)for(let k=j+1;k<goals.length;k++)assert.ok(Math.hypot(goals[j].goal[0]-goals[k].goal[0],goals[j].goal[1]-goals[k].goal[1])>=1.119);
  }
 }
 assert.equal(visits.size,12,'every resident must complete a visit, not just keep moving');
 assert.ok(events.length>40);
 for(const completedAt of lastCompletion.values())assert.ok(simTime-completedAt<90,'no resident starves while the station is at capacity');
 assert.ok(crowd.samples().filter(a=>a.goal).every(a=>a.stall<30),'travelling residents must recover from obstructions');
 console.log('single-station stress:',crowd.audit());
});
test('navigation detours around a dynamic obstruction and excludes isolated cells',()=>{
 const allowed=(x,z)=>Math.abs(x)<6.8&&Math.abs(z)<6.8&&!(x>3&&x<4);
 const grid=buildWalkGrid({pieces:terrain,allowed,spawn:[-5,0]});
 assert.ok(grid.point(grid.nearest(6,0))[0]<3);
 const blocked=(x,z)=>Math.hypot(x,z)<1;
 const path=grid.route(grid.nearest(-3,0),grid.nearest(2,0),{blocked});
 assert.ok(path.length>2);
 for(let i=1;i<path.length;i++)assert.ok(grid.segment(grid.point(path[i-1]),grid.point(path[i]),blocked));
 assert.deepEqual(grid.route(grid.nearest(-3,0),grid.nearest(0,0),{blocked}),[]);
});

test('smoothed routes leave space around curved obstacles rather than grazing their collider',()=>{
 const allowed=(x,z)=>Math.abs(x)<6.8&&Math.abs(z)<6.8&&Math.hypot(x-.13,z+.19)>.7;
 const grid=buildWalkGrid({pieces:terrain,allowed,spawn:[-5,-5]});
 for(const [start,end] of [[[-4,-1],[4,1]],[[-3,0],[3,0]],[[-1,-3],[1,3]]]){
  const path=grid.route(grid.nearest(...start),grid.nearest(...end));assert.ok(path.length);
  for(let j=1;j<path.length;j++){
   const a=grid.point(path[j-1]),b=grid.point(path[j]);
   for(let i=0;i<=1000;i++)assert.ok(allowed(a[0]+(b[0]-a[0])*i/1000,a[1]+(b[1]-a[1])*i/1000));
  }
 }
});

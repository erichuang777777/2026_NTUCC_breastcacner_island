import test from 'node:test';
import assert from 'node:assert/strict';
import {createControlPump} from './hope-control-pump.js';
test('release during in-flight request sends zero next, without replaying old pointer directions',async()=>{
 let value=1,resolve,time=0,id=0;const jobs=new Map(),sent=[];
 const pump=createControlPump({now:()=>time,schedule:(f,ms)=>{jobs.set(++id,{f,ms});return id;},cancel:id=>jobs.delete(id),send:()=>{sent.push(value);return new Promise(r=>resolve=r);}});
 const tick=()=>{const [key,job]=jobs.entries().next().value;jobs.delete(key);time+=job.ms;job.f();};
 pump.request();tick();assert.deepEqual(sent,[1]);
 value=2;pump.request();value=3;pump.request();value=0;pump.request(true);
 assert.equal(jobs.size,0,'must not send concurrently');resolve();await Promise.resolve();
 assert.equal([...jobs.values()][0].ms,0,'stop has priority over rate limit');tick();assert.deepEqual(sent,[1,0]);resolve();await Promise.resolve();assert.equal(jobs.size,0);
});
test('pointer storms coalesce and are rate limited',async()=>{
 let time=0,id=0,value=1;const jobs=new Map(),sent=[];
 const pump=createControlPump({now:()=>time,schedule:(f,ms)=>{jobs.set(++id,{f,ms});return id;},cancel:id=>jobs.delete(id),send:async()=>sent.push(value)});
 const tick=()=>{const [key,job]=jobs.entries().next().value;jobs.delete(key);time+=job.ms;job.f();};
 pump.request();tick();await Promise.resolve();
 for(let i=0;i<100;i++){value=i;pump.request();}assert.equal(jobs.size,1);assert.equal([...jobs.values()][0].ms,60);tick();await Promise.resolve();assert.deepEqual(sent,[1,99]);
});

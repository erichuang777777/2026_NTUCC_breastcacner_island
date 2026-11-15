import test from 'node:test';
import assert from 'node:assert/strict';
import {DAY_CYCLE_MS,sampleDayCycle,phaseOffset} from './hope-day-cycle.js';
test('ten-minute cycle includes day, sunset, night and sunrise, then repeats',()=>{
 assert.equal(DAY_CYCLE_MS,600000);
 assert.equal(sampleDayCycle(0).daylight,1);assert.equal(sampleDayCycle(300000).daylight,0);
 assert.ok(Math.abs(sampleDayCycle(150000).twilight-1)<1e-12);assert.ok(Math.abs(sampleDayCycle(450000).twilight-1)<1e-12);
 for(const t of [0,150000,300000,450000])assert.deepEqual(sampleDayCycle(t),sampleDayCycle(t+DAY_CYCLE_MS));
 for(let t=0;t<DAY_CYCLE_MS;t+=1000)assert.ok(Math.abs(sampleDayCycle(t).daylight-sampleDayCycle(t+1000).daylight)<.04,'lighting cannot jump at transitions');
});
test('manual preview continues automatically and wall clock catches up after backgrounding',()=>{
 const now=1794470000000,offset=phaseOffset(now,true);
 assert.equal(sampleDayCycle(now,offset).daylight,0);
 assert.equal(sampleDayCycle(now+300000,offset).daylight,1);
 assert.equal(sampleDayCycle(now+1800000,offset).daylight,0);
 assert.equal(sampleDayCycle(now,phaseOffset(now,false)).daylight,1);
});

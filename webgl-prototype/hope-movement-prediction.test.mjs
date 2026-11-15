import test from 'node:test';
import assert from 'node:assert/strict';
import {createMovementPredictor,movePredicted,gridAllows} from './hope-movement-prediction.js';
test('input moves before a delayed acknowledgement, stops, and never predicts indefinitely',()=>{
 let t=0;const predictor=createMovementPredictor({allowed:()=>true,now:()=>t});predictor.acknowledge({x:0,z:0,sequence:0},0);
 t=1000;predictor.input(1,0);t=1016;assert.ok(predictor.sample().x>.02,'first frame responds without a network reply');
 t=1200;const before=predictor.sample().x;assert.ok(before>.3);
 t=2000;const capped=predictor.sample();assert.ok(capped.x<=.500001);
 predictor.input(0,0);t=3000;assert.equal(predictor.sample().x,capped.x);
 predictor.acknowledge({x:.2,z:0,sequence:3},t);t+=500;assert.ok(Math.abs(predictor.sample().x-.2)<1e-4);
 predictor.acknowledge({x:99,z:99,sequence:2},t);assert.ok(predictor.sample().x<1,'old replies cannot rewind the sequence');
});
test('prediction uses collision substeps and respects other players',()=>{
 const allowed=(x,z)=>x<.3&&z<2;
 const p=movePredicted({x:0,z:0},{dx:1,dz:1},.25,allowed);assert.ok(p.x<.3&&p.z>p.x,'slide along obstacle');
 const q=movePredicted({x:0,z:0},{dx:1,dz:0},.25,()=>true,[{x:.7,z:0}]);assert.ok(q.x<=.12);
 const grid=gridAllows({origin:[0,0],step:1,width:2,height:1,walkable:[0]});assert.equal(grid(.5,.5),true);assert.equal(grid(1.5,.5),false);assert.equal(grid(-.1,.5),false);
});

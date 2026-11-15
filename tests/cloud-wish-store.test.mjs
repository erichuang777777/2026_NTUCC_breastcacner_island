import test from 'node:test';
import assert from 'node:assert/strict';
import {createCloudWishStore} from '../webgl-prototype/hope-wish-cloud.js';
const storage={getItem:()=>null,setItem:()=>{throw Error('Cloud must not silently use local storage');}};
const response=(data,status=200)=>Response.json(data,{status});
test('failed cloud saves never create a local wish; retry recovers cloud state',async()=>{
 let fail=true;const store=createCloudWishStore(storage,{fetcher:async(_url,options)=>{if(fail)throw Error('offline');return response(options.method==='GET'?{wishes:[]}:{id:'wish-1'});}});
 await assert.rejects(store.add('希望',0,'wish-1'),/offline/);assert.equal(store.wishes.length,0);assert.equal(store.persistent,false);
 fail=false;await store.add('希望',0,'wish-1');await store.add('希望',0,'wish-1');assert.equal(store.wishes.length,1);assert.equal(store.mode,'cloud');assert.equal(store.persistent,true);
});
test('remote completion runs once and another visitor cannot complete a wish',async()=>{
 let status='lit',completed=[];const store=createCloudWishStore(storage,{fetcher:async()=>response({wishes:[{id:'remote',status,canEdit:false}]}),onCompleted:id=>completed.push(id)});
 await new Promise(resolve=>setTimeout(resolve,0));assert.equal(await store.complete('remote'),false);
 status='completed';await store.refresh();await store.refresh();assert.deepEqual(completed,['remote']);
});

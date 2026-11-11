import assert from 'node:assert/strict';
import {pieces,joins,onLand,insidePolygon,mapPoint,WORLD_SCALE,coastline} from './taiwan-layout.js';

assert.equal(pieces.length,10);
assert.equal(joins.length,23);
assert.equal(onLand(30,0),false);
assert.equal(WORLD_SCALE,2.4);
assert(joins.filter(j=>j.r>=2).length>=20);
for(const piece of pieces){
 assert(piece.points.every(p=>p.every(Number.isFinite)));
 assert(insidePolygon(...piece.center,piece.points));
}
// Flood the actual land footprint, not merely the declared connection graph.
const step=.24,minX=Math.min(...coastline.map(p=>p[0]))-1,minZ=Math.min(...coastline.map(p=>p[1]))-1,width=Math.ceil((Math.max(...coastline.map(p=>p[0]))-minX+1)/step),depth=Math.ceil((Math.max(...coastline.map(p=>p[1]))-minZ+1)/step),visited=new Set(),queue=[];
const [sx,sz]=mapPoint(.2,.54);
queue.push([Math.round((sx-minX)/step),Math.round((sz-minZ)/step)]);
const reached=new Set();
for(let i=0;i<queue.length;i++){
 const [ix,iz]=queue[i],key=iz*width+ix;
 if(ix<0||ix>=width||iz<0||iz>=depth||visited.has(key))continue;
 visited.add(key);const x=minX+ix*step,z=minZ+iz*step;if(!onLand(x,z))continue;
 for(const p of pieces)if(insidePolygon(x,z,p.points))reached.add(p.id);
 queue.push([ix-1,iz],[ix+1,iz],[ix,iz-1],[ix,iz+1]);
}
assert.equal(reached.size,10,'All ten pieces must be reachable across shared shores.');
console.log('PASS: enlarged Taiwan, ten finite island polygons, 23 shore joins and connected land.');

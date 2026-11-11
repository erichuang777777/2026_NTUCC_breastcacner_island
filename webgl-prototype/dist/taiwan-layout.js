// Stylized Taiwan silhouette, north at negative Z. Shared curved cuts form ten pieces.
import {shores,modelPieces,divisionLevels,coastline as sourceCoastline} from './taiwan-coastline.js?v=15';
export const WORLD_SCALE=2.4;
export const SHORE_JOIN_RADIUS=2.4;
export const coastline=sourceCoastline.map(p=>p.map(n=>n*WORLD_SCALE));
export function mapPoint(u,v){
 const i=Math.max(0,shores.findIndex((p,j)=>j<shores.length-1&&v>=p[0]&&v<=shores[j+1][0]));
 const a=shores[i],b=shores[i+1],t=(v-a[0])/(b[0]-a[0]);
 const left=a[1]+(b[1]-a[1])*t,right=a[2]+(b[2]-a[2])*t;
 const bend=Math.sin(Math.PI*u)*Math.sin(Math.PI*v);
 return [(left+(right-left)*u+.38*bend*Math.sin(v*19))*WORLD_SCALE,(24*v-12+.72*bend*Math.sin(u*10+v*17))*WORLD_SCALE];
}
export const levels=divisionLevels;
export const bandV=(row,fraction)=>levels[row]+(levels[row+1]-levels[row])*fraction;
export const seams=[.50,.57,.45,.56,.43,.50];
export function seamAt(v){const row=Math.max(0,levels.findIndex((a,i)=>i<5&&v>=a&&v<=levels[i+1])),t=(v-levels[row])/(levels[row+1]-levels[row]);return seams[row]+(seams[row+1]-seams[row])*t+.06*Math.sin(t*Math.PI*2);}
export const pieces=modelPieces.map(p=>({...p,center:p.center.map(n=>n*WORLD_SCALE),points:p.points.map(point=>point.map(n=>n*WORLD_SCALE))}));
export const routes=[];
for(let row=0;row<5;row++)for(const f of [.26,.5,.74]){const v=bandV(row,f);routes.push(Array.from({length:61},(_,i)=>mapPoint(seamAt(v)*.5+i/60*.5,v)));}
for(const col of [0,1])routes.push(Array.from({length:241},(_,i)=>{const v=bandV(0,.26)+i/240*(bandV(4,.74)-bandV(0,.26));return mapPoint(col?(1+seamAt(v))/2:seamAt(v)/2,v);}));
export function routeClearance(x,z){return Math.min(...routes.flat().map(p=>Math.hypot(x-p[0],z-p[1])));}
// Short shared shore tips connect all ten pieces, without elevated bridges.
export const joins=[];
function addJoin(point,a,b){
 let clearance=Infinity;
 for(let i=1;i<coastline.length;i++){const p=coastline[i-1],q=coastline[i],dx=q[0]-p[0],dz=q[1]-p[1],t=Math.max(0,Math.min(1,((point[0]-p[0])*dx+(point[1]-p[1])*dz)/(dx*dx+dz*dz||1)));clearance=Math.min(clearance,Math.hypot(point[0]-p[0]-dx*t,point[1]-p[1]-dz*t));}
 const r=Math.min(SHORE_JOIN_RADIUS,clearance-.12);if(r>.6)joins.push({point,a,b,r});
}
for(let row=0;row<5;row++)for(const f of [.26,.5,.74]){const v=bandV(row,f);addJoin(mapPoint(seamAt(v),v),row*2,row*2+1);}
for(let row=1;row<5;row++)for(const col of [0,1]){const v=levels[row];addJoin(mapPoint(col?(1+seamAt(v))/2:seamAt(v)/2,v),(row-1)*2+col,row*2+col);}
export function insidePolygon(x,z,points){let yes=false;for(let i=0,j=points.length-1;i<points.length;j=i++){
 const a=points[i],b=points[j];if((a[1]>z)!==(b[1]>z)&&x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])yes=!yes;
}return yes;}
export function onLand(x,z){return pieces.some(p=>insidePolygon(x,z,p.points))||joins.some(j=>Math.hypot(x-j.point[0],z-j.point[1])<j.r);}

import * as THREE from 'three';
import {pieces,mapPoint,seamAt,insidePolygon,bandV,routeClearance,coastline} from './taiwan-layout.js?v=15';

export const themes=[
 {name:'病理科',place:'微觀花園',color:'#b68c91',roof:'gable',prop:'microscope',role:2},
 {name:'影像醫學',place:'光影觀察所',color:'#47798d',roof:'dome',prop:'scanner',role:3},
 {name:'腫瘤內科',place:'陪伴庭院',color:'#9d9bb1',roof:'gable',prop:'pergola',role:1},
 {name:'腫瘤外科',place:'綠蔭照護站',color:'#6e9b87',roof:'flat',prop:'arch',role:4},
 {name:'整形外科',place:'重建花園',color:'#c39d88',roof:'gable',prop:'ribbon',role:2},
 {name:'放射腫瘤科',place:'星光庭院',color:'#8d9fbc',roof:'dome',prop:'orbits',role:5},
 {name:'心臟科',place:'心律水庭',color:'#bf8792',roof:'gable',prop:'heart',role:2},
 {name:'家庭醫學科',place:'日常小屋',color:'#a4ab82',roof:'gable',prop:'pergola',role:0},
 {name:'復健科',place:'活力步道',color:'#4d8d80',roof:'flat',prop:'rails',role:3},
 {name:'生育保存',place:'種子溫室',color:'#8c6a92',roof:'glass',prop:'sprout',role:1}
];

export function buildLandscapes({island,material,mesh,box,ball,cylinder,colliders,createCharacter,towerX,towerZ}){
 const ivory=material('architecture-ivory','#f0e6d3'),timber=material('architecture-timber','#a17c5a'),glass=material('architecture-glass','#a9c8cb',.28),brass=material('architecture-brass','#c5aa70',.4),green=material('garden-leaf','#7f9c75'),stone=material('garden-stone','#c8bfab');
 const anchors=[],npcModels=[];
 function tube(parent,points,r,mat){return mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p))),24,r,6,false),mat,parent);}
 function arch(parent,mat,x=0,y=.6,z=0,r=.45){const o=mesh(new THREE.TorusGeometry(r,.045,8,32,Math.PI),mat,parent,x,y,z);return o;}
 function bench(parent,x,z){box(parent,timber,x,.30,z,.70,.07,.27);box(parent,timber,x,.48,z-.11,.70,.30,.045);for(const dx of [-.26,.26])box(parent,brass,x+dx,.14,z,.045,.27,.22);}
 function specialtyBuilding(parent,theme,index){
  parent.name='specialty-building-'+index;
  const accent=material('theme-'+theme.name,theme.color),dark=material('architecture-ink','#52676b');
  const volume=(x,y,z,w,h,d,mat=ivory)=>box(parent,mat,x,y,z,w,h,d,.055);
  const ring=(x,y,z,r,thickness,mat=accent)=>mesh(new THREE.TorusGeometry(r,thickness,10,48),mat,parent,x,y,z);
  const window=(x,y,z,w=.25,h=.40)=>{volume(x,y,z,w+.045,h+.045,.045,timber);volume(x,y,z+.027,w,h,.018,glass);volume(x,y,z+.04,.018,h,.02,ivory);};
  const dome=(x,y,z,r,sy,mat)=>{const d=mesh(new THREE.SphereGeometry(r,28,16,0,Math.PI*2,0,Math.PI/2),mat,parent,x,y,z);d.scale.y=sy;return d;};
  const roof=(x,y,z,w,d)=>{const shape=new THREE.Shape();shape.moveTo(-w/2,0);shape.lineTo(0,w*.42);shape.lineTo(w/2,0);shape.closePath();mesh(new THREE.ExtrudeGeometry(shape,{depth:d,bevelEnabled:true,bevelSize:.02,bevelThickness:.02,bevelSegments:1,steps:1}),accent,parent,x,y,z-d/2);};
  // Shared entrance details, but each department has its own massing and roof silhouette.
  cylinder(parent,stone,0,.055,0,1.08,1.08,.11,48);
  if(index===0){
   volume(-.34,.67,0,.85,1.22,1.05);volume(.40,.87,-.05,.66,1.62,.92);
   volume(-.34,1.32,0,.94,.13,1.13,accent);volume(.4,1.73,-.05,.76,.13,1.01,accent);
   const scope=new THREE.Group();scope.position.set(.33,1.80,-.03);scope.scale.setScalar(.95);parent.add(scope);feature(scope,'microscope',accent);
   for(const x of [-.61,-.34,-.07])window(x,.82,.55,.17,.53);
   for(const y of [.62,1.18])window(.42,y,.43,.35,.32);
   for(let k=0;k<3;k++)volume(-.35,1.46+k*.07,0,.62,.035,.38,k%2?glass:ivory);
  }else if(index===1){
   cylinder(parent,ivory,0,.65,0,.73,.73,1.20,48);cylinder(parent,accent,0,1.29,0,.82,.82,.12,48);
   ring(0,1.97,0,.72,.16);ring(0,1.97,-.12,.81,.035,brass);ring(0,1.97,.13,.46,.035,brass);
   for(let k=0;k<8;k++){const a=k*Math.PI/4;const fin=volume(Math.sin(a)*.65,1.97+Math.cos(a)*.65,0,.06,.16,.30,ivory);fin.rotation.z=-a;}
   for(const x of [-.48,.48])window(x,.76,.56,.19,.56);
   volume(0,1.02,.71,.57,.09,.28,accent);
  }else if(index===2){
   for(const x of [-.44,.44]){volume(x,.65,-.07,.66,1.20,1.0);dome(x,1.25,-.07,.40,.8,accent);window(x,.8,.45,.30,.48);}
   volume(0,.43,-.39,.35,.76,.44);volume(0,1.31,-.39,.52,.13,.60,accent);
   for(const x of [-.7,.7])volume(x,.70,.63,.055,1.3,.055,timber);
   for(let k=0;k<7;k++)volume(-.72+k*.24,1.36,.57,.075,.08,.43,timber);
   tube(parent,[[-.73,1.43,.63],[-.35,1.60,.63],[.1,1.48,.63],[.72,1.48,.63]],.045,green);
   for(let k=0;k<5;k++)ball(parent,accent,-.55+k*.25,1.54,.64,.075);
   // A welcoming petal lantern over the central courtyard.
   for(let k=0;k<5;k++){const a=k*Math.PI*2/5;ball(parent,accent,Math.cos(a)*.20,1.85+Math.sin(a)*.20,-.36,.14,.14,.07);}ball(parent,brass,0,1.85,-.30,.09);
  }else if(index===3){
   volume(0,.63,0,1.42,1.15,1.08);volume(0,1.24,0,1.57,.13,1.21,accent);
   volume(-.35,1.64,-.12,.68,.69,.73);volume(-.35,2.01,-.12,.78,.09,.83,accent);
   for(const x of [-.5,.5])window(x,.73,.57,.27,.48);
   ring(-.35,1.69,.27,.23,.035,brass);volume(-.35,1.69,.29,.28,.065,.025,accent);volume(-.35,1.69,.29,.065,.28,.025,accent);
   for(let k=0;k<4;k++)volume(.12+k*.16,1.34,-.20,.045,.10,.72,ivory);
   arch(parent,accent,0,.48,.65,.48);for(const x of [-.48,.48])volume(x,.29,.65,.08,.57,.09,accent);
  }else if(index===4){
   for(const x of [-.42,.42]){cylinder(parent,ivory,x,.67,0,.42,.42,1.22,36);dome(x,1.3,0,.47,.65,accent);window(x,.80,.43,.26,.45);}
   volume(0,.57,-.25,.35,1.0,.64);const ribbon=new THREE.Group();ribbon.position.set(0,1.55,0);parent.add(ribbon);feature(ribbon,'ribbon',accent);
   tube(parent,[[-.85,1.05,.44],[-.43,1.34,.61],[0,1.14,.69],[.43,1.34,.61],[.85,1.05,.44]],.055,brass);
  }else if(index===5){
   cylinder(parent,ivory,0,.62,0,.74,.74,1.13,48);dome(0,1.19,0,.83,.78,accent);
   for(let k=0;k<6;k++){const a=k*Math.PI/3;const arc=ring(0,1.82,0,.57,.025,brass);arc.rotation.set(.8,a,.3);}
   ball(parent,brass,0,1.83,0,.14);for(const x of [-.50,.50])window(x,.74,.56,.20,.45);
   for(let k=0;k<7;k++){const a=k*Math.PI/6;ball(parent,ivory,Math.cos(a)*.67,1.2+Math.sin(a)*.56,.25,.045);}
  }else if(index===6){
   volume(0,.67,0,1.35,1.22,1.05);roof(0,1.3,0,1.53,1.18);
   const heart=new THREE.Group();heart.position.set(0,1.79,0);heart.scale.setScalar(.9);parent.add(heart);feature(heart,'heart',accent);
   volume(0,1.08,.56,1.12,.24,.05,dark);
   tube(parent,[[-.48,1.08,.60],[-.28,1.08,.60],[-.19,1.15,.60],[-.1,.99,.60],[0,1.20,.60],[.12,1.07,.60],[.48,1.07,.60]],.018,ivory);
   for(const x of [-.46,.46])window(x,.65,.55,.22,.36);
  }else if(index===7){
   volume(-.27,.65,0,.88,1.18,1.04);roof(-.27,1.26,0,1.02,1.18);
   volume(.5,.45,.05,.54,.78,.90);roof(.5,.86,.05,.67,1.02);
   cylinder(parent,ivory,-.27,1.80,0,.20,.23,.26,32);const clock=ring(-.27,1.79,.23,.14,.025,timber);volume(-.27,1.83,.25,.015,.09,.02,dark);volume(-.23,1.79,.25,.09,.015,.02,dark);
   window(-.49,.76,.55,.23,.37);window(.51,.53,.53,.25,.33);
   for(const x of [-.65,.1])volume(x,.42,.72,.05,.8,.05,timber);volume(-.27,.87,.69,.93,.10,.35,accent);
   volume(.5,1.27,-.22,.16,.48,.19,timber);
  }else if(index===8){
   for(let k=0;k<3;k++){const x=-.5+k*.50,h=.68+k*.35;volume(x,h/2+.08,0,.49,h,1.02);volume(x,h+.13,0,.54,.11,1.10,accent);window(x,h*.55+.1,.53,.29,h*.45);for(const z of [-.35,.35])volume(x,h+.30,z,.025,.28,.025,brass);tube(parent,[[x-.20,h+.44,-.35],[x+.20,h+.44,-.35]],.018,brass);}
   for(const x of [-.70,.70])volume(x,1.0,-.40,.055,1.8,.055,timber);volume(0,1.94,-.40,1.5,.10,.35,accent);
   for(let k=0;k<3;k++)volume(-.48+k*.16,.10+k*.08,.68,.16,.16+k*.16,.23,stone);
   for(const x of [-.72,.72])tube(parent,[[x,.25,.72],[x,.72,.72],[x,.72,.25]],.028,accent);
  }else{
   cylinder(parent,ivory,0,.34,0,.78,.78,.58,48);dome(0,.63,0,.82,1.42,glass);
   for(let k=0;k<8;k++){const a=k*Math.PI/4,pts=[];for(let j=0;j<=16;j++){const t=j*Math.PI/32;pts.push([Math.cos(a)*.83*Math.cos(t),.63+1.18*Math.sin(t),Math.sin(a)*.83*Math.cos(t)]);}tube(parent,pts,.025,ivory);}
   for(let k=0;k<8;k++){const a=k*Math.PI/4;const petal=ball(parent,accent,Math.cos(a)*.55,1.61,Math.sin(a)*.55,.23,.035,.12);petal.rotation.y=-a;}
   const seed=new THREE.Group();seed.position.set(0,1.82,0);seed.scale.setScalar(.8);parent.add(seed);feature(seed,'sprout',green);
   for(const x of [-.49,.49])ball(parent,green,x,.52,.35,.17,.24,.17);
  }
  // A readable department plaque belongs to the facade rather than floating over the island.
  volume(0,.42,.76,.34,.66,.06,timber);volume(0,.44,.80,.26,.54,.025,glass);ball(parent,brass,.10,.4,.83,.025);
  volume(0,.93,.76,1.24,.26,.10,accent);
  const canvas=document.createElement('canvas');canvas.width=512;canvas.height=112;
  const ctx=canvas.getContext('2d');ctx.fillStyle='#fff9e8';ctx.font='600 58px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(theme.name,256,56);
  const plaque=mesh(new THREE.PlaneGeometry(1.17,.23),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(canvas),transparent:true,depthWrite:false}),parent,0,.93,.817);plaque.castShadow=false;
  for(const x of [-.80,.80]){cylinder(parent,accent,x,.18,.45,.12,.09,.26,16);ball(parent,green,x,.38,.45,.16,.18,.16);}
 }
 function feature(parent,kind,accent){
  cylinder(parent,stone,0,.06,0,.42,.46,.12,24);
  if(kind==='microscope'){
   box(parent,ivory,0,.16,0,.44,.12,.33);tube(parent,[[.13,.20,-.05],[.24,.58,-.05],[.05,.78,-.05]],.065,accent);
   box(parent,brass,0,.43,.05,.40,.04,.28);const barrel=cylinder(parent,accent,-.06,.72,.08,.07,.09,.34,12);barrel.rotation.z=-.42;ball(parent,glass,-.13,.88,.08,.075,.025,.075);
  }else if(kind==='scanner'){
   mesh(new THREE.TorusGeometry(.31,.10,12,28),ivory,parent,0,.48,0);mesh(new THREE.TorusGeometry(.24,.025,8,28),accent,parent,0,.48,.09);box(parent,glass,0,.30,.35,.22,.08,.60);box(parent,ivory,0,.17,.38,.12,.26,.20);
  }else if(kind==='heart'){
   const shape=new THREE.Shape();shape.moveTo(0,-.25);shape.bezierCurveTo(-.7,.2,-.2,.65,0,.28);shape.bezierCurveTo(.2,.65,.7,.2,0,-.25);const g=new THREE.ExtrudeGeometry(shape,{depth:.10,bevelEnabled:true,bevelSize:.03,bevelThickness:.03,bevelSegments:2,steps:1});mesh(g,accent,parent,0,.55,0);
   cylinder(parent,glass,0,.14,0,.37,.37,.06,32);
  }else if(kind==='sprout'){
   tube(parent,[[0,.16,0],[.02,.5,0],[0,.8,0]],.035,green);for(const sign of [-1,1]){const l=ball(parent,green,sign*.16,.57+sign*.10,0,.22,.09,.11);l.rotation.z=sign*.45;}
  }else if(kind==='orbits'){
   ball(parent,brass,0,.58,0,.13);for(let i=0;i<3;i++){const ring=mesh(new THREE.TorusGeometry(.36,.02,6,32),accent,parent,0,.58,0);ring.rotation.set(i*.8,i*.7,0);}
  }else if(kind==='ribbon'){
   tube(parent,[[-.25,.18,0],[.16,.62,0],[.12,.89,0],[-.12,.89,0],[-.16,.62,0],[.25,.18,.05]],.055,accent);
  }else if(kind==='rails'){
   for(const x of [-.23,.23]){for(const z of [-.3,.3])cylinder(parent,brass,x,.35,z,.023,.023,.58,8);tube(parent,[[x,.65,-.36],[x,.65,.36]],.032,accent);}
  }else{
   for(const x of [-.34,.34])for(const z of [-.23,.23])box(parent,timber,x,.45,z,.045,.8,.045,.01);
   arch(parent,accent,0,.8,-.23,.34);arch(parent,accent,0,.8,.23,.34);
   for(let i=0;i<5;i++)box(parent,timber,-.4+i*.2,.86,0,.06,.06,.65,.01);
   for(const x of [-.35,.35])ball(parent,green,x,.92,0,.18,.12,.3);
  }
 }
 for(const [i,p] of pieces.entries()){
  const theme=themes[i];let anchor=null,scale=1;
  // Keep construction away from the shared shore approaches and the main promenade.
  for(const size of [1.55,1.3,1.1,.9,.72,.55]){
   for(const [frac,across] of [.26,.30,.72,.76,.36,.64,.42,.58,.12,.18,.86,.92,.06,.96].flatMap(v=>[.53,.38,.65,.25,.78,.15,.87].map(u=>[v,u]))){
    const v=bandV(p.row,frac),u=p.col?seamAt(v)+(1-seamAt(v))*across:seamAt(v)*across,[x,z]=mapPoint(u,v),r=1.12*size;
    if(Array.from({length:16},(_,k)=>insidePolygon(x+Math.cos(k*Math.PI/8)*r,z+Math.sin(k*Math.PI/8)*r,p.points)).every(Boolean)&&routeClearance(x,z)>r+.28&&Math.hypot(x-towerX,z-towerZ)>r+1.8&&!colliders.some(c=>Math.hypot(x-c.x,z-c.z)<r+c.r+.1)){anchor=[x,z];scale=size;break;}
   }if(anchor)break;
  }
  if(!anchor)throw new Error('No safe building footprint for island '+p.id);
  const [x,z]=anchor,group=new THREE.Group();group.position.set(x,.7,z);group.scale.setScalar(scale);island.add(group);specialtyBuilding(group,theme,i);colliders.push({x,z,r:1.08*scale});
  anchors.push({id:p.id,name:theme.name,place:theme.place,point:anchor,scale,architecture:theme.prop,buildingVersion:3});
  // Place distinct symbolic objects in an open patch, leaving the walking corridor clear.
  const candidates=[];for(const du of [.30,.70,.15,.85,.22,.78,.38,.62])for(const dv of [.66,.36,.82,.18,.24,.76,.10,.90]){const v=bandV(p.row,dv),u=p.col?seamAt(v)+(1-seamAt(v))*du:seamAt(v)*du; candidates.push(mapPoint(u,v));}
  const free=(pt,r)=>Math.hypot(pt[0]-towerX,pt[1]-towerZ)>r+1.8&&routeClearance(pt[0],pt[1])>r+.28&&Array.from({length:12},(_,k)=>insidePolygon(pt[0]+Math.cos(k*Math.PI/6)*r,pt[1]+Math.sin(k*Math.PI/6)*r,p.points)).every(Boolean)&&!colliders.some(c=>Math.hypot(pt[0]-c.x,pt[1]-c.z)<r+c.r+.22);
  let propPoint=candidates.find(pt=>free(pt,.30));
  anchors[i].feature=propPoint?theme.prop:null;
  if(propPoint){const g=new THREE.Group();g.position.set(propPoint[0],.7,propPoint[1]);g.scale.setScalar(.65);island.add(g);feature(g,theme.prop,material('theme-'+theme.name,theme.color));colliders.push({x:propPoint[0],z:propPoint[1],r:.28});}
  else if(theme.prop==='pergola'){const canopy=new THREE.Group();canopy.position.set(0,.65,.50);canopy.scale.setScalar(.40);group.add(canopy);feature(canopy,'pergola',material('theme-'+theme.name,theme.color));anchors[i].feature='entry-pergola';}
  const seat=candidates.find(pt=>free(pt,.42));if(seat){const g=new THREE.Group();g.position.set(seat[0],.7,seat[1]);island.add(g);bench(g,0,0);colliders.push({x:seat[0],z:seat[1],r:.38});}
  // Moving residents are created by the shared crowd renderer, never baked into terrain.
  // Planter borders and small flower clusters add close-range detail without blocking paths.
  for(let k=0;k<6;k++){
   const v=bandV(p.row,.14+(k%6)*.14),u=p.col?seamAt(v)+(1-seamAt(v))*.88:seamAt(v)*.12,[fx,fz]=mapPoint(u,v);
   if(!free([fx,fz],.08))continue;
   ball(island,green,fx,.76,fz,.10,.07,.10);for(let j=0;j<3;j++)ball(island,material('petal-'+i,theme.color),fx+Math.cos(j*2.1)*.05,.82,fz+Math.sin(j*2.1)*.05,.035,.025,.035);
  }
 }
 // Follow the actual coastline with surf and intermittent rounded boulders.
 const surfPoints=coastline.map(([x,z])=>new THREE.Vector3(x,-.52,z));const surf=mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(surfPoints,true),600,.025,4,true),material('surf','#d7ece3'),island);surf.castShadow=false;
 for(let i=0;i<coastline.length-1;i+=4){const [x,z]=coastline[i],o=mesh(new THREE.DodecahedronGeometry(.11+(i%3)*.035,1),stone,island,x,-.14,z);o.scale.set(1,.7,.8);o.rotation.set(i*.17,i*.4,0);}
 return {anchors,npcModels};
}

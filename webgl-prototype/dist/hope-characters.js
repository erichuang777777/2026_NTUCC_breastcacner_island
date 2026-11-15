import * as THREE from 'three';

export const characterStyles=[
 {id:'visitor',name:'病友・玫瑰頭巾',description:'約 40–50 歲的病友情境角色；玫瑰頭巾、粉色外套、牛仔褲與隨身背包。',shirt:'#b97c87',pants:'#657a8d',hair:'#654738',style:'scarf'},
 {id:'scarf',name:'陪伴者・日常服',description:'約 40–50 歲的陪伴者情境角色；以舒適日常服裝呈現，不設定特定病史。',shirt:'#48677d',pants:'#a98e74',hair:'#47372e',style:'short'},
 {id:'doctor',name:'醫師・深灰工作服',description:'約 40–50 歲的醫師情境角色；深灰工作服與聽診器。',shirt:'#626b76',pants:'#626b76',hair:'#52473f',style:'doctor'},
 {id:'nurse',name:'護理師・深藍制服',description:'約 20–30 歲的護理師情境角色；深藍制服與識別證。',shirt:'#385779',pants:'#385779',hair:'#71503e',style:'bob'},
 {id:'surgeon',name:'醫師・綠色刷手服',description:'約 40–50 歲的手術團隊醫師情境角色；綠色刷手服與手術帽。',shirt:'#39756b',pants:'#39756b',hair:'#654738',style:'cap'},
 {id:'scrub',name:'護理師・刷手服與口罩',description:'約 20–30 歲的手術室護理師情境角色；綠色刷手服、手術帽與口罩。',shirt:'#39756b',pants:'#39756b',hair:'#654738',style:'mask'}
];

export const filmCharacterStyles=[
 {id:'visitor',name:'女主角・灰頭巾',description:'依微電影化療期造型：灰頭巾、深灰連帽外套。以島上可愛 3D 比例呈現。',shirt:'#35363a',pants:'#454955',hair:'#797a80',style:'scarf'},
 {id:'scarf',name:'阿澤・日常陪伴',description:'依阿澤參考造型：黑色短髮、深藍連帽外套、灰色內搭。',shirt:'#31394f',pants:'#5e6370',hair:'#262522',style:'short'},
 {id:'doctor',name:'林醫師・白袍眼鏡',description:'依林醫師參考造型：黑框眼鏡、白袍、淺藍襯衫與深色領帶。',shirt:'#f0f0ee',pants:'#4a505d',hair:'#282929',style:'short'},
 {id:'nurse',name:'陳護理師・深藍制服',description:'依陳護理師參考造型：束起的黑髮、深藍制服、識別證與護理錶。',shirt:'#303e6a',pants:'#303e6a',hair:'#292522',style:'ponytail'},
 {id:'surgeon',name:'王醫師・白袍眼鏡',description:'依王醫師參考造型：灰黑短髮、金屬框眼鏡、白袍與深藍內搭。',shirt:'#eff0ee',pants:'#3b4050',hair:'#464546',style:'short'},
];

export function createCharacter(index,{material,ball,box,mesh,cylinder},appearance={}){
 const base=characterStyles[index],spec={...base,...appearance,id:base.id},person=new THREE.Group(),body=new THREE.Group(),head=new THREE.Group(),limbs=[];
 person.name='hope-character-'+spec.id;body.name='body';head.name='head';person.add(body);head.position.y=1.15;body.add(head);
 const shirtColor=spec.shirt||base.shirt,pantsColor=spec.pants||base.pants,hairColor=spec.hair||base.hair,skinColor=spec.skin||'#edc6a7';
 const skin=material('skin-'+skinColor,skinColor),hair=material('hair-'+hairColor,hairColor),shirt=material('outfit-'+spec.id+'-'+shirtColor,shirtColor),pants=material('pants-'+spec.id+'-'+pantsColor,pantsColor),shoe=material('shoe','#fff8ed'),ink=material('eyes','#453f39'),cream=material('ivory','#fff5de');
 ball(body,shirt,0,.70,0,.235,.31,.16);
 if(spec.style==='scarf'){
  ball(body,cream,0,.70,.142,.13,.245,.045);
  for(const sign of [-1,1])ball(body,shirt,sign*.145,.70,.125,.10,.27,.075);
  const pinkRibbon=material('patient-ribbon','#e28fa4');const ribbon=new THREE.CatmullRomCurve3([new THREE.Vector3(-.13,.86,.183),new THREE.Vector3(-.10,.80,.188),new THREE.Vector3(-.13,.74,.19),new THREE.Vector3(-.16,.80,.188),new THREE.Vector3(-.13,.86,.183)]);mesh(new THREE.TubeGeometry(ribbon,24,.012,7,false),pinkRibbon,body);
  const bag=material('patient-bag','#eadfca'),strap=material('patient-bag-strap','#f5ecda');box(body,bag,0,.60,-.205,.31,.34,.12,.06);const strapCurve=new THREE.CatmullRomCurve3([new THREE.Vector3(-.22,.94,.02),new THREE.Vector3(-.18,.84,-.13),new THREE.Vector3(-.12,.60,-.18)]);mesh(new THREE.TubeGeometry(strapCurve,18,.018,7,false),strap,body);
 }

 ball(head,spec.style==='scarf'?material('scarf-'+spec.id+'-'+shirtColor,shirtColor):hair,0,.025,-.025,.31,.32,.28);ball(head,skin,0,-.01,.075,.275,.265,.23);
 for(const x of [-.23,.23]){ball(head,skin,x,-.045,.04,.068,.09,.065);ball(head,material('inner-ear','#dca991'),x*1.10,-.045,.09,.025,.045,.012);}
 if(spec.style==='scarf'||spec.style==='cap'||spec.style==='mask'){
  const cloth=spec.style==='scarf'?material('scarf-'+spec.id+'-'+shirtColor,shirtColor):shirt;
  ball(head,cloth,0,.16,-.04,.318,.23,.28);
  for(let i=0;i<3;i++){
   const offset=i*.035,curve=new THREE.CatmullRomCurve3([new THREE.Vector3(-.28,.06+offset,.11),new THREE.Vector3(-.16,.21+offset,.20),new THREE.Vector3(.12,.20+offset,.21),new THREE.Vector3(.29,.06+offset,.09)]);
   mesh(new THREE.TubeGeometry(curve,18,.017,6,false),cloth,head);
  }
  ball(head,cloth,-.27,-.06,-.18,.10,.12,.10);const tail=ball(head,cloth,-.25,-.24,-.18,.07,.2,.045);tail.rotation.z=-.3;
 }else{
  for(const [x,y,z,s] of [[-.16,.19,.18,.14],[0,.23,.15,.16],[.17,.18,.14,.15],[-.26,.03,0,.10],[.26,.03,0,.10]])ball(head,hair,x,y,z,s,s*.9,s*.7);
  if(spec.style==='bob')for(const x of [-.24,.24])ball(head,hair,x,-.13,-.04,.10,.22,.18);
  const highlight=material('hair-soft-highlight','#675344');
  for(let i=0;i<5;i++){const lock=ball(head,i%2?hair:highlight,-.20+i*.085,.23+Math.sin(i*.8)*.025,.14,.075,.055,.105);lock.rotation.z=-.3+i*.08;}
 }
 for(const x of [-.095,.095]){
  ball(head,cream,x,.008,.284,.036,.044,.018);
  ball(head,material('iris','#765343'),x,.006,.300,.025,.032,.010);
  ball(head,ink,x,.006,.308,.014,.023,.006);ball(head,cream,x-.008,.021,.315,.008);
  const lid=new THREE.CatmullRomCurve3([new THREE.Vector3(x-.031,.020,.298),new THREE.Vector3(x,.049,.292),new THREE.Vector3(x+.031,.020,.298)]);mesh(new THREE.TubeGeometry(lid,10,.005,5,false),hair,head);
  ball(head,material('cheek','#e6a6a5'),x*1.55,-.07,.26,.04,.02,.012);
  const brow=ball(head,hair,x,.075,.278,.045,.012,.012);brow.rotation.z=x>0?-.1:.1;
 }
 ball(head,skin,0,-.035,.31,.025,.028,.025);
 const smile=new THREE.CatmullRomCurve3([new THREE.Vector3(-.045,-.10,.29),new THREE.Vector3(0,-.115,.299),new THREE.Vector3(.045,-.10,.29)]);mesh(new THREE.TubeGeometry(smile,10,.006,5,false),ink,head);
 if(spec.style==='mask'){box(head,material('mask','#c1ddd9'),0,-.09,.286,.35,.15,.06,.035);for(const x of [-.20,.20])box(head,cream,x,-.04,.18,.015,.02,.20,.005);}
 for(const sign of [-1,1]){
  const arm=new THREE.Group();arm.name=sign<0?'arm-left':'arm-right';arm.position.set(sign*.235,.85,0);body.add(arm);ball(arm,shirt,sign*.025,-.12,0,.08,.18,.09);ball(arm,skin,sign*.03,-.30,.015,.065,.08,.065);cylinder(arm,shirt,sign*.025,-.24,0,.074,.074,.045,16);
  const leg=new THREE.Group();leg.name=sign<0?'leg-left':'leg-right';leg.position.set(sign*.105,.48,0);body.add(leg);box(leg,pants,0,-.18,0,.145,.38,.16,.055);ball(leg,shoe,0,-.40,.045,.09,.08,.14);ball(leg,material('shoe-sole','#d7ceba'),0,-.455,.045,.091,.023,.14);for(let j=0;j<3;j++)box(leg,cream,0,-.34,.055+j*.029,.10,.009,.010,.003);limbs.push({arm,leg,sign});
 }
 if(index>=2){
  for(const sign of [-1,1]){const collar=box(body,shirt,sign*.055,.915,.15,.09,.11,.025,.01);collar.rotation.z=sign*.45;}
  box(body,cream,.12,.79,.16,.085,.09,.02,.009);box(body,material('badge','#9aab9c'),.12,.80,.176,.05,.015,.008,.002);
  box(body,shirt,-.12,.61,.155,.14,.10,.03,.01);
  box(body,material('badge-clip','#a9b5b5',.35),.12,.845,.18,.035,.02,.013,.005);
  box(body,cream,-.12,.66,.176,.125,.009,.006,.002);
 }else{
  for(const x of [-.08,.08])box(body,shirt,x,.72,.16,.10,.42,.04,.02);
  for(let i=0;i<3;i++)ball(body,cream,.04,.60+i*.09,.19,.012);
 }
 if(spec.style==='doctor'){
  const curve=new THREE.CatmullRomCurve3([new THREE.Vector3(-.11,.91,.18),new THREE.Vector3(-.13,.69,.20),new THREE.Vector3(.07,.66,.20),new THREE.Vector3(.11,.91,.18)]);
  mesh(new THREE.TubeGeometry(curve,16,.012,6,false),ink,body);ball(body,material('metal','#b9c4c2',.35),.07,.65,.21,.045,.045,.015);
 }
 if(spec.style==='scarf'){
  box(body,material('bag','#e2b4b9'),-.28,.5,0,.17,.23,.15,.035);
  box(body,material('bag-strap','#dfacb7'),-.23,.78,.04,.035,.5,.04,.012);
 }
 return {person,body,head,limbs,spec};
}

// 在場景靜態合批移除原始子網格前保存包圍盒。
{
 window.__propsObstacles=[];
 scene.updateMatrixWorld(true);
 // 僅取建築與地上大型物件；不使用分區、地面或尋路網格的包圍盒。
 const buildingNames=/^(specialty-building-|ntu-cancer-center$|hope-lighthouse$)/;
 const selected=new Set();
 scene.traverse(o=>{if(buildingNames.test(o.name))selected.add(o);});
 for(const o of island.children) {
  if(!o.isGroup || selected.has(o))continue;
  const b=new THREE.Box3().setFromObject(o),size=b.getSize(new THREE.Vector3());
  if(size.y>=.55 && Math.max(size.x,size.z)>=.7 && Math.max(size.x,size.z)<=6 && b.min.y>=.5)selected.add(o);
 }
 for(const o of selected) {
  const b=new THREE.Box3().setFromObject(o);
  if(b.isEmpty())continue;
  window.__propsObstacles.push({name:o.name||`large-object-${window.__propsObstacles.length}`,type:buildingNames.test(o.name)?'building':'large-object',
   x:(b.min.x+b.max.x)/2,z:(b.min.z+b.max.z)/2,halfX:(b.max.x-b.min.x)/2,halfZ:(b.max.z-b.min.z)/2});
 }
}

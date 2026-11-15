export const WISH_KEY='hopeIslandStudyWishesV1';
const islandIds=['pathology','imaging','medical_oncology','surgical_oncology','reconstruction','radiation_oncology','cardiology','family_medicine','rehabilitation','fertility'];
export function createWishStore(storage){
 let persistent=true,wishes=[];
 try{const raw=JSON.parse(storage.getItem(WISH_KEY)??storage.getItem('hopeIslandWishes')??'[]');if(Array.isArray(raw))wishes=raw.filter(w=>w&&typeof w.id==='string'&&typeof w.text==='string').map(w=>({...w,island:Number.isInteger(w.island)&&w.island>=0&&w.island<10?w.island:Math.max(0,islandIds.indexOf(String(w.islandId||'').replace('island.',''))),status:w.completed||w.status==='completed'||w.status==='archived'?'archived':'lit'}));}catch{persistent=false;}
 function save(){try{storage.setItem(WISH_KEY,JSON.stringify(wishes));persistent=true;}catch{persistent=false;}}
 function add(text,island,id,{requirePersistence=false}={}){text=String(text).trim().slice(0,200);if(!text||wishes.some(w=>w.id===id))return null;const wish={id,text,island:Math.max(0,Math.min(9,island)),status:'lit',createdAt:new Date().toISOString()};wishes.push(wish);save();if(requirePersistence&&!persistent){wishes.pop();return null;}return wish;}
 function complete(id){const w=wishes.find(w=>w.id===id);if(!w||w.status!=='lit')return false;w.status='completed';w.completedAt=new Date().toISOString();save();return true;}
 function archive(id){const w=wishes.find(w=>w.id===id);if(!w||w.status!=='completed')return false;w.status='archived';w.completed=true;save();return true;}
 return {get wishes(){return wishes;},get persistent(){return persistent;},add,complete,archive};
}

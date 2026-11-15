import {createHash,pbkdf2,timingSafeEqual,randomBytes} from 'node:crypto';
import {promisify} from 'node:util';
import {unzipSync} from 'fflate';
const derive=promisify(pbkdf2);
export class ApiError extends Error{constructor(status,message){super(message);this.status=status;}}
export function requireValue(condition,message,status=400){if(!condition)throw new ApiError(status,message);}
export const digest=value=>createHash('sha256').update(String(value)).digest('hex');
export const secret=()=>randomBytes(32).toString('base64url');
export async function hashPassword(password){const salt=randomBytes(16).toString('hex');return salt+':'+(await derive(password,Buffer.from(salt,'hex'),600000,32,'sha256')).toString('hex');}
export async function verifyPassword(password,hash){if(!/^[a-f0-9]{32}:[a-f0-9]{64}$/.test(hash||''))return false;const [salt,expected]=hash.split(':'),actual=await derive(password,Buffer.from(salt,'hex'),600000,32,'sha256');return timingSafeEqual(actual,Buffer.from(expected,'hex'));}
export function cookie(request,name){return request.headers.get('cookie')?.split(';').map(v=>v.trim()).find(v=>v.startsWith(name+'='))?.slice(name.length+1)||'';}
export const bearer=req=>(req.headers.get('authorization')||'').replace(/^Bearer /,'');
export function profile(body){requireValue(body&&typeof body==='object','角色格式錯誤。');requireValue(['visitor','scarf','doctor','nurse','surgeon','scrub'].includes(body.role),'角色不正確。');const a=body.appearance;requireValue(a&&['short','bob','scarf','cap','mask'].includes(a.style),'髮型不正確。');const result={style:a.style};for(const key of ['shirt','pants','hair','skin']){requireValue(typeof a[key]==='string'&&/^#[0-9a-fA-F]{6}$/.test(a[key]),'顏色格式錯誤。');result[key]=a[key];}requireValue(typeof body.displayName==='string'&&body.displayName.trim().length<=18,'暱稱最多 18 字。');return {role:body.role,appearance:result,displayName:body.displayName.trim()};}
export const publicProfile=r=>({id:r.id,status:r.status,displayName:r.display_name,role:r.role,appearance:JSON.parse(r.appearance_json),createdAt:r.created_at,updatedAt:r.updated_at});
export function decodeBase64(value){requireValue(typeof value==='string'&&/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value),'附件資料損毀。');return Buffer.from(value,'base64');}
export function fileType(name,data){requireValue(typeof name==='string'&&name.length>0&&name.length<=160&&!/[\\/\x00-\x1f]/.test(name),'附件名稱錯誤。');requireValue(data.length>0&&data.length<=12*1024*1024,'附件上限為 12 MB。',413);const ext=name.split('.').at(-1).toLowerCase();
 if(ext==='pdf'&&data.subarray(0,5).toString()==='%PDF-')return 'application/pdf';
 if(ext==='png'&&data.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))return 'image/png';
 if(['jpg','jpeg'].includes(ext)&&data.subarray(0,3).equals(Buffer.from([255,216,255])))return 'image/jpeg';
 if(ext==='docx'){let total=0,count=0;const names=[];try{unzipSync(data,{filter:f=>{total+=f.originalSize;count++;names.push(f.name);requireValue(count<2000&&total<80*1024*1024,'Word 解壓後過大。');requireValue(!f.name.includes('vbaProject'),'不接受巨集檔案。');return false;}});}catch(e){if(e instanceof ApiError)throw e;throw new ApiError(400,'Word 檔案損毀。');}requireValue(names.includes('word/document.xml')&&names.includes('[Content_Types].xml'),'Word 格式不正確。');return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';}
 throw new ApiError(415,'僅接受 PDF、DOCX、JPG 與 PNG，且內容須符合格式。');
}

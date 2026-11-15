// Import before first public API use. Refuses to merge into an occupied database.
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {getStore} from '@netlify/blobs';
import {database} from '../server/database.mjs';
const file=process.argv[2];if(!file)throw Error('請提供本機匯出檔案路徑');
const input=JSON.parse(await readFile(file,'utf8')),db=database(),store=getStore({name:'hope-attachments',consistency:'strong',...(process.env.NETLIFY_SITE_ID&&process.env.NETLIFY_AUTH_TOKEN?{siteID:process.env.NETLIFY_SITE_ID,token:process.env.NETLIFY_AUTH_TOKEN}:{})});
const columns={content_settings:['key','value'],agent_keys:['id','label','token_hash','prefix','created_at','last_used_at','revoked_at'],agent_requests:['key_id','request_key','fingerprint','response','status'],articles:['id','draft','published','status','version','updated_at'],article_revisions:['id','article_id','version','payload','action','created_at'],attachments:['id','article_id','name','mime','size','created_at'],sessions:['id','status','created_at','expires_at'],resident_profiles:['id','session_id','status','display_name','role','appearance_json','created_at','updated_at'],events:['id','code','title','date','status','questions','created_at'],participants:['id','event_id','profile_id','token','progress','attempts','completed_at','created_at']};
const uploaded=[];
try{await db.transaction(async q=>{await q('SELECT pg_advisory_xact_lock(20971114)');for(const table of Object.keys(columns)){const count=Number((await q(`SELECT COUNT(*) n FROM ${table}`)).rows[0].n);if(count)throw Error('目的資料庫已有資料，停止匯入以避免覆寫：'+table);}
 for(const [table,keys] of Object.entries(columns))for(const row of input.tables[table]||[]){if(table==='content_settings'&&row.key==='entry_url')continue;await q(`INSERT INTO ${table} (${keys.join(',')}) VALUES (${keys.map((_,i)=>'$'+(i+1)).join(',')})`,keys.map(k=>row[k]??null));}
 for(const f of input.tables.attachments||[]){if(!/^[a-f0-9-]{36}$/.test(f.id))throw Error('附件 ID 格式錯誤');const bytes=await readFile(path.join(input.attachmentsDirectory,f.id));if(bytes.length!==f.size)throw Error('附件大小不符');await store.set('files/'+f.id,bytes);uploaded.push('files/'+f.id);}
 await q("SELECT setval(pg_get_serial_sequence('article_revisions','id'),COALESCE(MAX(id),1),COUNT(*)>0) FROM article_revisions");});console.log('資料與附件匯入完成；舊本機網址未帶入雲端。');}catch(e){for(const key of uploaded)await store.delete(key);throw e;}
process.exit(0);

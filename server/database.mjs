import {getDatabase} from '@netlify/database';
let pool;
export function database(){
 pool??=getDatabase(process.env.DATABASE_URL?{connectionString:process.env.DATABASE_URL}:undefined).pool;
 return {query:(sql,args=[])=>pool.query(sql,args),transaction:async fn=>{const client=await pool.connect();try{await client.query('BEGIN');const result=await fn((sql,args=[])=>client.query(sql,args));await client.query('COMMIT');return result;}catch(e){await client.query('ROLLBACK');throw e;}finally{client.release();}}};
}

import {getStore} from '@netlify/blobs';
import seed from '../../webgl-prototype/education-seed.json' with {type:'json'};
import map from '../../webgl-prototype/server-assets/walkable-v22.json' with {type:'json'};
import {database} from '../../server/database.mjs';
import {createApp} from '../../server/app.mjs';
import {IslandWorld} from '../../server/world.mjs';
let app;
export default (req,context)=>{try{app??=createApp({db:database(),store:()=>getStore({name:'hope-attachments',consistency:'strong'}),seed,world:new IslandWorld(map)});return app(req,context);}catch(error){console.error('Hope initialization failed',{code:error.code||error.name});return Response.json({error:'雲端服務尚未完成設定，請稍後重試。'},{status:503,headers:{'Cache-Control':'no-store'}});}};
export const config={path:'/api/*'};

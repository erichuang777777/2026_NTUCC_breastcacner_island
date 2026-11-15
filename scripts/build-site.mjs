import {readFile,writeFile,mkdir,cp,readdir,stat,rm} from 'node:fs/promises';
import path from 'node:path';
const source=path.resolve('webgl-prototype'),out=path.resolve('public');await rm(out,{recursive:true,force:true});await mkdir(out,{recursive:true});
const files=(await readdir(source)).filter(name=>/\.(html|css|js|json)$/.test(name));
for(const name of files)await cp(path.join(source,name),path.join(out,name));
await cp(path.join(source,'vendor'),path.join(out,'vendor'),{recursive:true});
const assets=JSON.parse(await readFile('deployment/assets.json','utf8'));
for(const name of assets){if(name.includes('..')||path.isAbsolute(name))throw Error('Invalid asset path');const from=path.join(source,'assets',name),to=path.join(out,'assets',name);await stat(from);await mkdir(path.dirname(to),{recursive:true});await cp(from,to);}
for(const name of ['index.html','taiwan-study.html','mobile-controller.html','education-admin.html','resident-setup.html','event-join.html','character-study.html'])await stat(path.join(out,name));
await writeFile(path.join(out,'deployment.json'),JSON.stringify({builtAt:new Date().toISOString(),assets:assets.length,backend:'Netlify Functions + Postgres + Blobs'}));
console.log(`Built ${files.length} source files and ${assets.length} runtime assets in public/`);

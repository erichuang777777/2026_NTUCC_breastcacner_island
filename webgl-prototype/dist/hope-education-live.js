export async function loadPublishedEducation(stations){
 const response=await fetch('/api/education',{cache:'no-store'});if(!response.ok)throw Error('衛教服務暫時無法連線，請稍後重新開啟。');
 const data=await response.json();for(const station of stations)station.items=data.articles.filter(a=>a.stations.includes(station.id));return data.articles.length;
}
export const readingKey=(station,item)=>`${station.id}:read:${item.id}:v${item.version}`;
export function appendArticle(detail,item){
 const add=(tag,text,cls)=>{const el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;detail.append(el);return el;};
 add('h3',item.title);if(item.summary)add('p',item.summary,'education-copy');add('p',item.body,'education-copy');
 if(item.reviewer)add('p',`審閱：${item.reviewer}${item.author?' · 作者：'+item.author:''}`,'hint');
 if(item.references||item.source)add('p','參考資料：'+(item.references||item.source),'education-copy');
 for(const file of item.files||[]){const link=add('a',`${file.name} · ${Math.ceil(file.size/1024)} KB`);link.href='/api/files/'+file.id;link.target='_blank';link.rel='noopener noreferrer';link.style.display='block';link.style.margin='12px 0';}
}

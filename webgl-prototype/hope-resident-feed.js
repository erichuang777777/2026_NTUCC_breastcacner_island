// Push committed state to screens; polling remains a fallback for hosts without SSE.
export function connectResidentFeed(onState){
 let source=null,connected=false,busy=false,stopped=false,lastPoll=0,lastTime=0,updates=0;
 function accept(data){if(!Array.isArray(data?.profiles)||(data.serverTime||0)<lastTime)return;lastTime=data.serverTime||0;updates++;onState(data.profiles);}
 async function poll(){if(stopped||busy||document.hidden||performance.now()-lastPoll<(connected?5000:250))return;busy=true;lastPoll=performance.now();try{const response=await fetch('/api/events/residents',{cache:'no-store',signal:AbortSignal.timeout(3000)});if(response.ok)accept(await response.json());}catch{}finally{busy=false;}}
 function open(){if(stopped||document.hidden||source)return;if(typeof EventSource!=='function'){poll();return;}source=new EventSource('/api/events/resident-stream');source.onopen=()=>connected=true;source.onerror=()=>connected=false;source.addEventListener('residents',e=>{try{accept(JSON.parse(e.data));}catch{}});}
 function visibility(){if(document.hidden){source?.close();source=null;connected=false;}else{lastPoll=0;open();poll();}}
 const timer=setInterval(poll,250);document.addEventListener('visibilitychange',visibility);open();poll();
 return {audit:()=>({transport:connected?'push':'polling',updates}),dispose(){stopped=true;source?.close();clearInterval(timer);document.removeEventListener('visibilitychange',visibility);}};
}

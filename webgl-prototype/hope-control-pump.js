// One request in flight; intermediate pointer events collapse into the newest input.
// A release bypasses the rate limit and is sent as soon as the active request settles.
export function createControlPump({send,interval=60,now=()=>performance.now(),schedule=setTimeout,cancel=clearTimeout}){
 let busy=false,pending=false,urgent=false,timer=null,last=-Infinity;
 function plan(){
  if(busy||!pending)return;
  if(timer!==null){if(!urgent)return;cancel(timer);timer=null;}
  const wait=urgent?0:Math.max(0,interval-(now()-last));
  timer=schedule(flush,wait);
 }
 async function flush(){
  timer=null;if(busy||!pending)return;
  busy=true;pending=false;urgent=false;last=now();
  try{await send();}finally{busy=false;plan();}
 }
 return {request(immediate=false){pending=true;urgent||=immediate;plan();},audit:()=>({busy,pending,interval})};
}

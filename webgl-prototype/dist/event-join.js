import {showQuizFeedback,clearQuizFeedback,labelQuizChoice} from './hope-quiz-feedback.js?v=1';
const $=id=>document.getElementById(id),eventId=new URLSearchParams(location.search).get('event'),key=eventId?'hopeEventParticipant:'+eventId:'hopeEventParticipantV1';let token=sessionStorage.getItem(key),state=null,busy=false,answered=false,pendingAnswer=null;
function message(text,error=false){$('message').textContent=text;$('message').dataset.error=String(error);}
async function api(path,data){const r=await fetch('/api/'+path,{method:data?'POST':'GET',headers:{...(data?{'Content-Type':'application/json'}:{}),...(token?{Authorization:'Bearer '+token}:{})},body:data?JSON.stringify(data):undefined});const b=await r.json();if(!r.ok)throw Object.assign(Error(b.error||'目前無法連線，請再試一次。'),{status:r.status});return b;}
async function run(fn){if(busy)return;const previousFocus=document.activeElement;busy=true;document.querySelectorAll('button').forEach(b=>b.disabled=true);try{await fn();}catch(e){message(e.message,true);}finally{busy=false;document.querySelectorAll('button').forEach(b=>b.disabled=false);if(answered)document.querySelectorAll('#choices button').forEach(b=>b.disabled=true);if(!$('next').hidden)$('next').focus();else if(previousFocus?.isConnected&&previousFocus.getClientRects().length&&previousFocus.matches('button'))previousFocus.focus();}}
function render(){if(!state)return;answered=false;pendingAnswer=null;$('controller-link').href='mobile-controller.html?event='+encodeURIComponent(state.eventId);$('journey-intro').textContent='角色已加入希望島。三題都答對，就完成今天的希望旅程。';$('join-form').hidden=true;$('journey').hidden=false;$('event-name').textContent=state.title;$('welcome').textContent=`${state.name}，歡迎來到希望島。`;$('steps').replaceChildren();for(let i=0;i<state.total;i++){const li=document.createElement('li');li.textContent=`第 ${i+1} 題${i<state.progress?'・已完成':''}`;li.dataset.done=String(i<state.progress);$('steps').append(li);}$('choices').replaceChildren();clearQuizFeedback($('feedback'));$('next').hidden=true;$('complete-link').hidden=!state.completedAt;$('closed-note').textContent=state.active?'':'活動目前已結束，已完成的進度仍會保留。';
 if(state.completedAt){$('question-title').textContent='三題全數答對，恭喜通關！';$('feedback').textContent='你已完成今天的希望旅程。回到島上，為自己點亮一顆願望星星。';return;}
 $('question-title').textContent=state.question.prompt;if(!state.active)return;
 state.question.choices.forEach((choice,i)=>{const button=document.createElement('button');labelQuizChoice(button,choice,i);button.onclick=()=>run(async()=>{
 if(answered)return;
 if(!pendingAnswer||pendingAnswer.index!==state.progress||pendingAnswer.choice!==i)pendingAnswer={index:state.progress,choice:i,attemptId:crypto.randomUUID()};
 let result;try{result=await api('participant/answer',pendingAnswer);}catch(error){if(error.status===409){state=await api('participant');render();}throw error;}
 pendingAnswer=null;showQuizFeedback($('feedback'),result,button);
 if(!result.correct){message('可以再選一次；每次作答會納入活動統計。');return;}
 state=result;answered=true;$('next').textContent=result.completedAt?'查看通關紀錄':'下一題';$('next').hidden=false;message('答對了，進度已儲存。');
 });$('choices').append(button);});}

async function showActivities(){
 $('join-form').hidden=false;$('journey').hidden=true;
 if(eventId){location.replace('resident-setup.html?event='+encodeURIComponent(eventId));return;}
 try{const {events}=await api('events/today');$('event-options').replaceChildren();for(const event of events){const a=document.createElement('a');a.className='button';a.href='resident-setup.html?event='+event.id;a.textContent=event.title+' · 設定角色並參加';$('event-options').append(a);}if(!events.length)$('event-options').textContent='今天尚無開放活動。你仍可以自由探索島上衛教內容。';}catch(e){message(e.message,true);}
}
$('next').onclick=()=>{render();$('question-title').focus();};$('leave').onclick=()=>{if(!confirm('結束這位參加者在此裝置的操作，交給下一位嗎？'))return;if(state?.eventId)sessionStorage.removeItem('hopeEventParticipant:'+state.eventId);sessionStorage.removeItem(key);sessionStorage.removeItem('hopeEventParticipantV1');location.href=state?.eventId?'resident-setup.html?event='+state.eventId:'event-join.html';};
if(token)run(async()=>{try{state=await api('participant');if(eventId&&state.eventId!==eventId)throw Object.assign(Error('請重新設定角色加入這場活動。'),{status:401});render();}catch(e){if(e.status===401){sessionStorage.removeItem(key);token=null;await showActivities();}else throw e;}});else showActivities();

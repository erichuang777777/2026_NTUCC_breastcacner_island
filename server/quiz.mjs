import {randomUUID} from 'node:crypto';
import {requireValue as need} from './validation.mjs';
export async function recordAnswer({q,participant,event,input,progress,today}){
 const requestId=input.attemptId||randomUUID();need(typeof requestId==='string'&&/^[A-Za-z0-9_-]{16,100}$/.test(requestId),'作答識別碼錯誤。');
 const prior=(await q('SELECT question_index,choice,response FROM quiz_attempts WHERE participant_id=$1 AND request_id=$2',[participant.id,requestId])).rows[0];
 if(prior){need(prior.question_index===input.index&&prior.choice===input.choice,'重送的答案內容不同。',409);return JSON.parse(prior.response);}
 const questions=JSON.parse(event.questions),index=participant.progress;need(index<questions.length,'已完成全部題目。',409);need(input.index===index,'進度已更新，請重新載入。',409);need(Number.isInteger(input.choice)&&input.choice>=0&&input.choice<questions[index].choices.length,'請選擇答案。');
 const previous=(await q('SELECT id FROM quiz_attempts WHERE participant_id=$1 AND question_index=$2 LIMIT 1',[participant.id,index])).rows.length;
 const correct=input.choice===questions[index].answer,next=index+Number(correct),at=new Date().toISOString();
 const row=(await q('UPDATE participants SET progress=$1,attempts=attempts+1,completed_at=$2 WHERE id=$3 RETURNING *',[next,next===questions.length?at:null,participant.id])).rows[0];
 const response={...await progress(row,q,today),correct,answeredIndex:index,attemptId:requestId,explanation:correct?questions[index].explanation:'這次還沒答對，請再想一想。答錯不會扣分，可以繼續嘗試。',sources:correct?(questions[index].sources||[]):[]};
 await q('INSERT INTO quiz_attempts(participant_id,event_id,request_id,question_index,choice,correct,is_first,response,created_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)',[participant.id,event.id,requestId,index,input.choice,correct,!previous&&!!participant.quiz_tracking_started_at,JSON.stringify(response),at]);return response;
}
export async function quizStats(q,id){
 const event=(await q('SELECT id,title,questions FROM events WHERE id=$1',[id])).rows[0];need(event,'找不到活動。',404);
 const people=(await q('SELECT COUNT(*) joined,COUNT(completed_at) completed,COALESCE(SUM(attempts),0) total FROM participants WHERE event_id=$1',[id])).rows[0];
 const rows=(await q('SELECT question_index,COUNT(*) attempts,COUNT(DISTINCT participant_id) people,COUNT(*) FILTER(WHERE correct) correct,COUNT(*) FILTER(WHERE is_first) first_count,COUNT(*) FILTER(WHERE is_first AND correct) first_correct FROM quiz_attempts WHERE event_id=$1 GROUP BY question_index',[id])).rows;
 const choices=(await q('SELECT question_index,choice,COUNT(*) n FROM quiz_attempts WHERE event_id=$1 GROUP BY question_index,choice',[id])).rows;
 const rate=(n,d)=>d?Math.round(n/d*1000)/10:null;
 const questions=JSON.parse(event.questions).map((item,index)=>{const r=rows.find(r=>r.question_index===index)||{},attempts=Number(r.attempts||0),correct=Number(r.correct||0),firstCount=Number(r.first_count||0),firstCorrect=Number(r.first_correct||0);return {index,prompt:item.prompt,attempts,people:Number(r.people||0),correct,accuracy:rate(correct,attempts),firstCount,firstCorrect,firstAccuracy:rate(firstCorrect,firstCount),choices:item.choices.map((text,choice)=>({label:String.fromCharCode(65+choice),text,correct:choice===item.answer,count:Number(choices.find(c=>c.question_index===index&&c.choice===choice)?.n||0)}))};});
 const sum=key=>questions.reduce((n,q)=>n+q[key],0),attempts=sum('attempts'),correct=sum('correct'),firstCount=sum('firstCount'),firstCorrect=sum('firstCorrect');
 return {eventId:id,title:event.title,joined:Number(people.joined),completed:Number(people.completed),completionRate:rate(Number(people.completed),Number(people.joined)),attempts,correct,accuracy:rate(correct,attempts),firstCount,firstCorrect,firstAccuracy:rate(firstCorrect,firstCount),untrackedAttempts:Math.max(0,Number(people.total)-attempts),questions};
}

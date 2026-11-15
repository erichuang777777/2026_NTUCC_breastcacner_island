export function clearQuizFeedback(container){container.replaceChildren();container.removeAttribute('data-result');}
export function showQuizFeedback(container,{correct,explanation,sources=[]},selected){
 clearQuizFeedback(container);container.dataset.result=correct?'correct':'incorrect';
 const result=document.createElement('div');result.className='quiz-feedback-result';result.dataset.result=container.dataset.result;
 const icon=document.createElement('span');icon.className='quiz-feedback-icon';icon.setAttribute('aria-hidden','true');
 if(correct){const check=document.createElement('span');check.className='t-success-check';check.dataset.state='out';check.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l4 4L19 6" /></svg>';icon.append(check);result.append(icon);}
 else{icon.textContent='×';result.append(icon);}
 const copy=document.createElement('div');copy.className='quiz-feedback-copy';const title=document.createElement('strong');title.textContent=correct?'答對了！希望再前進一步':'還沒答對，再試一次';const p=document.createElement('p');p.textContent=explanation;copy.append(title,p);
 for(const source of sources){const a=document.createElement('a');a.href=source.url;a.textContent=source.label;a.target='_blank';a.rel='noopener noreferrer';copy.append(a);}result.append(copy);container.append(result);
 if(selected){selected.dataset.answer=correct?'correct':'incorrect';if(!correct){selected.classList.add('t-input','is-error');selected.classList.remove('is-shaking');void selected.offsetWidth;selected.classList.add('is-shaking');const cs=getComputedStyle(document.documentElement),ms=(n,f)=>parseFloat(cs.getPropertyValue(n))||f;setTimeout(()=>selected.classList.remove('is-shaking'),ms('--shake-dur-a',80)*2+ms('--shake-dur-b',60)*2+20);}}
 const check=result.querySelector('.t-success-check');if(check){const path=check.querySelector('path'),length=Math.ceil(path.getTotalLength());path.style.strokeDasharray=String(length);path.style.strokeDashoffset=String(length);void check.offsetWidth;check.dataset.state='in';}
}
export function labelQuizChoice(button,text,index){const label=document.createElement('span');label.className='quiz-option-label';label.textContent=String.fromCharCode(65+index);const copy=document.createElement('span');copy.textContent=text;button.append(label,copy);}

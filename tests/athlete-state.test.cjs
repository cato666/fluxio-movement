const {test}=require('node:test');
const assert=require('node:assert/strict');
const Athlete=require('../app/static/athlete-state.js');
for(const [reviews,state,label] of [
  [[], 'NONE','Solicitar revisión a un coach'],
  [[{status:'PENDING'}],'WAITING','Esperando revisión del coach'],
  [[{status:'IN_REVIEW'}],'WAITING','Esperando revisión del coach'],
  [[{status:'COMPLETED'},{status:'PENDING'}],'AVAILABLE','Ver revisión del coach'],
]) test(`contextual CTA ${state} ${reviews[0]?.status||'none'}`,()=>{
  const result=Athlete.reviewAction({id:'a',coach_reviews:reviews});assert.equal(result.state,state);assert.equal(result.label,label);
  if(state==='AVAILABLE')assert.equal(result.badge,'Revisión disponible');
});
test('completed feedback takes priority even without list metadata',()=>assert.equal(Athlete.reviewAction({id:'a',completed_coach_reviews:[{}]}).state,'AVAILABLE'));
test('objective remains required including whitespace',()=>{const fields={exercise:'Sentadilla',objective:'  ',view:'side',file:{name:'video.mp4'}};assert.deepEqual(Athlete.requirements(fields).filter(r=>!r.ready).map(r=>r.label),['Escribe tu objetivo']);fields.objective='Profundidad';assert.ok(Athlete.requirements(fields).every(r=>r.ready));});
test('file requirement mirrors existing backend formats rather than accepting every video MIME type',()=>{for(const name of ['video.MP4','video.mov','video.m4v','video.avi'])assert.equal(Athlete.requirements({file:{name}})[3].ready,true);assert.equal(Athlete.requirements({file:{name:'video.webm'}})[3].ready,false);});
test('processing retries reads after network loss and 503 without claiming FAILED',async()=>{
  for(const failure of [new TypeError('offline'),Object.assign(Error('unavailable'),{status:503})]){
    const timers=[],data=[],errors=[];let calls=0;
    const poll=Athlete.createPoller({read:async()=>{if(++calls===1)throw failure;return{status:'COMPLETED'};},onData:i=>data.push(i),onError:e=>errors.push(e),schedule:(fn,delay)=>{timers.push({fn,delay});return timers.length;},cancel(){}});
    await poll.retry();assert.equal(data.length,0);assert.equal(errors.length,1);assert.equal(timers[0].delay,3000);
    await timers[0].fn();assert.equal(data[0].status,'COMPLETED');assert.equal(calls,2);poll.stop();
  }
});
test('auth/permission/not-found errors stop automatic retries',async()=>{for(const status of [401,403,404]){let scheduled=0;const poll=Athlete.createPoller({read:async()=>{throw Object.assign(Error(),{status});},onData(){},onError(){},schedule(){scheduled++;},cancel(){}});await poll.retry();assert.equal(scheduled,0);}});
test('double retry is serialized and stopped responses cannot render',async()=>{let resolve,calls=0,rendered=0;const pending=new Promise(r=>resolve=r);const poll=Athlete.createPoller({read:()=>{calls++;return pending;},onData(){rendered++;},onError(){},schedule(){},cancel(){}});const first=poll.retry();await poll.retry();assert.equal(calls,1);poll.stop();resolve({status:'PROCESSING'});await first;assert.equal(rendered,0);});
test('real processing failure is terminal, waiting coach continues read-only refresh',()=>{assert.equal(Athlete.refreshDelay({status:'FAILED'}),null);assert.equal(Athlete.refreshDelay({status:'COMPLETED',coach_reviews:[{status:'PENDING'}]}),15000);assert.equal(Athlete.refreshDelay({status:'COMPLETED',coach_reviews:[{status:'COMPLETED'}]}),null);});

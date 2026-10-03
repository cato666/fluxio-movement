/* Record locally, review, then explicitly request an editable transcript. */
window.createTrainingVoice = function ({container, source, onBusy, onText}) {
  const panel=document.createElement('section');panel.className='training-voice';
  function button(text) {const node=document.createElement('button');node.type='button';node.textContent=text;panel.append(node);return node;}
  const record=button('Dictar entrenamiento');
  const stop=button('Terminar grabación');
  const discard=button('Descartar grabación');
  const send=button('Transcribir audio');
  const player=document.createElement('audio');player.controls=true;player.setAttribute('aria-label','Escuchar tu grabación');panel.append(player);
  const status=document.createElement('p');status.setAttribute('role','status');panel.append(status);
  const hint=document.createElement('p');hint.className='training-hint';hint.textContent='Graba hasta 3 minutos. Al transcribir, el audio se procesa con IA. Revisa el texto antes de interpretar el WOD.';panel.append(hint);
  container.append(panel);
  let recorder=null,stream=null,blob=null,url=null,timer=null,chunks=[],size=0;
  let active=false,pending=false,external=false,cancelled=false,disposed=false,started=0;
  const supported=!!(window.isSecureContext && navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
  function sync() {
    record.hidden=active;stop.hidden=!active;discard.hidden=!active&&!blob;send.hidden=!blob;player.hidden=!blob;
    record.disabled=!supported||pending||external;stop.disabled=pending||external;
    discard.disabled=pending||external;send.disabled=pending||external;
  }
  function release() {clearInterval(timer);timer=null;stream?.getTracks().forEach(track=>track.stop());stream=null;}
  function clearAudio() {blob=null;if(url)URL.revokeObjectURL(url);url=null;player.removeAttribute('src');player.load();}
  function finish() {if(recorder?.state==='recording')recorder.stop();release();}
  record.onclick=async()=>{
    if(pending||external||active)return;
    pending=true;onBusy(true);status.textContent='Solicitando acceso al micrófono…';sync();
    try {
      stream=await navigator.mediaDevices.getUserMedia({audio:true});
      if(disposed){release();return;}
      const mime=['audio/webm;codecs=opus','audio/mp4','audio/webm'].find(type=>MediaRecorder.isTypeSupported(type));
      recorder=mime?new MediaRecorder(stream,{mimeType:mime}):new MediaRecorder(stream);
      chunks=[];size=0;cancelled=false;
      recorder.ondataavailable=event=>{if(event.data.size){chunks.push(event.data);size+=event.data.size;if(size>8*1024*1024){cancelled=true;finish();status.textContent='La grabación supera 8 MB. Graba una descripción más breve.';}}};
      recorder.onstop=()=>{
        active=false;release();
        if(!cancelled&&!disposed&&size){clearAudio();blob=new Blob(chunks,{type:recorder.mimeType||'audio/webm'});url=URL.createObjectURL(blob);player.src=url;status.textContent='Grabación lista. Escúchala o transcribe para revisar el texto.';}
        else if(!cancelled&&!disposed)status.textContent='No se capturó audio. Intenta grabar nuevamente.';
        chunks=[];onBusy(false);sync();
      };
      recorder.onerror=()=>{cancelled=true;finish();active=false;release();onBusy(false);status.textContent='La grabación se interrumpió. Puedes reintentar o escribir.';sync();};
      clearAudio();recorder.start(1000);active=true;started=Date.now();status.textContent='Grabando · 0:00';
      timer=setInterval(()=>{const seconds=Math.floor((Date.now()-started)/1000);status.textContent=`Grabando · ${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;if(seconds>=180)finish();},500);
    } catch(error) {
      release();onBusy(false);status.textContent=error.name==='NotAllowedError'?'No se permitió el micrófono. Habilítalo en tu navegador o escribe el entrenamiento.':'No se pudo abrir el micrófono. Revisa que esté conectado o escribe el entrenamiento.';
    } finally {pending=false;if(!active)onBusy(false);sync();}
  };
  stop.onclick=()=>finish();
  discard.onclick=()=>{cancelled=true;if(active)finish();clearAudio();status.textContent='Grabación descartada. Tu texto se conserva.';sync();};
  send.onclick=async()=>{
    if(!blob||pending||external)return;
    pending=true;onBusy(true);status.textContent='Transcribiendo audio…';sync();
    try {
      const body=new FormData();body.append('file',blob,blob.type.includes('mp4')?'recording.mp4':'recording.webm');
      const response=await fetch('/api/training-sessions/transcribe',{method:'POST',body});const data=await response.json();
      if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'No se pudo transcribir. Reintenta.');
      if(typeof data.text!=='string'||!data.text.trim())throw new Error('No se obtuvo texto legible. Graba nuevamente o escribe el entrenamiento.');
      const text=[source.value.trim(),data.text].filter(Boolean).join('\n\n');
      if(text.length>12000)throw new Error('El texto completo supera el límite. Acorta tu descripción antes de reintentar.');
      source.value=text;onText();clearAudio();status.textContent='Texto agregado. Corrige nombres, cargas o repeticiones antes de interpretar.';
    } catch(error){status.textContent=error.message+' La grabación se conserva para reintentar.';}
    finally{pending=false;onBusy(false);sync();}
  };
  function warn(event){if(active||blob){event.preventDefault();event.returnValue='';}}
  window.addEventListener('beforeunload',warn);
  function cleanup(){disposed=true;cancelled=true;finish();release();clearAudio();window.removeEventListener('beforeunload',warn);}
  window.addEventListener('pagehide',cleanup,{once:true});
  if(!supported)status.textContent='Tu navegador no permite grabar aquí. Usa HTTPS o localhost, o escribe el entrenamiento.';
  sync();
  return {setExternalBusy(value){external=value;sync();},cleanup};
};

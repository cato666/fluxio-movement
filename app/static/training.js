/* Training log: independent sessions, explicit confirmation, optional videos. */
window.setupTraining = async function (identifier) {
  const root = document.getElementById('training-view');
  const make = (tag, text, className) => {
    const node = document.createElement(tag); node.textContent = text || '';
    if (className) node.className = className;
    return node;
  };
  const link = (text, href) => { const node = make('a', text); node.href = href; return node; };
  const api = async (url, options) => {
    const response = await fetch(url, options); const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Revisa los campos e inténtalo nuevamente.');
    return data;
  };
  root.replaceChildren();
  const header = make('header', '', 'training-header');
  header.append(make('h1', identifier ? 'Tu entrenamiento' : 'Mi bitácora'));
  header.append(link(identifier ? 'Volver a la bitácora' : 'Registrar entrenamiento', identifier ? '/training' : '/training/new'));
  root.append(header);
  const status = make('p', 'Cargando…', 'training-status'); status.setAttribute('role', 'status'); root.append(status);
  try {
    if (!identifier) {
      const { items } = await api('/api/training-sessions'); status.textContent = '';
      if (!items.length) {
        root.append(make('h2', 'Tu próximo entrenamiento empieza aquí'), make('p', 'Registra el WOD y cómo te fue. Puedes agregar un video después.'));
      }
      for (const item of items) {
        const row = make('article', '', 'training-entry');
        row.append(make('p', new Intl.DateTimeFormat('es-CL', {dateStyle: 'long'}).format(new Date(item.trained_on + 'T12:00:00'))));
        row.append(link(item.title, '/training/' + item.id), make('p', item.result_text || 'Resultado sin registrar'));
        if (item.rpe !== null) row.append(make('p', `Esfuerzo ${item.rpe}/10`));
        root.append(row);
      }
      return;
    }
    const editing = identifier !== 'new';
    let dirty = false;
    root.addEventListener('input', () => { dirty = true; });
    window.addEventListener('beforeunload', event => {
      if (dirty) { event.preventDefault(); event.returnValue = ''; }
    });
    const data = editing ? await api('/api/training-sessions/' + identifier) : {};
    const now = new Date();
    const today = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
    const layout = make('div', '', 'training-layout');
    const conversation = make('section', '', 'training-conversation');
    conversation.append(make('h2', '¿Qué entrenaste hoy?'), make('p', 'Sube la pizarra o escribe el WOD y cómo te fue. Luego confirma la ficha.'));
    const messages = make('div', '', 'training-messages'); messages.setAttribute('aria-live', 'polite');
    const source = make('textarea'); source.rows = 6; source.maxLength = 12000; source.value = data.source_text || '';
    source.placeholder = 'Ej.: AMRAP de 12 minutos: 10 thrusters y 12 burpees.'; source.setAttribute('aria-label', 'Descripción del entrenamiento');
    let imageId = data.source_image_id || null;
    const photoLabel = make('label', 'Foto de la pizarra · opcional');
    const photo = make('input'); photo.type = 'file'; photo.accept = 'image/jpeg,image/png,image/webp';
    photoLabel.append(photo);
    const preview = make('img'); preview.alt = 'Foto de la pizarra'; preview.className = 'training-photo'; preview.hidden = !imageId;
    if (imageId) preview.src = '/api/training-sessions/images/' + imageId;
    const removePhoto = make('button', 'Quitar foto'); removePhoto.type = 'button'; removePhoto.hidden = !imageId;
    removePhoto.onclick = () => { imageId = null; photo.value = ''; preview.removeAttribute('src'); preview.hidden = true; removePhoto.hidden = true; dirty = true; };
    const prepare = make('button', 'Interpretar WOD'); prepare.type = 'button';
    const manual = make('button', 'Completar manualmente'); manual.type = 'button';
    conversation.append(messages, photoLabel, preview, removePhoto, source, prepare, manual, make('p', 'Al interpretar, tu descripción y la foto se procesan con IA. Revisa los datos antes de guardar. Puedes añadir aclaraciones al texto y volver a interpretar; se reemplazará la ficha.', 'training-hint'));
    const form = make('form', '', 'training-form'); form.append(make('h2', 'Confirma tu sesión'));
    const controls = {};
    function field(name, label, type, value, required = false, max = 4000) {
      const group = make('label', label);
      const input = make(type === 'textarea' ? 'textarea' : 'input');
      if (type !== 'textarea') input.type = type;
      else input.rows = name === 'workout' ? 7 : 3;
      input.name = name; input.value = value ?? ''; input.required = required;
      if (['text', 'textarea'].includes(type)) input.maxLength = max;
      group.append(input); form.append(group); controls[name] = input; return input;
    }
    field('trained_on', 'Fecha del entrenamiento', 'date', data.trained_on || today, true);
    field('title', 'Nombre', 'text', data.title, true, 160);
    field('workout', 'Entrenamiento programado · ejercicios, series, repeticiones y cargas', 'textarea', data.workout, true, 12000);
    field('result_text', 'Tu resultado · tiempo, rondas o series realizadas', 'textarea', data.result_text);
    field('adaptations', 'Cargas utilizadas y adaptaciones · opcional', 'textarea', data.adaptations);
    const rpe = field('rpe', 'Esfuerzo percibido · opcional (1 mínimo, 10 máximo)', 'number', data.rpe);
    rpe.min = 1; rpe.max = 10; rpe.step = 1;
    let blocks = data.blocks || [];
    let openBlock = -1;
    const blockArea = make('section', '', 'training-blocks');
    const formatNames = {strength:'Fuerza',for_time:'Por tiempo',amrap:'AMRAP',emom:'EMOM',other:'Otro'};
    const blockSummary = () => blocks.map(block => `${block.title} · ${formatNames[block.format]}\n${block.prescription}\n${block.movements.map(movement=>`${movement.name}: ${movement.prescription}`).join('\n')}`).join('\n\n');
    function updateBlocks() {
      dirty = true; controls.workout.value = blockSummary();
      blockArea.querySelectorAll('details').forEach((disclosure,index)=>{
        const block=blocks[index];if(!block)return;
        disclosure.querySelector('summary').firstChild.textContent=`${block.title || 'Nuevo bloque'} · ${formatNames[block.format]} · Editar`;
        disclosure.querySelector('.training-block-preview').textContent=[block.prescription,...block.movements.map(m=>`${m.name}: ${m.prescription}`)].filter(Boolean).join('\n');
      });
    }
    function renderBlocks() {
      blockArea.replaceChildren();
      blockArea.append(make('h3', 'Bloques del entrenamiento'));
      blocks.forEach((block, index) => {
        const disclosure=make('details'); disclosure.open=index===openBlock;
        const summary=make('summary', `${block.title || 'Nuevo bloque'} · ${formatNames[block.format]} · Editar`);
        summary.append(make('span', [block.prescription,...block.movements.map(m=>`${m.name}: ${m.prescription}`)].filter(Boolean).join('\n'), 'training-block-preview'));
        disclosure.append(summary);
        const group = make('fieldset'); group.append(make('legend', `Bloque ${index+1}`));
        function edit(label, value, change, multiline = false, limit = 500, required = false) {
          const wrapper = make('label', label); const input = make(multiline ? 'textarea' : 'input');
          input.value = value; input.maxLength = limit; input.required=required; if (multiline) input.rows = 2;
          input.oninput = () => { change(input.value); updateBlocks(); }; wrapper.append(input); group.append(wrapper);
        }
        edit('Nombre del bloque', block.title, value=>{block.title=value}, false, 160, true);
        const formatLabel = make('label','Formato'); const format = make('select');
        for (const [value,text] of Object.entries(formatNames)) { const option=make('option',text); option.value=value; format.append(option); }
        format.value=block.format; format.onchange=()=>{block.format=format.value;updateBlocks()}; formatLabel.append(format);group.append(formatLabel);
        edit('Duración, rondas y esquema',block.prescription,value=>{block.prescription=value},true,2000);
        block.movements.forEach((movement,movementIndex)=>{
          edit('Ejercicio',movement.name,value=>{movement.name=value},false,100,true);
          edit('Series, repeticiones y carga programada',movement.prescription,value=>{movement.prescription=value});
          const removeMovement=make('button','Quitar ejercicio');removeMovement.type='button';
          removeMovement.onclick=()=>{openBlock=index;block.movements.splice(movementIndex,1);updateBlocks();renderBlocks()};group.append(removeMovement);
        });
        const addMovement=make('button','Agregar ejercicio');addMovement.type='button';
        addMovement.onclick=()=>{if(block.movements.length>=30)return;openBlock=index;block.movements.push({name:'',prescription:''});updateBlocks();renderBlocks()};group.append(addMovement);
        const remove=make('button','Quitar bloque'); remove.type='button';remove.onclick=()=>{blocks.splice(index,1);updateBlocks();renderBlocks()};group.append(remove);
        disclosure.append(group); blockArea.append(disclosure);
      });
      const addBlock=make('button','Agregar bloque');addBlock.type='button';
      addBlock.onclick=()=>{if(blocks.length>=12)return;openBlock=blocks.length;blocks.push({title:'',format:'other',prescription:'',movements:[]});updateBlocks();renderBlocks()};blockArea.append(addBlock);
    }
    form.insertBefore(blockArea, controls.result_text.parentElement); renderBlocks();
    controls.workout.addEventListener('input',()=>{if(blocks.length){blocks=[];renderBlocks();status.textContent='Conservé tu edición libre; los bloques anteriores se quitaron para evitar datos contradictorios.'}});
    manual.onclick = () => {
      if (!source.value.trim()) { source.focus(); return; }
      if (!controls.workout.value.trim()) controls.workout.value = source.value.trim();
      messages.replaceChildren(make('p', source.value, 'training-message'), make('p', 'Conservé tu descripción. Separa la programación de tu resultado y confirma los datos.'));
      controls.title.focus();
    };
    let busy = false;
    let voice;
    function processing(value, fromVoice = false) {
      busy = value;
      for (const input of root.querySelectorAll('input, textarea, select, button')) input.disabled = value;
      voice?.setExternalBusy(fromVoice ? false : value);
    }
    voice=window.createTrainingVoice({container:conversation,source,onBusy:value=>processing(value,true),onText:()=>{dirty=true;source.dispatchEvent(new Event('input',{bubbles:true}));}});
    conversation.insertBefore(conversation.querySelector('.training-voice'),source);
    photo.onchange = async () => {
      const file = photo.files[0]; if (!file) return;
      if (file.size > 8*1024*1024) { status.textContent = 'La imagen supera 8 MB. Elige una más pequeña.'; photo.value=''; return; }
      processing(true); status.textContent='Guardando foto…';
      try {
        const body = new FormData(); body.append('file',file);
        const uploaded=await api('/api/training-sessions/images',{method:'POST',body});
        imageId=uploaded.id; preview.src=uploaded.url; preview.hidden=false; removePhoto.hidden=false; dirty=true; status.textContent='Foto lista. Puedes añadir tu resultado e interpretar el WOD.';
      } catch(error) { status.textContent=error.message; photo.value=''; }
      finally { processing(false); }
    };
    prepare.onclick = async () => {
      if (busy) return;
      if (!source.value.trim() && !imageId) { status.textContent='Escribe el WOD o agrega una foto de la pizarra.'; source.focus(); return; }
      processing(true); status.textContent='Interpretando el entrenamiento…';
      try {
        const draft=await api('/api/training-sessions/interpret',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:source.value,image_id:imageId})});
        for (const key of ['title','workout','result_text','adaptations','rpe']) controls[key].value=draft[key] ?? '';
        blocks=draft.blocks;renderBlocks();dirty=true;
        messages.replaceChildren(make('p', source.value || 'Foto de la pizarra', 'training-message'),make('p','Preparé un borrador. Revisa la programación y tu resultado.'));
        if (draft.questions.length) {
          messages.append(make('h3','Por confirmar'));
          const list=make('ul'); draft.questions.forEach(question=>list.append(make('li',question)));messages.append(list,make('p','Añade tus aclaraciones al texto y vuelve a interpretar, o corrige la ficha directamente.'));
        }
        status.textContent='Ficha lista para revisar. Todavía no se ha guardado la sesión.';
      } catch(error) { status.textContent=error.message; }
      finally { processing(false); }
    };
    const videos = make('fieldset'); videos.append(make('legend', 'Videos · opcional'));
    const linked = make('div'); videos.append(linked);
    let videoLinks = data.video_links || [];
    const renderLinks = () => {
      linked.replaceChildren();
      videoLinks.forEach((item, index) => {
        const row = make('div', '', 'training-video');
        row.append(link(`${item.movement}${item.context ? ' · ' + item.context : ''}`, '/analyses/' + item.analysis_id));
        const remove = make('button', 'Desvincular'); remove.type = 'button';
        remove.onclick = () => { dirty = true; videoLinks.splice(index, 1); renderLinks(); }; row.append(remove); linked.append(row);
      });
    };
    renderLinks();
    const choose = make('button', 'Vincular análisis existente'); choose.type = 'button'; videos.append(choose);
    choose.onclick = async () => {
      choose.disabled = true;
      try {
        const {items} = await api('/api/analyses');
        if (!items.length) { status.textContent = 'Todavía no tienes análisis para vincular. Puedes guardar sin video.'; choose.disabled = false; return; }
        const select = make('select'); select.setAttribute('aria-label', 'Selecciona un análisis');
        for (const item of items) { const option = make('option', `${item.exercise} · ${new Date(item.created_at).toLocaleDateString('es-CL')}`); option.value = item.id; select.append(option); }
        const movement = make('input'); movement.placeholder = 'Movimiento, ej.: thrusters'; movement.maxLength = 100; movement.setAttribute('aria-label', 'Movimiento del video');
        const context = make('input'); context.placeholder = 'Serie o ronda · opcional'; context.maxLength = 160; context.setAttribute('aria-label', 'Serie o ronda');
        const add = make('button', 'Vincular'); add.type = 'button';
        add.onclick = () => {
          if (!movement.value.trim()) { movement.focus(); return; }
          if (videoLinks.length >= 30) { status.textContent = 'Puedes vincular hasta 30 videos por sesión.'; return; }
          dirty = true; videoLinks.push({analysis_id: select.value, movement: movement.value.trim(), context: context.value.trim()}); renderLinks(); movement.value = ''; context.value = '';
        };
        videos.append(select, movement, context, add); choose.hidden = true;
      } catch (error) { status.textContent = error.message; choose.disabled = false; }
    };
    form.append(videos);
    const save = make('button', editing ? 'Guardar cambios' : 'Guardar sesión'); save.type = 'submit'; form.append(save);
    form.onsubmit = async (event) => {
      event.preventDefault(); if (busy) return;
      save.disabled = true; status.textContent = 'Guardando…';
      const payload = Object.fromEntries(Object.entries(controls).map(([key, input]) => [key, input.value.trim()]));
      payload.rpe = payload.rpe === '' ? null : Number(payload.rpe);
      payload.source_text = source.value; payload.video_links = videoLinks; payload.blocks=blocks; payload.source_image_id=imageId;
      try {
        await api('/api/training-sessions' + (editing ? '/' + identifier : ''), {method: editing ? 'PUT' : 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)});
        dirty = false; window.location.assign('/training');
      } catch (error) { status.textContent = `${error.message} Tu borrador se conserva en esta pantalla.`; save.disabled = false; }
    };
    layout.append(conversation, form); root.append(layout); status.textContent = '';
  } catch (error) {
    status.textContent = error.message;
    const retry = make('button', 'Reintentar'); retry.onclick = () => window.setupTraining(identifier); root.append(retry);
  }
};

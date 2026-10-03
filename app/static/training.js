/* Training log: independent sessions, explicit confirmation, optional videos. */
window.setupTraining = async function (identifier) {
  const root = document.getElementById('training-view');
  root.trainingCleanup?.();
  const make = (tag, text, className) => {
    const node = document.createElement(tag); node.textContent = text || '';
    if (className) node.className = className;
    return node;
  };
  const link = (text, href) => { const node = make('a', text); node.href = href; return node; };
  const formats = {strength:'Fuerza',for_time:'Por tiempo',amrap:'AMRAP',emom:'EMOM',other:'Otro'};
  const calendarDate = value => new Date(value + 'T12:00:00');
  const dateLabel = value => new Intl.DateTimeFormat('es-CL', {dateStyle:'long'}).format(calendarDate(value));
  const localISO = date => `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  function displayName(item) {
    const dated = new Intl.DateTimeFormat('es-CL', {weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(calendarDate(item.trained_on));
    const title = (item.title || '').trim();
    return [dated,dateLabel(item.trained_on)].some(value => value.toLocaleLowerCase('es-CL') === title.toLocaleLowerCase('es-CL'))
      ? (item.blocks?.map(block => block.title).filter(Boolean).join(' · ') || 'Entrenamiento') : title;
  }
  function thumbnail(imageId, sessionId, fullPhoto = false) {
    const url = '/api/training-sessions/images/' + imageId;
    const node = link('', fullPhoto ? url : '/training/' + sessionId);
    node.className = 'training-thumbnail' + (fullPhoto ? ' training-thumbnail-note' : '');
    node.setAttribute('aria-label', fullPhoto ? 'Ver foto de la pizarra en otra pestaña' : 'Abrir entrenamiento con foto de la pizarra');
    if (fullPhoto) { node.target = '_blank'; node.rel = 'noopener'; }
    const image = make('img'); image.src = url; image.alt = 'Pizarra del entrenamiento'; image.width = 96; image.height = 72; image.loading = 'lazy'; image.decoding = 'async';
    image.onerror = () => {
      node.replaceChildren(make('span', 'Imagen no disponible'));
      node.setAttribute('aria-label', 'Imagen no disponible');
      if (fullPhoto) { node.removeAttribute('href'); node.removeAttribute('target'); }
    };
    node.append(image); return node;
  }
  const api = async (url, options) => {
    let response;
    try { response = await fetch(url, options); }
    catch { throw new Error('No pudimos conectar. Revisa tu conexión e inténtalo nuevamente.'); }
    let data;
    try { data = await response.json(); }
    catch { throw new Error('No pudimos leer la respuesta. Inténtalo nuevamente.'); }
    if (response.status === 401) throw new Error('Tu sesión expiró. Vuelve a iniciar sesión para continuar.');
    if (response.status === 403) throw new Error('No tienes permiso para esta acción. Puedes volver a tu bitácora.');
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Revisa los campos e inténtalo nuevamente.');
    return data;
  };
  root.replaceChildren();
  const header = make('header', '', 'training-header');
  header.append(make('h1', identifier === 'new' ? 'Registrar entrenamiento' : identifier ? 'Tu entrenamiento' : 'Mi bitácora'));
  header.append(link(identifier ? 'Volver a la bitácora' : 'Registrar entrenamiento', identifier ? '/training' : '/training/new'));
  root.append(header);
  const status = make('p', 'Cargando…', 'training-status'); status.setAttribute('role', 'status'); root.append(status);
  status.setAttribute('aria-atomic', 'true');
  const notify = (message, error = false) => {
    status.textContent = message; status.classList.toggle('is-error', error);
    if (message.includes('Tu sesión expiró.')) {
      const login = link('Iniciar sesión en otra pestaña', '/login?next=' + encodeURIComponent(window.location.pathname));
      login.target = '_blank'; login.rel = 'noopener'; status.append(document.createTextNode(' '), login);
    }
  };
  function deleteAction(item) {
    const button = make('button', '', 'secondary-button training-delete'); button.type = 'button';
    button.setAttribute('aria-label', 'Eliminar entrenamiento');
    function renderDelete() {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox','0 0 24 24'); svg.setAttribute('aria-hidden','true');
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d','M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6');
      svg.append(path); button.replaceChildren(svg, make('span', 'Eliminar'));
    }
    renderDelete();
    let deleting = false;
    button.onclick = async () => {
      if (deleting || !window.confirm(`¿Eliminar «${item.title}» del ${dateLabel(item.trained_on)}? Esta acción no se puede deshacer. Los análisis de video vinculados se conservan.`)) return;
      deleting = true; button.disabled = true; button.textContent = 'Eliminando…'; button.setAttribute('aria-label', 'Eliminando entrenamiento'); notify('Eliminando el entrenamiento…');
      try {
        await api('/api/training-sessions/' + item.id, {method:'DELETE'});
        setFlash('Entrenamiento eliminado de tu bitácora.');
        root.trainingCleanup?.();
        window.location.assign('/training');
      } catch (error) {
        notify(`${error.message} El entrenamiento sigue en esta pantalla; puedes reintentar.`, true);
        deleting = false; button.disabled = false; button.setAttribute('aria-label', 'Eliminar entrenamiento'); renderDelete();
      }
    };
    return button;
  }
  try {
    if (!identifier) {
      const { items } = await api('/api/training-sessions'); status.textContent = '';
      const flash = takeFlash(); if (flash) notify(flash);
      if (!items.length) {
        const empty = make('section', '', 'training-empty');
        const start = link('Registrar mi primer entrenamiento', '/training/new'); start.className = 'button-link';
        empty.append(make('h2', 'Guarda cómo te fue hoy'), make('p', 'Una foto de la pizarra, unas palabras o tu voz. Después revisas el WOD y tu resultado.'), start); root.append(empty);
      }
      const journal = make('div', '', 'training-journal');
      const monday = new Date(); monday.setHours(12,0,0,0); monday.setDate(monday.getDate() - (monday.getDay()+6)%7);
      const sunday = new Date(monday); sunday.setDate(sunday.getDate()+6);
      const week = items.filter(item => item.trained_on >= localISO(monday) && item.trained_on <= localISO(sunday));
      const weekly = make('section', '', 'training-week');
      weekly.append(make('h2', 'Esta semana'), make('p', `${dateLabel(localISO(monday))} — ${dateLabel(localISO(sunday))}`, 'training-hint'));
      const days = new Set(week.map(item => item.trained_on)).size;
      weekly.append(make('p', `${week.length} ${week.length === 1 ? 'entrenamiento registrado' : 'entrenamientos registrados'} · ${days} ${days === 1 ? 'día activo' : 'días activos'}`, 'training-week-count'));
      if (!week.length) weekly.append(make('p', 'Tu próximo registro aparecerá aquí.', 'training-hint'));
      if (items.length >= 200) weekly.append(make('p', 'Resumen de los registros cargados; puede haber registros anteriores fuera de esta lista.', 'training-hint'));
      journal.append(weekly); root.insertBefore(journal, root.querySelector('.training-empty'));
      let group, previousDate;
      for (const item of [...items].sort((a,b) => b.trained_on.localeCompare(a.trained_on))) {
        if (item.trained_on !== previousDate) {
          group = make('section', '', 'training-day');
          const heading = make('h2', `${item.trained_on === localISO(new Date()) ? 'Hoy · ' : ''}${dateLabel(item.trained_on)}`);
          group.append(heading); journal.append(group); previousDate = item.trained_on;
        }
        const row = make('article', '', 'training-entry');
        const content = make('div', '', 'training-entry-content');
        const name = link(displayName(item), '/training/' + item.id);
        content.append(name, make('p', item.result_text || 'Resultado sin registrar', 'training-entry-result'));
        if (item.adaptations) content.append(make('p', item.adaptations, 'training-entry-note'));
        if (item.rpe !== null && item.rpe !== undefined) content.append(make('p', `Esfuerzo ${item.rpe}/10`, 'training-entry-meta'));
        if (item.video_links?.length) content.append(link(`${item.video_links.length} ${item.video_links.length === 1 ? 'video vinculado' : 'videos vinculados'}`, '/training/' + item.id));
        if (item.source_image_id) row.append(thumbnail(item.source_image_id, item.id));
        else {
          const placeholder = make('div', '', 'training-thumbnail training-thumbnail-placeholder');
          placeholder.setAttribute('role', 'img'); placeholder.setAttribute('aria-label', 'Entrenamiento sin foto');
          const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
          svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('aria-hidden', 'true');
          const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          path.setAttribute('d', 'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2ZM3 17l6-6 4 4 3-3 5 5M16 7h.01');
          svg.append(path); placeholder.append(svg); row.append(placeholder);
        }
        const media = make('div', '', 'training-entry-media');
        const date = make('time', new Intl.DateTimeFormat('es-CL', {day:'2-digit',month:'2-digit',year:'numeric'}).format(calendarDate(item.trained_on)), 'training-thumbnail-date');
        date.dateTime = item.trained_on;
        media.append(row.firstElementChild, date);
        const actions = make('div', '', 'training-entry-actions');
        const edit = link('', '/training/' + item.id + '?edit=1'); edit.className = 'training-edit'; edit.setAttribute('aria-label', 'Editar entrenamiento');
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox','0 0 24 24'); svg.setAttribute('aria-hidden','true');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path'); path.setAttribute('d','M15 5l4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15v5Z'); svg.append(path);
        edit.append(svg, make('span', 'Editar')); actions.append(edit, deleteAction(item)); content.append(actions);
        row.append(media, content);
        group.append(row);
      }
      return;
    }
    const editing = identifier !== 'new';
    let dirty = false;
    let voice;
    const markDirty = () => { dirty = true; };
    const warnDraft = event => {
      if (dirty) { event.preventDefault(); event.returnValue = ''; }
    };
    root.addEventListener('input', markDirty);
    window.addEventListener('beforeunload', warnDraft);
    root.trainingCleanup = () => { root.removeEventListener('input', markDirty); window.removeEventListener('beforeunload', warnDraft); voice?.cleanup(); };
    const data = editing ? await api('/api/training-sessions/' + identifier) : {};
    const now = new Date();
    const today = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
    const layout = make('div', '', 'training-layout');
    const note = make('article', '', 'training-note');
    const noteHeading = make('h2', editing ? displayName(data) : data.title); noteHeading.tabIndex = -1;
    const unsavedNote = make('p', 'Tienes cambios sin guardar en el detalle.', 'training-hint'); unsavedNote.hidden = true;
    const viewDetail = make('button', 'Editar entrenamiento'); viewDetail.type = 'button';
    if (editing) {
      const date = make('time', new Intl.DateTimeFormat('es-CL', {dateStyle:'long'}).format(new Date(data.trained_on + 'T12:00:00')), 'training-note-date');
      date.dateTime = data.trained_on;
      note.append(date, noteHeading);
      if (data.source_image_id) note.append(thumbnail(data.source_image_id, data.id, true));
      function noteText(title, value) {
        const section = make('section', '', 'training-note-section');
        section.append(make('h3', title));
        const text = value || '';
        if (text.length > 650) {
          const cut = text.slice(0,650).replace(/\s+\S*$/, '');
          section.append(make('p', cut + '…'));
          const more = make('details'); more.append(make('summary', 'Leer ' + title.toLowerCase() + ' completo'), make('p', text)); section.append(more);
        } else section.append(make('p', text));
        note.append(section);
      }
      noteText('Cómo me fue', data.result_text || 'Todavía no anotaste tu resultado. Puedes añadirlo al editar.');
      if (data.blocks?.length) {
        const section = make('section', '', 'training-reading-blocks');
        section.append(make('h3', 'Bloques del entrenamiento'));
        data.blocks.forEach((block,index) => {
          const disclosure = make('details'); disclosure.open = index === 0;
          disclosure.append(make('summary', `${block.title} · ${formats[block.format] || 'Otro'}`));
          if (block.prescription) disclosure.append(make('p', block.prescription));
          const movements = make('ul');
          for (const movement of block.movements || []) movements.append(make('li', `${movement.name}${movement.prescription ? ': ' + movement.prescription : ''}`));
          if (movements.childElementCount) disclosure.append(movements);
          section.append(disclosure);
        });
        note.append(section);
        const original = make('details', '', 'training-reading-original');
        original.append(make('summary', 'Ver el entrenamiento como texto'), make('p', data.workout)); note.append(original);
      } else noteText('Lo que entrené', data.workout);
      if (data.adaptations) noteText('Cargas y adaptaciones', data.adaptations);
      if (data.rpe !== null && data.rpe !== undefined) note.append(make('p', `Esfuerzo percibido: ${data.rpe}/10`, 'training-note-meta'));
      if (data.video_links?.length) {
        const media = make('section', '', 'training-note-section'); media.append(make('h3', 'Videos vinculados'));
        for (const video of data.video_links) media.append(link(`${video.movement}${video.context ? ' · ' + video.context : ''}`, '/analyses/' + video.analysis_id));
        note.append(media);
      }
      note.append(viewDetail, deleteAction(data), unsavedNote);
    }
    const conversation = make('section', '', 'training-conversation');
    conversation.append(make('h2', '¿Qué entrenaste hoy?'), make('p', 'Cuéntame el WOD y cómo te fue. Puedes escribir, añadir la pizarra o usar tu voz.', 'training-chat-prompt'));
    const messages = make('div', '', 'training-messages'); messages.setAttribute('aria-live', 'polite');
    const source = make('textarea'); source.rows = 4; source.maxLength = 12000; source.value = data.source_text || '';
    source.placeholder = 'Ej.: AMRAP de 12 minutos: 10 thrusters y 12 burpees.'; source.setAttribute('aria-label', 'Descripción del entrenamiento');
    let imageId = data.source_image_id || null;
    const photoLabel = make('label', 'Foto de la pizarra · opcional', 'training-file-label');
    const photo = make('input'); photo.type = 'file'; photo.accept = 'image/jpeg,image/png,image/webp';
    photoLabel.append(photo);
    const choosePhoto = make('button', 'Añadir foto de la pizarra', 'secondary-button'); choosePhoto.type = 'button'; choosePhoto.onclick = () => photo.click();
    const preview = make('img'); preview.alt = 'Foto de la pizarra'; preview.className = 'training-photo'; preview.hidden = !imageId;
    if (imageId) preview.src = '/api/training-sessions/images/' + imageId;
    const removePhoto = make('button', 'Quitar foto', 'secondary-button'); removePhoto.type = 'button'; removePhoto.hidden = !imageId;
    removePhoto.onclick = () => { imageId = null; photo.value = ''; preview.removeAttribute('src'); preview.hidden = true; removePhoto.hidden = true; dirty = true; notify('Foto quitada. Tu descripción se conserva.'); };
    const prepare = make('button', 'Interpretar WOD'); prepare.type = 'button';
    const manual = make('button', 'Completar manualmente', 'secondary-button'); manual.type = 'button';
    const composer = make('div', '', 'training-composer');
    const captureActions = make('div', '', 'training-capture-actions training-chat-toolbar'); captureActions.append(choosePhoto, prepare);
    const sourceLabel = make('label'); sourceLabel.append(make('span', 'WOD y cómo te fue', 'training-composer-label'), source);
    function iconButton(button, path) {
      const label = button.textContent;
      button.replaceChildren(make('span', label, 'training-composer-label'));
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox','0 0 24 24'); svg.setAttribute('aria-hidden','true');
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'path'); line.setAttribute('d',path); svg.append(line); button.append(svg);
      button.classList.add('training-chat-icon'); button.title = label;
    }
    iconButton(choosePhoto, 'M12 5v14M5 12h14');
    composer.append(photoLabel, preview, removePhoto, sourceLabel, captureActions);
    conversation.append(composer, manual, make('p', 'Al interpretar, el texto y la foto se procesan con IA. Siempre revisas antes de guardar.', 'training-hint'));
    const form = make('form', '', 'training-form');
    const reviewHeading = make('h2', editing ? 'Información del entrenamiento' : 'Revisa tu entrenamiento'); reviewHeading.tabIndex = -1;
    form.append(reviewHeading, make('p', 'Así quedará en tu bitácora. Revisa el WOD y añade cómo te fue.', 'training-intro'), messages);
    const editSource = make('button', 'Volver a mi descripción', 'secondary-button'); editSource.type = 'button';
    function showReview(focus = true) {
      header.querySelector('h1').textContent = editing ? 'Editar entrenamiento' : 'Registrar entrenamiento';
      note.hidden = true;
      conversation.hidden = true; form.hidden = false; form.append(status);
      if (focus) reviewHeading.focus();
    }
    editSource.onclick = () => { form.hidden = true; conversation.hidden = false; captureActions.after(status); source.focus(); };
    form.append(editSource);
    if (editing) {
      const backToNote = make('button', 'Volver al resumen', 'secondary-button'); backToNote.type = 'button';
      backToNote.onclick = () => { showNote(); noteHeading.focus(); };
      form.insertBefore(backToNote, editSource);
      viewDetail.onclick = () => showReview();
    }
    function showNote() {
      header.querySelector('h1').textContent = 'Tu entrenamiento';
      conversation.hidden = true; form.hidden = true; note.hidden = false;
      unsavedNote.hidden = !dirty; note.append(status);
    }
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
    const dateName = value => {
      if (!value) return '';
      const text = new Intl.DateTimeFormat('es-CL', {weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date(value + 'T12:00:00'));
      return text.charAt(0).toUpperCase() + text.slice(1);
    };
    let defaultTitle = dateName(controls.trained_on.value);
    field('title', 'Nombre del entrenamiento', 'text', editing ? data.title : defaultTitle, true, 160);
    controls.trained_on.addEventListener('change', () => {
      if (!editing && controls.title.value === defaultTitle && controls.trained_on.value) {
        defaultTitle = dateName(controls.trained_on.value); controls.title.value = defaultTitle;
      }
    });
    field('workout', 'Entrenamiento programado · ejercicios, series, repeticiones y cargas', 'textarea', data.workout, true, 12000);
    field('result_text', 'Tu resultado · tiempo, rondas o series realizadas', 'textarea', data.result_text);
    field('adaptations', 'Cargas utilizadas y adaptaciones · opcional', 'textarea', data.adaptations);
    const rpe = field('rpe', 'Esfuerzo percibido · opcional (1 mínimo, 10 máximo)', 'number', data.rpe);
    rpe.min = 1; rpe.max = 10; rpe.step = 1;
    rpe.inputMode = 'numeric';
    function disclosure(title, nodes, open = false) {
      const section = make('details', '', 'training-disclosure'); section.open = open;
      section.append(make('summary', title), ...nodes); form.append(section); return section;
    }
    const contextDetails = disclosure('Cargas, adaptaciones y esfuerzo · opcional', [controls.adaptations.parentElement, rpe.parentElement], Boolean(data.adaptations || data.rpe));
    const workoutDetails = disclosure('Ver o editar el WOD como texto', [make('p', 'Editar este texto reemplaza los bloques por tu descripción libre.', 'training-hint'), controls.workout.parentElement]);
    // Native validation must reveal required inputs even inside closed disclosures.
    form.addEventListener('invalid', event => {
      let parent = event.target.parentElement;
      while (parent && parent !== form) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
      notify('Revisa los campos indicados antes de guardar.', true);
    }, true);
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
      workoutDetails.open = !blocks.length;
    }
    form.insertBefore(workoutDetails, controls.result_text.parentElement);
    form.insertBefore(blockArea, workoutDetails); renderBlocks();
    controls.workout.addEventListener('input',()=>{if(blocks.length){blocks=[];renderBlocks();status.textContent='Conservé tu edición libre; los bloques anteriores se quitaron para evitar datos contradictorios.'}});
    manual.onclick = () => {
      if (!controls.workout.value.trim()) controls.workout.value = source.value.trim();
      messages.replaceChildren(); showReview(false);
      controls.title.focus();
    };
    let busy = false;
    function processing(value, fromVoice = false) {
      busy = value;
      layout.setAttribute('aria-busy', String(value));
      for (const input of root.querySelectorAll('input, textarea, select, button')) input.disabled = value;
      voice?.setExternalBusy(fromVoice ? false : value);
    }
    voice=window.createTrainingVoice({container:conversation,source,onBusy:value=>processing(value,true),onText:()=>{dirty=true;source.dispatchEvent(new Event('input',{bubbles:true}));}});
    iconButton(voice.recordButton, 'M9 5a3 3 0 0 1 6 0v7a3 3 0 0 1-6 0V5M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8');
    captureActions.insertBefore(voice.recordButton, prepare);
    composer.insertBefore(conversation.querySelector('.training-voice'), captureActions);
    photo.onchange = async () => {
      const file = photo.files[0]; if (!file) return;
      if (file.size > 8*1024*1024) { notify('La imagen supera 8 MB. Elige una más pequeña.', true); photo.value=''; return; }
      processing(true); notify('Guardando foto…');
      try {
        const body = new FormData(); body.append('file',file);
        const uploaded=await api('/api/training-sessions/images',{method:'POST',body});
        imageId=uploaded.id; preview.src=uploaded.url; preview.hidden=false; removePhoto.hidden=false; dirty=true; notify('Foto lista. Puedes añadir tu resultado e interpretar el WOD.');
      } catch(error) { notify(error.message, true); photo.value=''; }
      finally { processing(false); }
    };
    prepare.onclick = async () => {
      if (busy) return;
      if (!source.value.trim() && !imageId) { status.textContent='Escribe el WOD o agrega una foto de la pizarra.'; source.focus(); return; }
      processing(true); notify('Interpretando el entrenamiento…'); prepare.textContent = 'Interpretando…';
      try {
        const draft=await api('/api/training-sessions/interpret',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:source.value,image_id:imageId})});
        for (const key of (editing ? ['title','workout','result_text','adaptations','rpe'] : ['workout','result_text','adaptations','rpe'])) controls[key].value=draft[key] ?? '';
        blocks=draft.blocks;renderBlocks();dirty=true;
        contextDetails.open = Boolean(draft.adaptations || draft.rpe);
        messages.replaceChildren();
        if (draft.questions.length) {
          messages.append(make('h3','Por confirmar'));
          const list=make('ul'); draft.questions.forEach(question=>list.append(make('li',question)));messages.append(list,make('p','Añade tus aclaraciones al texto y vuelve a interpretar, o corrige la ficha directamente.'));
        }
        notify('Ficha lista para revisar. Todavía no se ha guardado la sesión.');
        showReview();
      } catch(error) { notify(error.message + ' Puedes reintentar o completar manualmente.', true); }
      finally { processing(false); prepare.textContent = 'Interpretar WOD'; }
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
    const choose = make('button', 'Vincular análisis existente', 'secondary-button'); choose.type = 'button'; videos.append(choose);
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
          dirty = true; videoLinks.push({analysis_id: select.value, movement: movement.value.trim(), context: context.value.trim()}); renderLinks(); movement.value = ''; context.value = ''; notify('Video vinculado al borrador. Guarda la sesión para confirmar.');
        };
        videos.append(select, movement, context, add); choose.hidden = true;
      } catch (error) { status.textContent = error.message; choose.disabled = false; }
    };
    disclosure('Videos · opcional', [videos], Boolean(videoLinks.length));
    const actions = make('div', '', 'form-actions training-save-actions');
    const save = make('button', editing ? 'Guardar cambios' : 'Guardar sesión'); save.type = 'submit'; actions.append(save); form.append(actions);
    form.onsubmit = async (event) => {
      event.preventDefault(); if (busy) return;
      processing(true); save.textContent = 'Guardando…'; notify('Guardando tu entrenamiento…'); form.setAttribute('aria-busy','true');
      const payload = Object.fromEntries(Object.entries(controls).map(([key, input]) => [key, input.value.trim()]));
      payload.rpe = payload.rpe === '' ? null : Number(payload.rpe);
      payload.source_text = source.value; payload.video_links = videoLinks; payload.blocks=blocks; payload.source_image_id=imageId;
      try {
        await api('/api/training-sessions' + (editing ? '/' + identifier : ''), {method: editing ? 'PUT' : 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)});
        dirty = false; setFlash(editing ? 'Cambios guardados en tu bitácora.' : 'Entrenamiento guardado en tu bitácora.'); window.location.assign('/training');
      } catch (error) { notify(`${error.message} Tu borrador se conserva en esta pantalla.`, true); save.disabled = false; save.textContent = editing ? 'Guardar cambios' : 'Guardar sesión'; }
      finally { processing(false); form.setAttribute('aria-busy','false'); }
    };
    layout.append(note, conversation, form); root.append(layout); status.textContent = '';
    if (editing) {
      if (new URLSearchParams(window.location.search).get('edit') === '1') showReview();
      else showNote();
    }
    else { note.hidden = true; form.hidden = true; captureActions.after(status); }
  } catch (error) {
    notify(error.message, true);
    const retry = make('button', 'Reintentar'); retry.onclick = () => window.setupTraining(identifier); root.append(retry);
  }
};

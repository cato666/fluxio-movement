const filters = document.querySelector('#filters');
const list = document.querySelector('#exercise-list');
const detail = document.querySelector('#detail');
const status = document.querySelector('#status');
const stateLabel = value => value === 'supported' ? 'Con análisis' : 'Solo referencia';
function node(tag, text, parent) {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  parent.append(element);
  return element;
}
function show(exercise, selected) {
  list.querySelectorAll('button').forEach(button => button.setAttribute('aria-current', String(button === selected)));
  detail.replaceChildren();
  node('h2', exercise.name, detail);
  node('p', `${exercise.category} · ${stateLabel(exercise.analysis_status)} · Vistas: ${exercise.supported_views.join(', ')}`, detail);
  node('p', exercise.analysis_status === 'supported' ? 'Soporte de conteo de repeticiones. Los errores listados son referencias para el coach.' : 'Este ejercicio aún no tiene detección automática. Las vistas indicadas están previstas para futuras implementaciones.', detail);
  node('h3', 'Referencia', detail);
  if (!exercise.reference_videos.length) node('p', 'Video oficial pendiente de verificación.', detail);
  exercise.reference_videos.forEach(video => {
    const frame = node('iframe', '', detail);
    frame.title = `${exercise.name} · ${video.organization}`;
    frame.loading = 'lazy'; frame.allowFullscreen = true;
    frame.referrerPolicy = 'strict-origin-when-cross-origin';
    frame.src = `https://www.youtube.com/embed/${video.video_id}`;
    const link = node('a', 'Ver en YouTube', detail);
    link.href = video.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
    video.segments.forEach(segment => {
      const button = node('button', `${segment.type}: ${segment.start_sec}–${segment.end_sec} s`, detail);
      button.onclick = () => { frame.src = `https://www.youtube.com/embed/${video.video_id}?start=${Math.floor(segment.start_sec)}&end=${Math.ceil(segment.end_sec)}`; };
    });
  });
  for (const [title, values] of [['Fases', exercise.phases.map(x => x.replaceAll('_', ' '))], ['Errores comunes', exercise.faults.map(x => `${x.name}: ${x.description}`)], ['Cues para el coach', exercise.coaching_cues]]) {
    node('h3', title, detail); const ul = node('ul', '', detail);
    values.forEach(value => node('li', value, ul));
  }
}
let generation = 0;
async function load() {
  const current = ++generation;
  status.textContent = 'Cargando ejercicios…';
  try {
    const response = await fetch(`/api/exercises?${new URLSearchParams([...new FormData(filters)].filter(([, value]) => value))}`);
    if (response.status === 401) { location.href = '/login?next=/exercises'; return; }
    if (!response.ok) throw new Error('No se pudo cargar la biblioteca.');
    const exercises = await response.json();
    if (current !== generation) return;
    list.replaceChildren(); detail.replaceChildren();
    status.textContent = exercises.length ? `${exercises.length} ejercicios` : 'No hay ejercicios con estos filtros.';
    exercises.forEach(exercise => {
      const button = node('button', exercise.name, list);
      node('small', `${exercise.category} · ${stateLabel(exercise.analysis_status)} · ${exercise.supported_views.join(', ')}`, button);
      button.onclick = () => show(exercise, button);
    });
    if (exercises.length) show(exercises[0], list.firstChild);
  } catch (error) {
    if (current !== generation) return;
    status.textContent = `${error.message} Cambia un filtro para reintentar.`;
  }
}
fetch('/api/exercise-categories').then(response => {
  if (!response.ok) throw new Error(); return response.json();
}).then(categories => categories.forEach(category => {
  const option = node('option', category, filters.elements.category); option.value = category;
})).catch(() => { status.textContent = 'No se pudieron cargar las categorías.'; });
filters.addEventListener('change', load);
load();

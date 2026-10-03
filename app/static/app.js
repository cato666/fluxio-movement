const $ = (selector) => document.querySelector(selector);

const stateLabels = {
  PENDING: "Pendiente",
  PROCESSING: "Procesando",
  COMPLETED: "Completado",
  FAILED: "Fallido",
};

const reviewStateLabels = {
  PENDING: "Pendiente",
  IN_REVIEW: "En revisión",
  COMPLETED: "Completada",
};

const annotationLabels = { COMMENT: "Comentario", REVIEW: "Revisar", CORRECT: "Corregir", PRIORITY: "Prioridad" };
const NO_REPS_TIP = "No se detectaron repeticiones. Graba de lado, con el cuerpo completo en cuadro y buena luz.";
const noReps = (item) => item.status === "COMPLETED" && item.repetitions_detected === 0;
let detailPoller = null;

const fmtDate = (value) => value
  ? new Intl.DateTimeFormat("es-CL", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value))
  : "—";

function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = String(content);
  return node;
}

function setFlash(message) {
  window.sessionStorage.setItem("movement-coach-flash", message);
}

function takeFlash() {
  const message = window.sessionStorage.getItem("movement-coach-flash");
  window.sessionStorage.removeItem("movement-coach-flash");
  return message;
}

async function apiJson(url, options) {
  const response = await fetch(url, options);
  if (response.ok && response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) {
    const message = typeof data.detail === "string" ? data.detail : data.detail?.message;
    const error = new Error(message || "No se pudo completar la solicitud");
    error.analysisId = data.detail?.analysis_id;
    error.status = response.status;
    throw error;
  }
  return data;
}

function showView(id) {
  const trainingView = $('#training-view');
  if (trainingView) trainingView.hidden = id !== 'training-view';
  if (id !== "detail-view" && detailPoller) { detailPoller.stop(); detailPoller = null; }
  // Las rutas públicas no deben revelar accesos del área autenticada.
  const marketing = ["landing-view", "demo-view", "login-view"].includes(id);
  document.body.classList.toggle("marketing", marketing);
  document.documentElement.classList.toggle("marketing", marketing);
  for (const selector of [".functional-nav", ".functional-actions"]) {
    const item = document.querySelector(selector);
    item.hidden = marketing || document.querySelector(".functional-nav").dataset.ready !== "true";
  }
  const marketingNav = document.querySelector(".marketing-nav");
  const marketingActions = document.querySelector(".auth-actions");
  marketingNav.hidden = !marketing;
  marketingActions.hidden = !marketing;
  for (const view of ["landing-view", "login-view", "usage-view", "demo-view", "new-view", "coach-new-analysis-view", "coach-new-athlete-view", "list-view", "detail-view", "coach-selection-view", "coach-reviews-view", "coach-review-detail-view"]) {
    $(`#${view}`).hidden = view !== id;
  }
}

async function sessionUser() { return apiJson("/api/auth/me", {cache:"no-store"}); }

function setupLogout() {
  const button = $("#logout-button");
  if (!button) return;
  button.onclick = async () => {
    await apiJson("/api/auth/logout", { method: "POST" });
    window.location.assign("/");
  };
}

function configureNavigation(user) {
  document.querySelector(".functional-nav").dataset.ready = "true";
  const currentPath = window.location.pathname.replace(/\/$/, "");
  for (const link of document.querySelectorAll("[data-nav-role]")) {
    link.hidden = link.dataset.navRole !== user.role;
    const target = new URL(link.href).pathname;
    const active = currentPath === target
      || (target === '/training' && currentPath.startsWith('/training/'))
      || (target === "/analyses" && /^\/analyses\/\d/.test(currentPath))
      || (target === "/coach/reviews" && currentPath.startsWith("/coach/reviews/"));
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  if (!document.body.classList.contains('marketing')) {
    document.querySelector('.functional-nav').hidden = false;
    document.querySelector('.functional-actions').hidden = false;
  }
}

function setupLogin() {
  showView("login-view");
  const form = $("#login-form"); const status = $("#login-status");
  form.onsubmit = async (event) => {
    event.preventDefault(); const button = form.querySelector("button"); button.disabled = true; status.textContent = "Ingresando…";
    try {
      const user = await apiJson("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(new FormData(form))) });
      const next = new URLSearchParams(window.location.search).get("next");
      window.location.assign(next && next.startsWith("/") && !next.startsWith("//") ? next : user.next);
    }
    catch (error) { status.textContent = error.message; button.disabled = false; }
  };
}

function setupCommercialAudience(audience) {
  showView("landing-view");
  if (audience === "athlete") {
    $("#landing-title").innerHTML = "Mejora tu técnica.<br><em>Con feedback claro.</em>";
    $("#landing-copy").textContent = "Sube tu video, revisa tus repeticiones y recibe el feedback de tu coach en el momento exacto.";
  }
  setupLandingInteractions();
}

function setupLandingInteractions() {
  const tabs = [...document.querySelectorAll("[data-product-tab]")];
  const selectTab = (tab) => {
    for (const item of tabs) {
      const active = item === tab;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", String(active));
      item.tabIndex = active ? 0 : -1;
      const pane = document.getElementById(item.getAttribute("aria-controls"));
      if (pane) { pane.hidden = !active; pane.classList.toggle("is-active", active); }
    }
  };
  for (const [index, tab] of tabs.entries()) {
    tab.onclick = () => selectTab(tab);
    tab.onkeydown = (event) => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const target = event.key === 'Home' ? tabs[0] : event.key === 'End' ? tabs.at(-1) : tabs[(index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
      target.focus(); selectTab(target);
    };
  }
  const priceButtons = [...document.querySelectorAll("[data-price-cycle]")];
  for (const button of priceButtons) button.onclick = () => {
    for (const item of priceButtons) {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    }
    for (const price of document.querySelectorAll("[data-m][data-a]")) price.textContent = `$${price.dataset[button.dataset.priceCycle]}`;
  };
}

const number = (value) => new Intl.NumberFormat("es-CL").format(Number(value || 0));

async function setupUsage() {
  showView("usage-view");
  const status = $("#usage-status");
  status.textContent = "Cargando consumo…";
  try {
    const data = await apiJson("/api/internal/ai-usage");
    const totals = data.totals;
    $("#usage-totals").replaceChildren(
      metric("Operaciones completadas", number(totals.completed_runs)),
      metric("Tokens de entrada", number(totals.input_tokens)),
      metric("Tokens de salida", number(totals.output_tokens)),
      metric("Tokens reportados", number(totals.total_tokens)),
      metric("Llamadas de transcripción", number(totals.transcription_runs)),
      metric("Audio enviado", `${number(totals.audio_seconds)} s`),
    );
    const models = $("#usage-by-model"); models.replaceChildren();
    if (!data.by_model.length) models.textContent = "Aún no hay consumo de IA registrado.";
    for (const item of data.by_model) {
      const row = element("div", "rep");
      row.append(element("strong", "", item.model));
      row.append(element("span", "", ` · ${number(item.runs)} operaciones · entrada ${number(item.input_tokens)} · salida ${number(item.output_tokens)} · total ${number(item.total_tokens)} tokens reportados`));
      models.append(row);
    }
    const athletes = $("#usage-by-athlete"); athletes.replaceChildren();
    for (const athlete of data.training_by_athlete || []) {
      const row = element("div", "rep");
      row.append(element("strong", "", athlete.athlete_name));
      row.append(element("span", "", ` · ${number(athlete.runs)} llamadas · entrada ${number(athlete.input_tokens)} · salida ${number(athlete.output_tokens)} · total ${number(athlete.total_tokens)} tokens reportados · ${number(athlete.audio_seconds)} s de audio enviado`));
      if (athlete.unreported_runs) row.append(element("span", "", ` · ${number(athlete.unreported_runs)} llamadas sin detalle de tokens`));
      athletes.append(row);
    }
    if (!athletes.children.length) athletes.textContent = "Aún no hay llamadas de la bitácora registradas.";
    const recent = $("#usage-recent-runs"); recent.replaceChildren();
    if (!data.recent_runs.length) recent.textContent = "Aún no hay ejecuciones registradas.";
    for (const run of data.recent_runs) {
      const row = element("div", "rep");
      row.append(element("strong", "", run.exercise));
      if (run.athlete_name) row.append(element("span", "", ` · ${run.athlete_name} · ${run.model}`));
      row.append(element("span", "", ` · ${fmtDate(run.created_at)} · ${run.status}`));
      row.append(element("span", "", run.total_tokens === null ? ' · Tokens no reportados por el proveedor' : ` · entrada ${number(run.input_tokens)} · salida ${number(run.output_tokens)} · total ${number(run.total_tokens)}`));
      if (run.duration_seconds !== null && run.duration_seconds !== undefined) row.append(element("span", "", ` · ${number(run.duration_seconds)} s de audio enviado`));
      recent.append(row);
    }
    status.textContent = totals.unreported_training_runs ? `${number(totals.unreported_training_runs)} llamadas de la bitácora no tienen detalle de tokens; el total solo incluye tokens reportados.` : "";
  } catch (error) {
    status.textContent = error.message;
  }
}

function renderFilterChips(container, items, active, labels, onSelect) {
  container.replaceChildren();
  const values = ["", ...Object.keys(labels)];
  for (const value of values) {
    const count = value ? items.filter((item) => item.status === value).length : items.length;
    const button = element("button", `filter-chip${active === value ? " is-active" : ""}`, value ? `${labels[value]} (${count})` : `Todas (${count})`);
    button.type = "button";
    button.setAttribute("aria-pressed", String(active === value));
    button.onclick = () => onSelect(value);
    container.append(button);
  }
}

function setupNew() {
  showView("new-view");
  const form = $("#analysis-form"), button = $("#go"), status = $("#status");
  const fileInput = form.elements.file, preview = $("#upload-preview"), progress = $("#upload-progress");
  let uploading = false, previewUrl;
  const refresh = () => {
    const objective = form.elements.objective;
    objective.setCustomValidity(objective.value.trim() ? "" : "Escribe qué quieres observar o mejorar.");
    const requirements = AthleteState.requirements({exercise: form.elements.exercise.value, objective: objective.value, view: form.elements.view.value, file: fileInput.files[0]});
    fileInput.setCustomValidity(fileInput.files[0] && !requirements[3].ready ? "Usa un video MP4, MOV, M4V o AVI." : "");
    $("#analysis-requirements").replaceChildren(...requirements.filter(r => !r.ready).map(r => element("li", "", r.label)));
    const ready = form.checkValidity();
    $("#form-readiness").textContent = ready ? "Listo para subir y analizar." : requirements.every(r => r.ready) ? "Revisa los valores del formulario." : "Para continuar falta:";
    button.disabled = uploading || !ready;
  };
  fileInput.addEventListener("change", () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    const file = fileInput.files[0]; preview.hidden = !file;
    if (file) { previewUrl = URL.createObjectURL(file); preview.src = previewUrl; }
    else preview.removeAttribute("src");
    $("#selected-file").textContent = file ? `${file.name} · ${(file.size / 1048576).toFixed(1)} MB · seleccionado` : "Ningún video seleccionado.";
    status.textContent = ""; refresh();
  });
  form.addEventListener("input", refresh); refresh();
  form.addEventListener("submit", event => {
    event.preventDefault();
    if (uploading || !form.checkValidity()) { if (!uploading) form.reportValidity(); return; }
    const data = new FormData(form); if (!data.get("load_kg")) data.delete("load_kg");
    uploading = true; button.disabled = true;
    const controls = [...form.querySelectorAll("input, select, textarea")]; controls.forEach(c => c.disabled = true);
    progress.hidden = false; progress.value = 0; status.textContent = "Subiendo video… 0 %";
    const fail = message => { uploading = false; controls.forEach(c => c.disabled = false); progress.hidden = true; status.textContent = message; refresh(); };
    const request = new XMLHttpRequest(); request.open("POST", "/api/analyses");
    request.upload.onprogress = event => {
      if (event.lengthComputable) { progress.value = Math.round(event.loaded / event.total * 100); status.textContent = progress.value === 100 ? "Video enviado. Esperando confirmación del servidor…" : `Subiendo video… ${progress.value} %`; }
    };
    request.onload = () => {
      let body = {}; try { body = JSON.parse(request.responseText); } catch (_) {}
      if (request.status === 202 && body.id) { window.location.assign(`/analyses/${body.id}`); return; }
      fail(typeof body.detail === "string" ? body.detail : body.detail?.message || "No se pudo iniciar el análisis. Revisa los datos e intenta nuevamente.");
    };
    request.onerror = () => fail("Se perdió la conexión durante la subida. Revisa Mis análisis antes de volver a enviar: el servidor podría haber recibido el video.");
    request.send(data);
  });
}

async function setupCoachNewAnalysis() {
  showView("coach-new-analysis-view");
  const form = $("#coach-analysis-form"); const status = $("#coach-upload-status"); const athlete = $("#coach-athlete");
  try {
    const data = await apiJson("/api/coach/athletes");
    athlete.replaceChildren(element("option", "", "Selecciona un atleta")); athlete.options[0].value = "";
    for (const item of data.items) { const option = element("option", "", item.name); option.value = item.id; athlete.append(option); }
  } catch (error) { status.textContent = error.message; return; }
  form.onsubmit = async (event) => {
    event.preventDefault(); const button = form.querySelector("button"); button.disabled = true; status.textContent = "Subiendo y creando revisión…";
    const data = new FormData(form); if (!data.get("load_kg")) data.delete("load_kg");
    try { const result = await apiJson("/api/coach/analyses", { method: "POST", body: data }); window.location.assign(`/coach/reviews/${result.review_id}`); }
    catch (error) { status.textContent = error.message; button.disabled = false; }
  };
}

function setupCoachNewAthlete() {
  showView("coach-new-athlete-view");
  const form = $("#coach-athlete-form"); const status = $("#coach-athlete-status");
  form.onsubmit = async (event) => {
    event.preventDefault(); const button = form.querySelector("button"); button.disabled = true; status.textContent = "Registrando atleta…";
    try {
      const athlete = await apiJson("/api/coach/athletes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(new FormData(form))) });
      setFlash(`${athlete.name} fue registrado y ya está disponible para subir un video.`);
      window.location.assign("/coach/analyses/new");
    } catch (error) { status.textContent = error.message; button.disabled = false; }
  };
}

async function setupList() {
  showView("list-view");
  const status = $("#list-status");
  const list = $("#analysis-list");
  status.textContent = "Cargando análisis…";
  try {
    const data = await apiJson("/api/analyses");
    const items = data.items;
    let activeFilter = "";
    const render = () => {
      list.replaceChildren();
      const visible = activeFilter ? items.filter((item) => item.status === activeFilter) : items;
      status.textContent = visible.length ? "" : activeFilter ? "No hay análisis en este estado." : "Aún no tienes análisis. Sube un video para comenzar la demo.";
      status.classList.toggle("empty-state", visible.length === 0);
      renderFilterChips($("#analysis-filters"), items, activeFilter, stateLabels, (next) => { activeFilter = next; render(); });
      for (const item of visible) {
      const card = element("article", "card analysis-row");
      const thumb = item.thumbnail_url ? element("img", "analysis-thumbnail") : element("div", "analysis-thumbnail thumbnail-placeholder");
      if (item.thumbnail_url) { thumb.src = item.thumbnail_url; thumb.loading = "lazy"; thumb.alt = ""; }
      const info = element("div");
      info.append(element("h2", "", item.exercise || "Análisis anterior"));
      info.append(element("p", "muted", `${fmtDate(item.created_at)} · ${item.load_kg == null ? "Sin carga" : `${item.load_kg} kg`}`));
      info.append(element("p", "", item.objective || "Sin objetivo registrado"));
      const side = element("div", "row-side");
      if (noReps(item)) {
        side.append(element("span", "state state-warning", "Sin reps detectadas"));
      } else {
        side.append(element("span", `state state-${item.status.toLowerCase()}`, stateLabels[item.status] || item.status));
        if (item.status === "PROCESSING") side.append(element("span", "muted", `${item.progress || 0} % · ${item.stage || "analyzing"}`));
        side.append(element("span", "muted", `${item.repetitions_detected} repeticiones`));
      }
      const action = AthleteState.reviewAction(item);
      if (action.badge) side.prepend(element("span", `state state-${action.state === "AVAILABLE" ? "completed" : "pending"}`, action.badge));
      const link = element("a", "button-link", action.state === "AVAILABLE" ? action.label : "Ver análisis");
      link.href = action.state === "AVAILABLE" ? action.href : `/analyses/${item.id}`;
      side.append(link);
      card.append(thumb, info, side);
      list.append(card);
      }
    }
    render();
  } catch (error) {
    status.textContent = `No se pudieron cargar tus análisis: ${error.message}`;
  }
}

function metric(label, value) {
  const box = element("div", "metric");
  box.append(element("span", "", label), element("b", "", value == null ? "—" : value));
  return box;
}

function aiObservationCard(observation, actions = null, onJump = seekAthleteVideo) {
  const card = element("article", `ai-observation severity-${observation.severity || "review"}`);
  const meta = ["IA", observation.repetition ? `Rep ${observation.repetition}` : null, observation.timestamp == null ? null : formatVideoTime(observation.timestamp)].filter(Boolean).join(" · ");
  const timestamp = element(observation.timestamp == null ? "span" : "button", "ai-observation-meta", meta);
  if (observation.timestamp != null) {
    timestamp.type = "button";
    timestamp.setAttribute("aria-label", `Ver momento ${formatVideoTime(observation.timestamp)}`);
    timestamp.onclick = (event) => { event.stopPropagation(); onJump(observation.timestamp); };
  }
  card.append(timestamp);
  card.append(element("h3", "", observation.title));
  card.append(element("p", "", observation.description));
  if (observation.evidence) card.append(element("p", "ai-observation-evidence", `Evidencia: ${observation.evidence}`));
  if (actions) card.append(actions);
  card.onclick = () => { if (observation.timestamp != null) onJump(observation.timestamp); };
  return card;
}

function renderAthleteAIObservations(observations) {
  const section = $("#athlete-ai-observations");
  const list = $("#athlete-ai-observations-list");
  list.replaceChildren();
  for (const observation of observations || []) list.append(aiObservationCard(observation));
  section.hidden = !(observations || []).length;
}

function renderPreflight(targetId, report) {
  const target = $(targetId);
  if (!target) return;
  const quality = report?.quality;
  const exercise = report?.exercise;
  if (!quality || quality.status === "UNAVAILABLE") { target.hidden = true; target.replaceChildren(); return; }
  target.hidden = false;
  const title = quality.status === "PASSED" ? "Captura validada" : "Calidad de captura";
  const message = quality.status === "PASSED"
    ? "Pose estable en " + Math.round((quality.pose_coverage || 0) * 100) + " % de las muestras."
    : [...(quality.warnings || []), ...(quality.blockers || [])].join(" ");
  target.replaceChildren(
    element("strong", "", title),
    element("p", "muted", message || "La captura fue procesada."),
    exercise?.status === "INCONCLUSIVE" ? element("p", "muted", "El ejercicio no pudo validarse automáticamente; se usó la selección indicada.") : document.createTextNode(""),
  );
}

function renderCompleted(item) {
  $("#detail-completed").hidden = false;
  for (const [id, url] of [["#original-video", item.original_video_url], ["#annotated-video", item.annotated_video_url]]) {
    const video = $(id); if (video.getAttribute("src") !== url) video.src = url;
  }
  const metrics = item.analysis_json?.summary_metrics || {};
  $("#metrics").replaceChildren(
    metric("Repeticiones", item.repetitions_detected),
    metric("Rodilla mín.", metrics.min_knee_angle == null ? null : `${metrics.min_knee_angle}°`),
    metric("Cadera mín.", metrics.min_hip_angle == null ? null : `${metrics.min_hip_angle}°`),
    metric("Inclinación tronco máx.", metrics.max_trunk_from_vertical == null ? null : `${metrics.max_trunk_from_vertical}°`),
  );
  renderPreflight("#detail-preflight", item.analysis_json?.preflight);
  const reps = $("#reps");
  reps.replaceChildren();
  if (!item.repetitions.length) {
    reps.textContent = NO_REPS_TIP;
  }
  for (const rep of item.repetitions) {
    const row = element("div", "rep");
    row.append(element("strong", "", `Rep ${rep.number}`));
    row.append(element("span", "", ` · ${rep.start_s}s → ${rep.end_s}s · punto más bajo ${rep.bottom_s}s`));
    if (rep.metrics.min_knee_angle != null) {
      row.append(element("span", "", ` · rodilla ${rep.metrics.min_knee_angle}°`));
    }
    const jump = element("button", "watch-moment", "Ver repetición"); jump.type = "button";
    jump.onclick = () => seekAthleteVideo(rep.bottom_s); row.append(jump);
    reps.append(row);
  }
  $("#technical-json").textContent = JSON.stringify(item.analysis_json, null, 2);
  renderAthleteAIObservations(item.ai_observations);
}

function seekAthleteVideo(timestamp) {
  const video = $("#annotated-video");
  if (!video || !Number.isFinite(Number(timestamp))) return;
  const seek = () => {
    const duration = Number.isFinite(video.duration) ? video.duration : Number(timestamp);
    const target = Math.max(0, Math.min(Number(timestamp), duration));
    video.currentTime = target;
    video.pause();
    video.scrollIntoView({ behavior: "auto", block: "center" });
    video.classList.add("video-seek-highlight");
    window.setTimeout(() => video.classList.remove("video-seek-highlight"), 900);
  };
  if (video.readyState >= HTMLMediaElement.HAVE_METADATA) seek();
  else video.addEventListener("loadedmetadata", seek, { once: true });
}

function renderCoachReviews(item) {
  const status = $("#review-status");
  status.replaceChildren();
  for (const review of item.coach_reviews || []) {
    const card = element("div", "card review-status-card");
    card.append(element("strong", "", `Revisión solicitada a ${review.coach.name} — ${reviewStateLabels[review.status] || review.status}`));
    status.append(card);
  }
  status.hidden = !item.coach_reviews?.length;
}

function renderAthleteCoachFeedback(item) {
  const container = $("#athlete-coach-feedback"); container.replaceChildren();
  for (const review of item.completed_coach_reviews || []) {
    const card = element("section", "card coach-feedback-card");
    card.append(element("h2", "", "Revisión del coach"), element("p", "muted", `${review.coach.name} · ${review.coach.specialty}`));
    if (review.main_focus) card.append(element("h3", "", "Punto principal"), element("p", "", review.main_focus));
    if (review.annotations?.length) {
      card.append(element("h3", "", "Momentos y comentarios del coach"));
      for (const annotation of review.annotations) {
        const note = element("div", "rep");
        note.append(element("strong", "", `${annotation.timestamp_s == null ? "Comentario" : formatVideoTime(annotation.timestamp_s)} · ${annotationLabels[annotation.type] || annotation.type}`), element("p", "", annotation.text));
        if (annotation.timestamp_s != null) {
          const watch = element("button", "watch-moment", "Ver momento"); watch.type = "button";
          watch.setAttribute("aria-label", `Ver momento ${formatVideoTime(annotation.timestamp_s)} en el video anotado`);
          watch.onclick = () => seekAthleteVideo(annotation.timestamp_s); note.append(watch);
        }
        card.append(note);
      }
    }
    if (review.next_session) card.append(element("h3", "", "Próxima sesión"), element("p", "", review.next_session));
    const details = element("details", "coach-feedback-details"); details.append(element("summary", "", "Más detalles de la revisión"));
    const repText = (label, rep) => rep ? `${label}: Rep ${rep.number}` : `${label}: Sin selección`;
    details.append(element("p", "", repText("Mejor repetición", review.best_repetition)), element("p", "", repText("Repetición a trabajar", review.work_repetition)));
    for (const [title, value] of [["Fortalezas", review.strengths], ["Resumen adicional", review.summary]]) if (value) details.append(element("h3", "", title), element("p", "", value));
    card.append(details); container.append(card);
  }
  container.hidden = !item.completed_coach_reviews?.length;
}

function renderAthleteNextStep(item) {
  const complete = item.status === "COMPLETED";
  $("#review-cta").hidden = !complete; $("#athlete-first-look").hidden = !complete;
  if (!complete) return;
  const action = AthleteState.reviewAction(item), link = $("#request-review-link");
  link.textContent = action.label; link.href = action.href;
  $("#review-cta-copy").textContent = action.copy;
  const human = item.completed_coach_reviews?.[0], observation = item.ai_observations?.[0];
  $("#athlete-first-look-copy").textContent = human?.main_focus ? `Punto principal del coach: ${human.main_focus}` : (observation ? `Análisis automático: ${observation.title}. ${observation.description}` : noReps(item) ? NO_REPS_TIP : `Se detectaron ${item.repetitions_detected} repeticiones. Mira el video anotado y compara las repeticiones antes de interpretar las métricas.`);
  const timestamp = human?.annotations?.find(a => a.timestamp_s != null)?.timestamp_s ?? observation?.timestamp ?? item.repetitions?.[0]?.bottom_s;
  const jump = $("#athlete-first-moment"); jump.hidden = timestamp == null;
  jump.onclick = () => seekAthleteVideo(timestamp);
}

async function setupDetail(id) {
  showView("detail-view");
  if (detailPoller) detailPoller.stop();
  const feedback = $("#detail-action-feedback"), connection = $("#detail-connection");
  const flash = takeFlash(); feedback.hidden = !flash; feedback.textContent = flash || "";
  let completedSignature;
  const render = item => {
    connection.hidden = true;
    $("#detail-title").textContent = item.exercise || "Análisis anterior";
    $("#detail-status").textContent = stateLabels[item.status] || item.status;
    $("#detail-status").className = `state state-${item.status.toLowerCase()}`;
    $("#detail-meta").textContent = `${fmtDate(item.created_at)} · ${item.load_kg == null ? "Sin carga" : `${item.load_kg} kg`} · ${item.view === "front" ? "Vista frontal" : "Vista de costado"} · ${item.repetitions_detected} repeticiones`;
    $("#detail-objective").textContent = item.objective || "Sin objetivo registrado";
    $("#detail-completed").hidden = item.status !== "COMPLETED";
    $("#detail-error").hidden = item.status !== "FAILED";
    renderAthleteNextStep(item);
    if (item.status === "COMPLETED") {
      const signature = JSON.stringify([item.analysis_json, item.ai_observations, item.coach_reviews, item.completed_coach_reviews]);
      if (signature !== completedSignature) { renderCompleted(item); renderCoachReviews(item); renderAthleteCoachFeedback(item); completedSignature = signature; }
      if (feedback.classList.contains("progress-card")) feedback.hidden = true;
    }
    if (["PENDING", "PROCESSING"].includes(item.status)) {
      feedback.hidden = false; feedback.className = "card progress-card";
      feedback.replaceChildren(element("h2", "", "Estamos analizando tu video."), element("p", "", "Puedes volver más tarde desde Mis análisis."));
      const stages = {validating_exercise: "Validando la captura", analyzing: "Analizando movimiento", annotating: "Generando el video anotado", finalizing: "Finalizando", generating_observations: "Generando observaciones automáticas"};
      const progress = element("progress"); progress.max = 100; progress.value = item.progress || 0;
      progress.setAttribute("aria-label", "Progreso del análisis");
      const back = element("a", "button-link secondary-button", "Volver a Mis análisis"); back.href = "/analyses";
      feedback.append(element("p", "muted", `${stages[item.stage] || "Preparando el análisis"} · ${item.progress || 0} %`), progress, back);
    }
    if (item.status === "FAILED") {
      feedback.hidden = true;
      const error = $("#detail-error");
      error.replaceChildren(element("h2", "", "El análisis no pudo completarse"), element("p", "", "Tu video quedó guardado. Revisa la captura y usa Reanalizar este video para intentarlo de nuevo."));
      const details = element("details"); details.append(element("summary", "", "Detalle del error"), element("p", "", item.error || "Error desconocido")); error.append(details);
    }
    const card = $("#reanalyze-card"); card.hidden = !["COMPLETED", "FAILED"].includes(item.status);
    if (!card.hidden && !$("#reanalyze-submit").onclick) {
      $("#reanalyze-exercise").value = item.exercise || "Otro"; $("#reanalyze-view").value = item.view || "side";
      $("#reanalyze-submit").onclick = async () => {
        const button = $("#reanalyze-submit"); if (button.disabled) return; button.disabled = true;
        $("#reanalyze-status").textContent = "Iniciando reanálisis…";
        try {
          const next = await apiJson(`/api/analyses/${encodeURIComponent(id)}/reanalyze`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({exercise: $("#reanalyze-exercise").value, view: $("#reanalyze-view").value})});
          window.location.assign(`/analyses/${next.id}`);
        } catch (error) { $("#reanalyze-status").textContent = error.message; button.disabled = false; }
      };
    }
  };
  detailPoller = AthleteState.createPoller({
    read: () => apiJson(`/api/analyses/${encodeURIComponent(id)}`), onData: render,
    onError: error => {
      connection.hidden = false;
      const denied = [401, 403, 404].includes(error.status);
      connection.replaceChildren(element("h2", "", denied ? "No podemos acceder al análisis" : "Conexión interrumpida"), element("p", "", denied ? error.message : "No podemos actualizar el estado. El análisis puede seguir en el servidor. Conservamos los últimos datos y volveremos a consultar."));
      const retry = element("button", "secondary-button", "Volver a consultar"); retry.type = "button"; retry.onclick = () => detailPoller.retry(); connection.append(retry);
      if (error.status === 401) { const login = element("a", "button-link", "Iniciar sesión"); login.href = "/login"; connection.append(login); }
    }, schedule: (fn, delay) => window.setTimeout(fn, delay), cancel: timer => window.clearTimeout(timer),
  });
  await detailPoller.retry();
  if (window.location.hash === "#athlete-coach-feedback") $("#athlete-coach-feedback").scrollIntoView({block: "start"});
}

async function setupCoachSelection(id) {
  showView("coach-selection-view");
  const status = $("#coach-selection-status"), list = $("#coach-list");
  $("#selection-back").href = `/analyses/${id}`; status.textContent = "Cargando coaches…";
  let analysis, sending = false, uncertain = false;
  const buttons = new Map();
  const updateRequests = () => {
    const requests = analysis.coach_reviews || [], target = $("#selection-requests-list"); target.replaceChildren();
    $("#selection-requests").hidden = !requests.length;
    for (const review of requests) {
      const row = element("p", "", `${review.coach.name} · ${review.status === "COMPLETED" ? "Revisión disponible" : "Esperando revisión del coach"}`);
      if (review.status === "COMPLETED") { const link = element("a", "button-link secondary-button", "Ver revisión del coach"); link.href = `/analyses/${id}#athlete-coach-feedback`; row.append(link); }
      target.append(row);
    }
    for (const [coachId, button] of buttons) {
      const active = requests.some(r => r.coach.id === coachId && ["PENDING", "IN_REVIEW"].includes(r.status));
      button.disabled = sending || uncertain || active;
      button.textContent = active ? "Revisión ya solicitada" : button.dataset.label;
    }
  };
  try {
    analysis = await apiJson(`/api/analyses/${encodeURIComponent(id)}`);
    if (analysis.status !== "COMPLETED") { window.location.assign(`/analyses/${id}`); return; }
    updateRequests();
    const data = await apiJson("/api/coaches"); list.replaceChildren();
    status.textContent = data.items.length ? "" : "No hay coaches disponibles en este momento. Vuelve más tarde.";
    for (const coach of data.items) {
      const card = element("article", "card coach-card"), button = element("button", "", `Solicitar a ${coach.name}`);
      button.type = "button"; button.dataset.label = button.textContent; buttons.set(coach.id, button);
      button.onclick = async () => {
        if (button.disabled || sending || uncertain) return;
        sending = true; updateRequests(); status.textContent = `Solicitando revisión a ${coach.name}…`;
        try {
          await apiJson(`/api/analyses/${encodeURIComponent(id)}/request-review`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({coach_id: coach.id})});
          setFlash(`Revisión solicitada a ${coach.name}. Puedes consultar su estado desde Mis análisis.`);
          window.location.assign(`/analyses/${id}`);
        } catch (error) {
          status.textContent = error.message;
          // A failed response can arrive after a write committed. Re-read before allowing another request.
          try { analysis = await apiJson(`/api/analyses/${encodeURIComponent(id)}`); }
          catch (_) {
            uncertain = true;
            status.append(element("span", "", " No pudimos comprobar si la solicitud quedó registrada. Vuelve a cargar esta página antes de intentarlo nuevamente."));
          }
          sending = false; updateRequests();
        }
      };
      card.append(element("h2", "", coach.name), element("p", "coach-specialty", coach.specialty), element("p", "muted", coach.bio || "Coach disponible para revisar tu análisis."), button); list.append(card);
    }
    updateRequests();
  } catch (error) { status.textContent = `No se pudieron cargar los coaches: ${error.message}`; }
}

function coachReviewCard(item, coachId) {
  const card = element("article", "card coach-review-row");
  const thumb = item.analysis.thumbnail_url ? element("img", "analysis-thumbnail") : element("div", "analysis-thumbnail thumbnail-placeholder");
  if (item.analysis.thumbnail_url) { thumb.src = item.analysis.thumbnail_url; thumb.loading = "lazy"; thumb.alt = ""; }
  const info = element("div");
  info.append(element("h2", "", item.analysis.exercise || "Análisis"));
  info.append(element("p", "", item.athlete.name));
  info.append(element("p", "muted", `${fmtDate(item.created_at)} · ${item.analysis.load_kg == null ? "Sin carga" : `${item.analysis.load_kg} kg`} · ${item.analysis.repetitions_detected} repeticiones`));
  info.append(element("p", "muted", item.analysis.objective || "Sin objetivo registrado"));
  const side = element("div", "row-side");
  side.append(element("span", `state state-${item.status.toLowerCase()}`, reviewStateLabels[item.status] || item.status));
  if (noReps(item.analysis)) side.append(element("span", "state state-warning", "Sin reps detectadas"));
  if (item.analysis.status === "PROCESSING" && item.analysis.progress != null) {
    side.append(element("span", "muted", `Procesando · ${item.analysis.progress} %`));
  }
  const link = element("a", "button-link", "Revisar");
  link.href = `/coach/reviews/${item.id}`;
  side.append(link);
  card.append(thumb, info, side);
  return card;
}

async function setupCoachReviews() {
  showView("coach-reviews-view");
  const status = $("#coach-reviews-status");
  const list = $("#coach-reviews-list");
  const filter = $("#review-filter");
  let coachId;
  try {
    const user = await sessionUser();
    coachId = user.id;
    $("#coach-identity").textContent = `${user.name} · Coach`;
  } catch (error) {
    status.textContent = `No se pudieron cargar los coaches: ${error.message}`;
    return;
  }
  const render = async () => {
    status.textContent = "Cargando revisiones…";
    list.replaceChildren();
    try {
      const query = new URLSearchParams({ coach_id: coachId });
      const data = await apiJson(`/api/coach/reviews?${query}`);
      const items = data.items;
      const paint = () => {
        list.replaceChildren();
        const visible = filter.value ? items.filter((item) => item.status === filter.value) : items;
        status.textContent = visible.length ? "" : "No hay revisiones para este filtro. Cuando un atleta solicite ayuda, aparecerá aquí.";
        status.classList.toggle("empty-state", visible.length === 0);
        renderFilterChips($("#coach-review-filters"), items, filter.value, reviewStateLabels, (next) => { filter.value = next; paint(); });
        for (const item of visible) list.append(coachReviewCard(item, coachId));
      };
      paint();
    } catch (error) {
      status.textContent = `No se pudieron cargar las revisiones: ${error.message}`;
    }
  };
  filter.addEventListener("change", render);
  await render();
}

function formatVideoTime(seconds) {
  const value = Number.isFinite(seconds) ? seconds : 0;
  const minutes = Math.floor(value / 60);
  const remainder = (value % 60).toFixed(2).padStart(5, "0");
  return `${String(minutes).padStart(2, "0")}:${remainder}`;
}

function jumpCoachVideo(timestamp) {
  const video = $("#coach-annotated-video");
  const seek = () => { video.currentTime = Number(timestamp); video.pause(); };
  if (video.readyState >= HTMLMediaElement.HAVE_METADATA) seek();
  else video.addEventListener("loadedmetadata", seek, { once: true });
}

function renderCoachMoments(item, onDecision, onComment, locked, state) {
  const moments = ReviewState.momentsForReview(item);
  const navigation = $("#coach-moments-navigation");
  const list = $("#coach-review-moments-list");
  navigation.replaceChildren(); list.replaceChildren();
  const hasSelection = moments.some(moment => moment.id === state.selected);
  $("#coach-moments-intro").hidden = hasSelection;
  $("#coach-moments-intro").nextElementSibling.hidden = hasSelection;
  $("#coach-moments-intro").textContent = moments.length
    ? `Encontré ${moments.length} ${moments.length === 1 ? "momento que probablemente quieras revisar" : "momentos que probablemente quieras revisar"}.`
    : "No hay momentos sugeridos disponibles. Puedes continuar revisando el video completo.";
  if (!moments.length) return;
  const visited = moments.filter(moment => state.reviewed.has(moment.id)).length;
  navigation.append(element("p", "moment-progress", `${visited} de ${moments.length} revisados`));
  const select = (moment, focus = true) => {
    state.selected = moment.id;
    jumpCoachVideo(Number(moment.timestamp));
    renderCoachMoments(item, onDecision, onComment, locked, state);
    if (focus) $("#coach-review-moments-list h3")?.focus({ preventScroll: true });
  };
  if (!moments.some(moment => moment.id === state.selected)) {
    const first = element("button", "", "Revisar primer momento"); first.type = "button";
    first.onclick = () => select(moments[0]); navigation.append(first); return;
  }
  const selected = moments.find(moment => moment.id === state.selected);
  const index = moments.indexOf(selected);
  const picker = element("div", "moment-picker");
  for (const [position, moment] of moments.entries()) {
    const button = element("button", moment.id === selected.id ? "is-selected" : "secondary-button", `Momento ${position + 1} · ${formatVideoTime(Number(moment.timestamp))}`);
    button.type = "button"; button.setAttribute("aria-pressed", String(moment.id === selected.id));
    button.onclick = () => select(moment); picker.append(button);
  }
  const momentSelector = element("details", "moment-selector");
  momentSelector.append(element("summary", "", `Momento ${index + 1} de ${moments.length} · Cambiar`), picker);
  navigation.append(momentSelector);
  const heading = element("h3", "", selected.title); heading.tabIndex = -1;
  list.append(element("p", "ai-observation-meta", `${selected.repetition ? `Rep ${selected.repetition} · ` : ""}${formatVideoTime(Number(selected.timestamp))}`), heading,
    element("p", "", selected.description || "Observación automática para revisar."));
  const context = element("details", "moment-context");
  context.append(element("summary", "", "Ver detalles de la sugerencia"),
    element("p", "muted", `Motivo: ${selected.reason || selected.evidence || "Observación generada a partir del análisis del movimiento."}`));
  if (selected.confidence) {
    const confidence = { low: "baja", medium: "media", high: "alta" }[selected.confidence] || String(selected.confidence);
    context.append(element("p", "muted", `Confianza de la sugerencia: ${confidence}. No confirma un error técnico.`));
  }
  list.append(element("p", "muted", selected.decision === "CONFIRMED" ? "IA confirmada por el coach. Esto no crea una anotación para el atleta." : selected.decision === "DISMISSED" ? "Sugerencia descartada. Esto no elimina anotaciones para el atleta." : "Revisar una sugerencia no la confirma ni la comparte con el atleta."));
  const actions = element("div", "form-actions review-moment-controls");
  const action = (label, callback, disabled = locked) => {
    const button = element("button", "secondary-button", label); button.type = "button"; button.disabled = disabled;
    button.onclick = callback; actions.append(button); return button;
  };
  action("Comentar este momento", () => { jumpCoachVideo(Number(selected.timestamp)); onComment(selected); }).className = "";
  action(state.reviewed.has(selected.id) ? "Momento revisado" : "Marcar como revisado", () => {
    state.reviewed.add(selected.id); renderCoachMoments(item, onDecision, onComment, locked, state);
    $("#coach-moments-navigation .moment-progress").textContent += " · Revisado en esta sesión; no se creó una anotación.";
  }, locked || state.reviewed.has(selected.id));
  action("Descartar sugerencia", async () => {
    const result = await onDecision(selected, { decision: "DISMISSED" });
    if (result === false) $("#coach-moments-feedback").textContent = "No se pudo descartar. Puedes reintentar.";
  });
  action("Siguiente momento", () => select(moments[index + 1]), index === moments.length - 1);
  list.append(actions);
  const advanced = element("details", "moment-decision");
  advanced.append(element("summary", "", "Validar o editar la observación IA"));
  const titleLabel = element("label", "", "Título de la observación");
  const title = element("input"); title.value = selected.title; title.maxLength = 240; title.disabled = locked;
  const descriptionLabel = element("label", "", "Descripción");
  const description = element("textarea"); description.value = selected.description || ""; description.maxLength = 800; description.disabled = locked;
  titleLabel.append(title); descriptionLabel.append(description);
  const confirm = element("button", "secondary-button", "Confirmar IA con este contenido"); confirm.type = "button"; confirm.disabled = locked;
  confirm.onclick = async () => {
    if (!title.value.trim() || !description.value.trim()) { $("#coach-moments-feedback").textContent = "Completa título y descripción."; return; }
    const result = await onDecision(selected, { decision: "CONFIRMED", title: title.value, description: description.value });
    if (result === false) $("#coach-moments-feedback").textContent = "No se pudo confirmar. El resumen se conserva.";
  };
  advanced.append(element("p", "muted", "Confirmar registra tu decisión sobre la IA. Para entregar feedback, usa Comentar este momento."), titleLabel, descriptionLabel, confirm);
  context.append(advanced);
  list.append(context);
  const feedback = element("p", "muted"); feedback.id = "coach-moments-feedback"; feedback.setAttribute("role", "status"); list.append(feedback);
}

function renderCoachAnalysis(item, onClassify, onAIDecision, onMomentComment, onCorrection, onMoments) {
  const analysis = item.analysis;
  $("#coach-review-title").textContent = analysis.exercise || "Revisión";
  $("#coach-review-state").textContent = reviewStateLabels[item.status] || item.status;
  $("#coach-review-state").className = `state state-${item.status.toLowerCase()}`;
  $("#coach-review-meta").textContent = `${item.athlete.name} · ${fmtDate(item.created_at)} · ${analysis.load_kg == null ? "Sin carga" : `${analysis.load_kg} kg`} · ${analysis.repetitions_detected} repeticiones`;
  $("#coach-review-objective").textContent = analysis.objective || "Sin objetivo registrado";
  for (const [selector, source] of [["#coach-original-video", analysis.original_video_url], ["#coach-annotated-video", analysis.annotated_video_url]]) {
    if (source && $(selector).getAttribute("src") !== source) $(selector).src = source;
  }
  const video = $("#coach-annotated-video");
  const videoTime = $("#coach-video-time");
  videoTime.textContent = formatVideoTime(video.currentTime);
  video.ontimeupdate = () => { videoTime.textContent = formatVideoTime(video.currentTime); };
  for (const button of document.querySelectorAll("[data-rate]")) {
    button.classList.toggle("is-active", Number(button.dataset.rate) === video.playbackRate);
    button.onclick = () => {
      video.playbackRate = Number(button.dataset.rate);
      for (const rateButton of document.querySelectorAll("[data-rate]")) {
        rateButton.classList.toggle("is-active", rateButton === button);
      }
    };
  }
  const metrics = analysis.analysis_json?.summary_metrics || {};
  $("#coach-metrics").replaceChildren(
    metric("Repeticiones", analysis.repetitions_detected),
    metric("Rodilla mín.", metrics.min_knee_angle == null ? null : `${metrics.min_knee_angle}°`),
    metric("Cadera mín.", metrics.min_hip_angle == null ? null : `${metrics.min_hip_angle}°`),
    metric("Inclinación tronco máx.", metrics.max_trunk_from_vertical == null ? null : `${metrics.max_trunk_from_vertical}°`),
  );
  renderPreflight("#coach-preflight", analysis.analysis_json?.preflight);
  const reps = $("#coach-reps");
  reps.replaceChildren();
  if (!analysis.repetitions.length) reps.textContent = NO_REPS_TIP;
  for (const rep of analysis.repetitions) {
    const row = element("div", "timeline-jump");
    const jump = element("button", "timeline-marker", `Rep ${rep.number}`);
    jump.type = "button";
    jump.setAttribute("aria-label", `Ver repetición ${rep.number}`);
    jump.onclick = (event) => { event.stopPropagation(); jumpCoachVideo(rep.start_s); };
    row.append(jump);
    row.append(element("span", "", `${formatVideoTime(rep.start_s)} → ${formatVideoTime(rep.end_s)} · punto más bajo ${formatVideoTime(rep.bottom_s)}`));
    row.onclick = () => jumpCoachVideo(rep.start_s);
    const classifications = element("span", "rep-classifications");
    for (const [value, label] of [["BEST", "⭐ Mejor"], ["NEEDS_WORK", "⚠ A trabajar"], ["NORMAL", "Normal"]]) {
      const button = element("button", rep.classification === value ? "is-selected" : "", label);
      button.type = "button";
      button.disabled = item.status === "COMPLETED" || rep.correction_status === "DISCARDED";
      button.onclick = (event) => { event.stopPropagation(); onClassify(rep, value); };
      classifications.append(button);
    }
    const correction = element("button", "secondary-button", rep.correction_status === "DISCARDED" ? "Restaurar" : "Descartar");
    correction.type = "button";
    correction.disabled = item.status === "COMPLETED";
    correction.onclick = (event) => { event.stopPropagation(); onCorrection(rep, rep.correction_status === "DISCARDED" ? "ACTIVE" : "DISCARDED"); };
    classifications.append(correction);
    if (rep.correction_status === "DISCARDED") row.classList.add("is-discarded");
    row.append(classifications);
    reps.append(row);
  }
  $("#coach-technical-json").textContent = JSON.stringify(analysis.analysis_json, null, 2);
  onMoments(item, onAIDecision, onMomentComment, item.status === "COMPLETED");
}

function fillAnnotationRepetitions(repetitions) {
  const select = $("#coach-annotation-repetition");
  select.replaceChildren(element("option", "", "Sin repetición"));
  select.options[0].value = "";
  for (const rep of repetitions) {
    const option = element("option", "", `Rep ${rep.number}`);
    option.value = rep.number;
    select.append(option);
  }
}

function renderCoachAnnotations(annotations, editable, onEdit, onDelete) {
  const list = $("#coach-annotations-list");
  const timeline = $("#coach-timeline-annotations");
  list.replaceChildren();
  timeline.replaceChildren();
  if (!annotations.length) {
    list.textContent = "Aún no hay feedback humano para este video.";
    return;
  }
  for (const annotation of annotations) {
    const item = element("article", "annotation-item");
    const time = element("button", "timeline-marker", formatVideoTime(annotation.timestamp_s));
    time.type = "button";
    time.setAttribute("aria-label", `Ver comentario en ${formatVideoTime(annotation.timestamp_s)}`);
    time.onclick = (event) => { event.stopPropagation(); jumpCoachVideo(annotation.timestamp_s); };
    const content = element("div");
    content.append(element("strong", "", annotationLabels[annotation.type] || annotation.type));
    content.append(element("p", "", annotation.text));
    if (annotation.repetition_number != null) content.append(element("span", "muted", `Rep ${annotation.repetition_number}`));
    item.append(time, content);
    item.onclick = () => jumpCoachVideo(annotation.timestamp_s);
    if (editable) {
      const actions = element("div", "annotation-actions");
      const edit = element("button", "", "Editar");
      const remove = element("button", "delete-button", "Eliminar");
      edit.type = remove.type = "button";
      edit.onclick = (event) => { event.stopPropagation(); onEdit(annotation); };
      remove.onclick = (event) => { event.stopPropagation(); onDelete(annotation); };
      actions.append(edit, remove);
      item.append(actions);
    }
    list.append(item);
    const marker = element("button", "timeline-jump");
    marker.type = "button";
    marker.append(element("strong", "timeline-marker", formatVideoTime(annotation.timestamp_s)), element("span", "", `${annotationLabels[annotation.type] || annotation.type} · ${annotation.text}`));
    marker.onclick = () => jumpCoachVideo(annotation.timestamp_s);
    timeline.append(marker);
  }
}

async function setupCoachReviewDetail(id) {
  showView("coach-review-detail-view");
  const error = $("#coach-review-error");
  let coachId;
  $("#coach-review-back").href = "/coach/reviews";
  try { coachId = (await sessionUser()).id; }
  catch (authError) { $("#coach-review-detail-view").classList.add("load-error"); error.hidden = false; error.textContent = authError.message; return; }
  let item;
  let loadVersion = 0;
  let pendingRequests = 0;
  let closing = false;
  const draft = ReviewState.createDraft();
  const momentState = { selected: null, reviewed: new Set() };
  const busyControls = new WeakMap();
  let annotations = [];
  let editingAnnotation = null;
  let annotationTimestamp = null;
  const annotationEditor = $("#coach-annotation-editor");
  const annotationStatus = $("#coach-annotations-status");
  const annotationType = $("#coach-annotation-type");
  const annotationText = $("#coach-annotation-text");
  const annotationRepetition = $("#coach-annotation-repetition");
  const summaryStatus = $("#coach-summary-status");
  const summaryFields = {
    strengths: $("#coach-strengths"),
    main_focus: $("#coach-main-focus"),
    next_session: $("#coach-next-session"),
    summary: $("#coach-summary"),
  };
  const updateReviewUX = () => {
    if (!item) return;
    const locked = item.status === "COMPLETED";
    $("#coach-draft-status").textContent = draft.dirty ? "Cambios sin guardar" : "Sin cambios pendientes";
    $("#coach-draft-status").classList.toggle("draft-dirty", draft.dirty);
    const list = $("#coach-close-requirements"); list.replaceChildren();
    for (const requirement of ReviewState.requirements(item.status, annotations, draft.snapshot())) {
      const row = element("li", requirement.met ? "requirement-met" : "", `${requirement.met ? "Listo" : "Pendiente"} · ${requirement.label}`);
      list.append(row);
    }
    for (const field of Object.values(summaryFields)) field.disabled = locked || closing;
    for (const field of document.querySelectorAll("#coach-annotation-editor input,#coach-annotation-editor textarea,#coach-annotation-editor select,#coach-review-moments-list input,#coach-review-moments-list textarea")) field.disabled = locked || closing || pendingRequests > 0;
    for (const button of document.querySelectorAll("#coach-review-detail-view button:not([data-rate])")) {
      if (closing || pendingRequests > 0) {
        if (!busyControls.has(button)) busyControls.set(button, button.disabled);
        button.disabled = true;
      } else if (busyControls.has(button)) {
        button.disabled = busyControls.get(button); busyControls.delete(button);
      }
    }
    $("#coach-save-summary").disabled = locked || closing || pendingRequests > 0;
    $("#coach-complete-review").disabled = locked || closing || pendingRequests > 0;
    $("#coach-complete-review").textContent = closing ? "Guardando y completando…" : "Guardar y completar revisión";
  };
  const reviewRequest = async (url, options) => {
    pendingRequests++; updateReviewUX();
    try { return await apiJson(url, options); }
    finally { pendingRequests--; updateReviewUX(); }
  };
  for (const [key, field] of Object.entries(summaryFields)) field.addEventListener("input", () => { draft.edit(key, field.value); updateReviewUX(); });
  window.addEventListener("beforeunload", event => {
    if (draft.dirty || (!annotationEditor.hidden && annotationText.value.trim())) { event.preventDefault(); event.returnValue = ""; }
  });
  const saveSummary = async snapshot => reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/summary?coach_id=${encodeURIComponent(coachId)}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(Object.entries(snapshot).map(([key,value]) => [key,value || null]))),
  });
  for (const option of annotationType.options) option.textContent = annotationLabels[option.value] || option.textContent;
  annotationText.placeholder = "Ej: cierra más rápido la extensión de cadera";
  summaryFields.strengths.placeholder = "Ej: buena posición de salida, barra cerca del cuerpo";
  summaryFields.main_focus.placeholder = "Ej: extensión de cadera más rápida";
  summaryFields.next_session.placeholder = "Ej: 3×3 al 70% con foco en el jalón";
  const focusEditor = () => { annotationText.focus({ preventScroll: true }); annotationEditor.scrollIntoView({ behavior: "auto", block: "end" }); };
  const openEditor = (annotation = null, seed = null) => {
    if (!annotationEditor.hidden && annotationText.value.trim()) { annotationStatus.textContent = "Guarda o cancela el comentario abierto antes de cambiar de momento."; focusEditor(); return; }
    editingAnnotation = annotation;
    annotationTimestamp = annotation ? annotation.timestamp_s : (seed?.timestamp_s ?? $("#coach-annotated-video").currentTime);
    annotationEditor.hidden = false;
    $("#coach-annotation-editor-title").textContent = annotation ? "Editar comentario" : "Agregar comentario";
    const timestamp = annotationTimestamp;
    $("#coach-annotation-time").textContent = `Tiempo: ${formatVideoTime(timestamp)}`;
    annotationType.value = annotation?.type || seed?.type || "COMMENT";
    annotationText.value = annotation?.text || seed?.text || "";
    annotationRepetition.value = annotation?.repetition_number || seed?.repetition_number || "";
    focusEditor();
  };
  const loadAnnotations = async () => {
    const data = await reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/annotations?coach_id=${encodeURIComponent(coachId)}`);
    annotations = data.items;
    updateReviewUX();
    const editable = item.status !== "COMPLETED";
    renderCoachAnnotations(annotations, editable, openEditor, async (annotation) => {
      if (!window.confirm("¿Eliminar este comentario?")) return;
      try {
        await reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/annotations/${encodeURIComponent(annotation.id)}?coach_id=${encodeURIComponent(coachId)}`, { method: "DELETE" });
        await loadAnnotations();
      } catch (deleteError) {
        annotationStatus.textContent = deleteError.message;
      }
    });
  };
  const load = async () => {
    const version = ++loadVersion;
    const nextItem = await reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}?coach_id=${encodeURIComponent(coachId)}`);
    if (version !== loadVersion) return;
    item = nextItem;
    renderCoachAnalysis(item, async (rep, classification) => {
      if (closing || pendingRequests || item.status === "COMPLETED") return;
      try {
        await reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/repetitions/${encodeURIComponent(rep.id)}?coach_id=${encodeURIComponent(coachId)}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ classification }),
        });
        await load();
      } catch (classificationError) {
        summaryStatus.textContent = classificationError.message;
      }
    }, async (observation, payload) => {
      if (closing || pendingRequests || item.status === "COMPLETED") return false;
      try {
        await reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/ai-observations/${encodeURIComponent(observation.id)}?coach_id=${encodeURIComponent(coachId)}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
        });
        await load();
      } catch (aiError) {
        summaryStatus.textContent = aiError.message;
        return false;
      }
    }, (moment) => { jumpCoachVideo(moment.timestamp); openEditor(null, { timestamp_s: moment.timestamp, type: "COMMENT", text: moment.title, repetition_number: moment.repetition }); }, async (rep, correction_status) => {
      try {
        await reviewRequest("/api/coach/reviews/" + encodeURIComponent(id) + "/repetitions/" + encodeURIComponent(rep.id) + "?coach_id=" + encodeURIComponent(coachId), {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ correction_status }),
        });
        $("#manual-rep-status").textContent = correction_status === "DISCARDED" ? "Repetición descartada." : "Repetición restaurada.";
        await load();
      } catch (correctionError) {
        $("#manual-rep-status").textContent = correctionError.message;
      }
    }, (current, onDecision, onComment, locked) => renderCoachMoments(current, onDecision, onComment, locked, momentState));
    const selectedRepetition = annotationRepetition.value;
    fillAnnotationRepetitions(item.analysis.repetitions);
    if (!annotationEditor.hidden) annotationRepetition.value = selectedRepetition;
    $("#coach-completed-recipient").textContent = `El feedback ya está disponible para ${item.athlete.name}.`;
    const startCard = $("#coach-start-card");
    startCard.hidden = item.status !== "PENDING";
    $("#coach-completed-card").hidden = item.status !== "COMPLETED";
    $("#coach-start-review").onclick = async () => {
      if (closing || pendingRequests || item.status === "COMPLETED") return;
      try {
        await reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/start?coach_id=${encodeURIComponent(coachId)}`, { method: "PATCH" });
        await load();
      } catch (startError) {
        error.hidden = false;
        error.textContent = startError.message;
      }
    };
    $("#coach-add-annotation").hidden = item.status === "COMPLETED";
    $("#coach-repetition-correction").hidden = item.status === "COMPLETED";
    const values = draft.hydrate(item.summary);
    for (const [key, field] of Object.entries(summaryFields)) {
      field.value = values[key];
      field.disabled = item.status === "COMPLETED";
    }
    $("#coach-save-summary").disabled = item.status === "COMPLETED";
    $("#coach-complete-review").disabled = item.status === "COMPLETED";
    await loadAnnotations();
    updateReviewUX();
  };
  $("#coach-add-annotation").onclick = () => openEditor();
  $("#manual-rep-save").onclick = async () => {
    if (closing || pendingRequests || item.status === "COMPLETED") return;
    const status = $("#manual-rep-status");
    const button = $("#manual-rep-save");
    const rawTimes = ["#manual-rep-start", "#manual-rep-bottom", "#manual-rep-end"].map(selector => $(selector).value.trim());
    const [start_s, bottom_s, end_s] = rawTimes.map(Number);
    if (rawTimes.some(value => value === "") || ![start_s, bottom_s, end_s].every(Number.isFinite)) { status.textContent = "Indica inicio, punto bajo y fin."; return; }
    button.disabled = true;
    try {
      await reviewRequest("/api/coach/reviews/" + encodeURIComponent(id) + "/repetitions?coach_id=" + encodeURIComponent(coachId), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start_s, bottom_s, end_s, correction_note: $("#manual-rep-note").value || null }),
      });
      status.textContent = "Repetición manual agregada.";
      ["#manual-rep-start", "#manual-rep-bottom", "#manual-rep-end", "#manual-rep-note"].forEach(selector => { $(selector).value = ""; });
      await load();
    } catch (manualError) {
      status.textContent = manualError.message;
    } finally {
      button.disabled = false;
    }
  };
  $("#coach-annotation-cancel").onclick = () => { annotationEditor.hidden = true; };
  $("#coach-annotation-save").onclick = async () => {
    if (closing || pendingRequests || item.status === "COMPLETED") return;
    const saveButton = $("#coach-annotation-save");
    saveButton.disabled = true;
    annotationStatus.textContent = "Guardando comentario…";
    const timestamp = editingAnnotation ? editingAnnotation.timestamp_s : annotationTimestamp;
    const payload = {
      type: annotationType.value,
      text: annotationText.value,
      repetition_number: annotationRepetition.value ? Number(annotationRepetition.value) : null,
    };
    try {
      if (editingAnnotation) {
        await reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/annotations/${encodeURIComponent(editingAnnotation.id)}?coach_id=${encodeURIComponent(coachId)}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
        });
      } else {
        await reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/annotations?coach_id=${encodeURIComponent(coachId)}`, {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...payload, timestamp_s: timestamp }),
        });
      }
      annotationEditor.hidden = true;
      annotationStatus.textContent = "Comentario guardado.";
      await load();
    } catch (saveError) {
      annotationStatus.textContent = saveError.message;
    } finally {
      saveButton.disabled = item.status === "COMPLETED";
    }
  };
  $("#coach-save-summary").onclick = async () => {
    if (closing || pendingRequests || item.status === "COMPLETED") return;
    const snapshot = draft.snapshot();
    summaryStatus.textContent = "Guardando resumen…";
    try {
      draft.acknowledge(snapshot, await saveSummary(snapshot));
      const values = draft.snapshot();
      for (const [key,field] of Object.entries(summaryFields)) field.value = values[key];
      summaryStatus.textContent = draft.dirty ? "Resumen guardado; hay cambios posteriores sin guardar." : "Resumen guardado.";
    } catch (saveError) { summaryStatus.textContent = `No se guardó el resumen: ${saveError.message}. Tu borrador se conserva.`; }
    finally { updateReviewUX(); }
  };
  $("#coach-complete-review").onclick = async () => {
    if (closing || pendingRequests) return;
    if (!annotationEditor.hidden && annotationText.value.trim()) { summaryStatus.textContent = "Guarda o cancela el comentario abierto antes de completar."; focusEditor(); return; }
    closing = true; updateReviewUX();
    let completed = false;
    summaryStatus.textContent = "Guardando campos pendientes y verificando requisitos…";
    try {
      await ReviewState.saveAndComplete({ draft, status: () => item.status, annotations: () => annotations, save: saveSummary,
        complete: () => reviewRequest(`/api/coach/reviews/${encodeURIComponent(id)}/complete?coach_id=${encodeURIComponent(coachId)}`, { method: "POST" }),
      });
      item.status = "COMPLETED";
      completed = true;
      summaryStatus.textContent = "Revisión completada. El feedback está disponible y la edición quedó bloqueada.";
      await load();
    } catch (completeError) {
      summaryStatus.textContent = completed
        ? "Revisión completada. No se pudo actualizar la vista; recarga para ver el estado final."
        : `${completeError.message} El contenido se conserva; puedes corregirlo y reintentar.`;
      if (completed) for (const button of document.querySelectorAll("#coach-review-detail-view button:not([data-rate])")) busyControls.set(button, true);
    }
    finally { closing = false; updateReviewUX(); }
  };
  try {
    await load();
  } catch (loadError) {
    $("#coach-review-detail-view").classList.add("load-error");
    error.hidden = false;
    error.textContent = loadError.message;
  }
}

const path = window.location.pathname;
if (path === "/demo") showView("demo-view");
else if (path === "/login") setupLogin();
else if (path === "/para-atletas") setupCommercialAudience("athlete");
else if (path === "/para-coaches") setupCommercialAudience("coach");
else if (path === "/internal/usage") setupUsage();
else if (path === "/coach/analyses/new") setupCoachNewAnalysis();
else if (path === "/coach/athletes/new") setupCoachNewAthlete();
else if (path === "/coach/reviews") setupCoachReviews();
else if (path.startsWith("/coach/reviews/")) setupCoachReviewDetail(path.split("/")[3]);
else if (path === "/analyses") setupList();
else if (path === "/training" || path.startsWith('/training/')) {
  const view = element('section'); view.id = 'training-view';
  $('#workspace').append(view);
  showView('training-view'); window.setupTraining(path.split('/')[2]);
}
else if (path.endsWith("/request-review")) setupCoachSelection(path.split("/")[2]);
else if (path.startsWith("/analyses/") && path !== "/analyses/new") setupDetail(path.split("/")[2]);
else if (path === "/") { showView("landing-view"); setupLandingInteractions(); }
else setupNew();

if (path !== "/" && !["/login", "/demo", "/para-atletas", "/para-coaches"].includes(path)) {
  let navigationCheck = 0;
  async function refreshSessionNavigation() {
    const check = ++navigationCheck;
    const nav = document.querySelector('.functional-nav');
    delete nav.dataset.ready;
    nav.hidden = true;
    document.querySelector('.functional-actions').hidden = true;
    for (const link of nav.querySelectorAll('[data-nav-role]')) link.hidden = true;
    try {
      const user = await sessionUser();
      if (check !== navigationCheck) return;
      const label = $('#session-user');
      if (label) label.textContent = user.name;
      configureNavigation(user);
      setupLogout();
    } catch {
      // Keep the current form intact; never reveal unconfirmed role links.
    }
  }
  refreshSessionNavigation();
  window.addEventListener('pageshow', event => { if (event.persisted) refreshSessionNavigation(); });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') refreshSessionNavigation(); });
}

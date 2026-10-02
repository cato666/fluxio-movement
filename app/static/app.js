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
let detailPollId = null;

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
  const data = await response.json();
  if (!response.ok) {
    const message = typeof data.detail === "string" ? data.detail : data.detail?.message;
    const error = new Error(message || "No se pudo completar la solicitud");
    error.analysisId = data.detail?.analysis_id;
    throw error;
  }
  return data;
}

function showView(id) {
  if (id !== "detail-view" && detailPollId) { window.clearInterval(detailPollId); detailPollId = null; }
  // Las rutas públicas no deben revelar accesos del área autenticada.
  const marketing = ["landing-view", "demo-view", "login-view"].includes(id);
  document.body.classList.toggle("marketing", marketing);
  document.documentElement.classList.toggle("marketing", marketing);
  for (const selector of [".functional-nav", ".functional-actions"]) {
    const item = document.querySelector(selector);
    item.hidden = marketing;
  }
  const marketingNav = document.querySelector(".marketing-nav");
  const marketingActions = document.querySelector(".auth-actions");
  marketingNav.hidden = !marketing;
  marketingActions.hidden = !marketing;
  for (const view of ["landing-view", "login-view", "usage-view", "demo-view", "new-view", "coach-new-analysis-view", "coach-new-athlete-view", "list-view", "detail-view", "coach-selection-view", "coach-reviews-view", "coach-review-detail-view"]) {
    $(`#${view}`).hidden = view !== id;
  }
}

async function sessionUser() { return apiJson("/api/auth/me"); }

function setupLogout() {
  const button = $("#logout-button");
  if (!button) return;
  button.onclick = async () => {
    await apiJson("/api/auth/logout", { method: "POST" });
    window.location.assign("/");
  };
}

function configureNavigation(user) {
  for (const link of document.querySelectorAll("[data-nav-role]")) {
    link.hidden = link.dataset.navRole !== user.role;
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
      metric("Análisis completados", number(totals.completed_runs)),
      metric("Tokens de entrada", number(totals.input_tokens)),
      metric("Tokens de salida", number(totals.output_tokens)),
      metric("Total facturable", number(totals.total_tokens)),
    );
    const models = $("#usage-by-model"); models.replaceChildren();
    if (!data.by_model.length) models.textContent = "Aún no hay análisis con razonamiento IA completado.";
    for (const item of data.by_model) {
      const row = element("div", "rep");
      row.append(element("strong", "", item.model));
      row.append(element("span", "", ` · ${number(item.runs)} análisis · ${number(item.total_tokens)} tokens`));
      models.append(row);
    }
    const recent = $("#usage-recent-runs"); recent.replaceChildren();
    if (!data.recent_runs.length) recent.textContent = "Aún no hay ejecuciones registradas.";
    for (const run of data.recent_runs) {
      const row = element("div", "rep");
      row.append(element("strong", "", run.exercise));
      row.append(element("span", "", ` · ${fmtDate(run.created_at)} · ${run.status}`));
      row.append(element("span", "", ` · entrada ${number(run.input_tokens)} · salida ${number(run.output_tokens)} · total ${number(run.total_tokens)}`));
      recent.append(row);
    }
    status.textContent = "";
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
  const form = $("#analysis-form");
  const button = $("#go");
  const status = $("#status");
  const fileInput = form.elements.file;
  const preview = $("#upload-preview");
  const refresh = () => { button.disabled = !form.checkValidity(); };
  fileInput.addEventListener("change", () => {
    if (preview.src) URL.revokeObjectURL(preview.src);
    const file = fileInput.files[0];
    preview.hidden = !file;
    if (file) {
      preview.src = URL.createObjectURL(file);
      status.textContent = `${file.name} · ${(file.size / 1048576).toFixed(1)} MB`;
    }
    refresh();
  });
  form.addEventListener("input", refresh);
  refresh();
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    button.disabled = true;
    status.textContent = "Subiendo… 0 %";
    const data = new FormData(form);
    if (!data.get("load_kg")) data.delete("load_kg");
    const request = new XMLHttpRequest();
    request.open("POST", "/api/analyses");
    request.upload.onprogress = (progress) => {
      if (progress.lengthComputable) status.textContent = `Subiendo… ${Math.round(progress.loaded / progress.total * 100)} %`;
    };
    request.onload = () => {
      let body = {}; try { body = JSON.parse(request.responseText); } catch (_) {}
      if (request.status === 202 && body.id) { window.location.assign(`/analyses/${body.id}`); return; }
      status.textContent = body.detail?.message || body.detail || "No se pudo iniciar el análisis";
      button.disabled = false;
    };
    request.onerror = () => { status.textContent = "No se pudo subir el video"; button.disabled = false; };
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
      const link = element("a", "button-link", "Ver análisis");
      link.href = `/analyses/${item.id}`;
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
  card.append(element("span", "ai-observation-meta", meta));
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

function renderCoachAIObservations(observations, onDecision, locked = false) {
  const list = $("#coach-ai-observations-list");
  list.replaceChildren();
  if (!observations?.length) { list.textContent = "No hay observaciones automáticas para este análisis."; return; }
  for (const observation of observations) {
    const actions = element("div", "ai-observation-actions");
    for (const [decision, label] of [["CONFIRMED", "Confirmar"], ["DISMISSED", "Descartar"]]) {
      const button = element("button", observation.decision === decision ? "is-selected" : "", label);
      button.type = "button";
      button.disabled = locked;
      button.onclick = (event) => { event.stopPropagation(); onDecision(observation, { decision }); };
      actions.append(button);
    }
    const edit = element("button", "secondary-button", "Modificar");
    edit.type = "button";
    edit.disabled = locked;
    edit.onclick = (event) => {
      event.stopPropagation();
      const title = window.prompt("Título de la observación", observation.title);
      if (title === null) return;
      const description = window.prompt("Descripción de la observación", observation.description);
      if (description === null) return;
      onDecision(observation, { decision: "CONFIRMED", title, description });
    };
    actions.append(edit);
    list.append(aiObservationCard(observation, actions, jumpCoachVideo));
  }
}

function renderReviewMoments(moments, onDecision, onComment, locked = false) {
  const list = $("#coach-review-moments-list"); list.replaceChildren();
  if (!moments?.length) { list.textContent = "No encontramos eventos destacados. Puedes revisar el video completo."; return; }
  for (const moment of moments) {
    const actions = element("div", "ai-observation-actions");
    const watch = element("button", "secondary-button", "Ver momento"); watch.type = "button"; watch.onclick = (event) => { event.stopPropagation(); jumpCoachVideo(moment.timestamp); };
    const confirm = element("button", moment.decision === "CONFIRMED" ? "is-selected" : "", "Confirmar"); confirm.type = "button"; confirm.disabled = locked; confirm.onclick = (event) => { event.stopPropagation(); onDecision(moment, {decision:"CONFIRMED"}); };
    const dismiss = element("button", moment.decision === "DISMISSED" ? "is-selected" : "", "Descartar"); dismiss.type = "button"; dismiss.disabled = locked; dismiss.onclick = (event) => { event.stopPropagation(); onDecision(moment, {decision:"DISMISSED"}); };
    const comment = element("button", "secondary-button", "Agregar comentario"); comment.type = "button"; comment.disabled = locked; comment.onclick = (event) => { event.stopPropagation(); onComment(moment); };
    actions.append(watch, confirm, dismiss, comment); list.append(aiObservationCard(moment, actions, jumpCoachVideo));
  }
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
  $("#original-video").src = item.original_video_url;
  $("#annotated-video").src = item.annotated_video_url;
  const metrics = item.analysis_json?.summary_metrics || {};
  $("#metrics").replaceChildren(
    metric("Repeticiones", item.repetitions_detected),
    metric("Rodilla mín.", metrics.min_knee_angle == null ? null : `${metrics.min_knee_angle}°`),
    metric("Cadera mín.", metrics.min_hip_angle == null ? null : `${metrics.min_hip_angle}°`),
    metric("Inclinación tronco máx.", metrics.max_trunk_from_vertical == null ? null : `${metrics.max_trunk_from_vertical}°`),
  );
  renderPreflight("#detail-preflight", item.analysis_json?.preflight);
  const reps = $("#reps");
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
    video.scrollIntoView({ behavior: "smooth", block: "center" });
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
  const container = $("#athlete-coach-feedback");
  container.replaceChildren();
  for (const review of item.completed_coach_reviews || []) {
    const card = element("section", "card coach-feedback-card");
    card.append(element("h2", "", "Tu coach revisó este entrenamiento"));
    card.append(element("p", "muted", `${review.coach.name} · ${review.coach.specialty}`));
    const repText = (label, rep) => rep ? `${label}: Rep ${rep.number}` : `${label}: Sin selección`;
    card.append(element("p", "", repText("⭐ Mejor repetición", review.best_repetition)));
    card.append(element("p", "", repText("⚠ Repetición a trabajar", review.work_repetition)));
    for (const [title, value] of [["Fortalezas", review.strengths], ["Principal punto a trabajar", review.main_focus], ["Próxima sesión", review.next_session], ["Resumen adicional", review.summary]]) {
      if (value) {
        card.append(element("h3", "", title), element("p", "", value));
      }
    }
    if (review.annotations.length) {
      card.append(element("h3", "", "Anotaciones del coach"));
      for (const annotation of review.annotations) {
        const note = element("div", "rep");
        note.append(element("strong", "", `${formatVideoTime(annotation.timestamp_s)} · ${annotationLabels[annotation.type] || annotation.type}`));
        note.append(element("p", "", annotation.text));
        const watch = element("button", "watch-moment", "Ver momento");
        watch.type = "button";
        watch.setAttribute("aria-label", `Ver momento ${formatVideoTime(annotation.timestamp_s)} en el video anotado`);
        watch.onclick = () => seekAthleteVideo(annotation.timestamp_s);
        note.append(watch);
        card.append(note);
      }
    }
    container.append(card);
  }
  container.hidden = !item.completed_coach_reviews?.length;
}

async function setupDetail(id) {
  showView("detail-view");
  try {
    const item = await apiJson(`/api/analyses/${encodeURIComponent(id)}`);
    $("#detail-title").textContent = item.exercise || "Análisis anterior";
    $("#detail-status").textContent = stateLabels[item.status] || item.status;
    $("#detail-status").classList.add(`state-${item.status.toLowerCase()}`);
    const viewLabel = item.view === "front" ? "Vista frontal" : "Vista de costado";
    $("#detail-meta").textContent = `${fmtDate(item.created_at)} · ${item.load_kg == null ? "Sin carga" : `${item.load_kg} kg`} · ${viewLabel} · ${item.repetitions_detected} repeticiones`;
    $("#detail-objective").textContent = item.objective || "Sin objetivo registrado";
    const feedback = $("#detail-action-feedback");
    const flash = takeFlash();
    feedback.hidden = !flash;
    feedback.textContent = flash || "";
    const requestLink = $("#request-review-link");
    const cta = $("#review-cta");
    const reanalyzeCard = $("#reanalyze-card");
    const reanalyzeExercise = $("#reanalyze-exercise");
    const reanalyzeView = $("#reanalyze-view");
    const reanalyzeSubmit = $("#reanalyze-submit");
    const reanalyzeStatus = $("#reanalyze-status");
    if (item.status === "COMPLETED") {
      requestLink.href = `/analyses/${item.id}/request-review`;
      cta.hidden = false;
    } else {
      cta.hidden = true;
    }
    reanalyzeCard.hidden = !["COMPLETED", "FAILED"].includes(item.status);
    if (!reanalyzeCard.hidden) {
      reanalyzeExercise.value = item.exercise || "Otro";
      reanalyzeView.value = item.view || "side";
      reanalyzeSubmit.onclick = async () => {
        reanalyzeSubmit.disabled = true;
        reanalyzeStatus.textContent = "Iniciando reanálisis…";
        try {
          const next = await apiJson(`/api/analyses/${encodeURIComponent(item.id)}/reanalyze`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ exercise: reanalyzeExercise.value, view: reanalyzeView.value }),
          });
          window.location.assign(`/analyses/${next.id}`);
        } catch (reanalyzeError) {
          reanalyzeStatus.textContent = reanalyzeError.message;
          reanalyzeSubmit.disabled = false;
        }
      };
    }
    if (item.status === "COMPLETED") {
      renderCompleted(item);
      // The worker marks an analysis complete only after the optional IA layer
      // settles. Keep this fallback for analyses created by older deployments.
      if (["PENDING", "RUNNING"].includes(item.ai_reasoning?.status)) {
        window.setTimeout(() => setupDetail(id), 1500);
      }
    }
    renderCoachReviews(item);
    renderAthleteCoachFeedback(item);
    if (item.status === "PENDING" || item.status === "PROCESSING") {
      const stageLabels = { uploading: "Subiendo", validating_exercise: "Validando ejercicio", reanalyzing: "Reanalizando video", analyzing: "Analizando movimiento", annotating: "Generando video anotado", finalizing: "Finalizando", generating_observations: "Generando observaciones automáticas" };
      feedback.hidden = false;
      feedback.className = "card progress-card";
      feedback.replaceChildren(element("strong", "", stageLabels[item.stage] || "Preparando análisis"));
      const progress = element("div", "analysis-progress");
      progress.setAttribute("role", "progressbar"); progress.setAttribute("aria-valuemin", "0"); progress.setAttribute("aria-valuemax", "100"); progress.setAttribute("aria-valuenow", String(item.progress || 0));
      const fill = element("i"); fill.style.width = `${item.progress || 0}%`; progress.append(fill);
      feedback.append(element("span", "muted", `${item.progress || 0} %`), progress);
      if (detailPollId) window.clearInterval(detailPollId);
      detailPollId = window.setInterval(async () => {
        const next = await apiJson(`/api/analyses/${encodeURIComponent(id)}`);
        if (next.status === "COMPLETED" || next.status === "FAILED") { window.clearInterval(detailPollId); detailPollId = null; setupDetail(id); }
        else { const now = $(".analysis-progress"); if (now) { now.setAttribute("aria-valuenow", String(next.progress || 0)); now.firstChild.style.width = `${next.progress || 0}%`; } }
      }, 1500);
      return;
    }
    if (item.status === "FAILED") {
      $("#detail-error").hidden = false;
      $("#detail-error").textContent = `No pudimos completar el análisis. El registro quedó guardado para que puedas intentarlo de nuevo. Detalle técnico: ${item.error || "Error desconocido"}`;
    }
  } catch (error) {
    $("#detail-title").textContent = "Análisis no disponible";
    $("#detail-error").hidden = false;
    $("#detail-error").textContent = error.message;
  }
}

async function setupCoachSelection(id) {
  showView("coach-selection-view");
  const back = $("#selection-back");
  const status = $("#coach-selection-status");
  const list = $("#coach-list");
  back.href = `/analyses/${id}`;
  status.textContent = "Cargando coaches…";
  try {
    const analysis = await apiJson(`/api/analyses/${encodeURIComponent(id)}`);
    if (analysis.status !== "COMPLETED") {
      window.location.assign(`/analyses/${id}`);
      return;
    }
    const data = await apiJson("/api/coaches");
    status.textContent = "";
    for (const coach of data.items) {
      const card = element("article", "card coach-card");
      const heading = element("h2", "", coach.name);
      const specialty = element("p", "coach-specialty", coach.specialty);
      const bio = element("p", "muted", coach.bio || "Coach disponible para revisar tu análisis.");
      const button = element("button", "", `Solicitar a ${coach.name}`);
      button.type = "button";
      button.addEventListener("click", async () => {
        button.disabled = true;
        status.textContent = `Solicitando revisión a ${coach.name}…`;
        try {
          await apiJson(`/api/analyses/${encodeURIComponent(id)}/request-review`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ coach_id: coach.id }),
          });
          setFlash(`Revisión solicitada a ${coach.name}.`);
          window.location.assign(`/analyses/${id}`);
        } catch (error) {
          status.textContent = error.message;
          button.disabled = false;
        }
      });
      card.append(heading, specialty, bio, button);
      list.append(card);
    }
  } catch (error) {
    status.textContent = `No se pudieron cargar los coaches: ${error.message}`;
  }
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
  video.currentTime = timestamp;
  video.pause();
}

function renderCoachAnalysis(item, onClassify, onAIDecision, onMomentComment, onCorrection) {
  const analysis = item.analysis;
  $("#coach-review-title").textContent = analysis.exercise || "Revisión";
  $("#coach-review-state").textContent = reviewStateLabels[item.status] || item.status;
  $("#coach-review-state").className = `state state-${item.status.toLowerCase()}`;
  $("#coach-review-meta").textContent = `${item.athlete.name} · ${fmtDate(item.created_at)} · ${analysis.load_kg == null ? "Sin carga" : `${analysis.load_kg} kg`} · ${analysis.repetitions_detected} repeticiones`;
  $("#coach-review-objective").textContent = analysis.objective || "Sin objetivo registrado";
  $("#coach-original-video").src = analysis.original_video_url;
  $("#coach-annotated-video").src = analysis.annotated_video_url;
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
    row.append(element("strong", "timeline-marker", `Rep ${rep.number}`));
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
  renderCoachAIObservations(item.ai_observations, onAIDecision, item.status === "COMPLETED");
  renderReviewMoments(item.review_moments, onAIDecision, onMomentComment, item.status === "COMPLETED");
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
    const time = element("strong", "timeline-marker", formatVideoTime(annotation.timestamp_s));
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
  catch (authError) { error.hidden = false; error.textContent = authError.message; return; }
  let item;
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
  for (const option of annotationType.options) option.textContent = annotationLabels[option.value] || option.textContent;
  annotationText.placeholder = "Ej: cierra más rápido la extensión de cadera";
  summaryFields.strengths.placeholder = "Ej: buena posición de salida, barra cerca del cuerpo";
  summaryFields.main_focus.placeholder = "Ej: extensión de cadera más rápida";
  summaryFields.next_session.placeholder = "Ej: 3×3 al 70% con foco en el jalón";
  const openEditor = (annotation = null, seed = null) => {
    editingAnnotation = annotation;
    annotationTimestamp = annotation ? annotation.timestamp_s : (seed?.timestamp_s ?? $("#coach-annotated-video").currentTime);
    annotationEditor.hidden = false;
    $("#coach-annotation-editor-title").textContent = annotation ? "Editar comentario" : "Agregar comentario";
    const timestamp = annotationTimestamp;
    $("#coach-annotation-time").textContent = `Tiempo: ${formatVideoTime(timestamp)}`;
    annotationType.value = annotation?.type || seed?.type || "COMMENT";
    annotationText.value = annotation?.text || seed?.text || "";
    annotationRepetition.value = annotation?.repetition_number || seed?.repetition_number || "";
    annotationText.focus();
  };
  const loadAnnotations = async () => {
    const data = await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/annotations?coach_id=${encodeURIComponent(coachId)}`);
    annotations = data.items;
    const editable = item.status !== "COMPLETED";
    renderCoachAnnotations(annotations, editable, openEditor, async (annotation) => {
      if (!window.confirm("¿Eliminar este comentario?")) return;
      try {
        await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/annotations/${encodeURIComponent(annotation.id)}?coach_id=${encodeURIComponent(coachId)}`, { method: "DELETE" });
        await loadAnnotations();
      } catch (deleteError) {
        annotationStatus.textContent = deleteError.message;
      }
    });
  };
  const load = async () => {
    item = await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}?coach_id=${encodeURIComponent(coachId)}`);
    renderCoachAnalysis(item, async (rep, classification) => {
      try {
        await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/repetitions/${encodeURIComponent(rep.id)}?coach_id=${encodeURIComponent(coachId)}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ classification }),
        });
        await load();
      } catch (classificationError) {
        summaryStatus.textContent = classificationError.message;
      }
    }, async (observation, payload) => {
      try {
        await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/ai-observations/${encodeURIComponent(observation.id)}?coach_id=${encodeURIComponent(coachId)}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
        });
        await load();
      } catch (aiError) {
        summaryStatus.textContent = aiError.message;
      }
    }, (moment) => { jumpCoachVideo(moment.timestamp); openEditor(null, { timestamp_s: moment.timestamp, type: "COMMENT", text: moment.title, repetition_number: moment.repetition }); }, async (rep, correction_status) => {
      try {
        await apiJson("/api/coach/reviews/" + encodeURIComponent(id) + "/repetitions/" + encodeURIComponent(rep.id) + "?coach_id=" + encodeURIComponent(coachId), {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ correction_status }),
        });
        $("#manual-rep-status").textContent = correction_status === "DISCARDED" ? "Repetición descartada." : "Repetición restaurada.";
        await load();
      } catch (correctionError) {
        $("#manual-rep-status").textContent = correctionError.message;
      }
    });
    fillAnnotationRepetitions(item.analysis.repetitions);
    const startCard = $("#coach-start-card");
    startCard.hidden = item.status !== "PENDING";
    $("#coach-completed-card").hidden = item.status !== "COMPLETED";
    $("#coach-start-review").onclick = async () => {
      try {
        await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/start?coach_id=${encodeURIComponent(coachId)}`, { method: "PATCH" });
        await load();
      } catch (startError) {
        error.hidden = false;
        error.textContent = startError.message;
      }
    };
    $("#coach-add-annotation").hidden = item.status === "COMPLETED";
    $("#coach-repetition-correction").hidden = item.status === "COMPLETED";
    for (const [key, field] of Object.entries(summaryFields)) {
      field.value = item.summary?.[key] || "";
      field.disabled = item.status === "COMPLETED";
    }
    $("#coach-save-summary").disabled = item.status === "COMPLETED";
    $("#coach-complete-review").disabled = item.status === "COMPLETED";
    annotationEditor.hidden = true;
    await loadAnnotations();
  };
  $("#coach-add-annotation").onclick = () => openEditor();
  $("#manual-rep-save").onclick = async () => {
    const status = $("#manual-rep-status");
    const button = $("#manual-rep-save");
    const rawTimes = ["#manual-rep-start", "#manual-rep-bottom", "#manual-rep-end"].map(selector => $(selector).value.trim());
    const [start_s, bottom_s, end_s] = rawTimes.map(Number);
    if (rawTimes.some(value => value === "") || ![start_s, bottom_s, end_s].every(Number.isFinite)) { status.textContent = "Indica inicio, punto bajo y fin."; return; }
    button.disabled = true;
    try {
      await apiJson("/api/coach/reviews/" + encodeURIComponent(id) + "/repetitions?coach_id=" + encodeURIComponent(coachId), {
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
        await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/annotations/${encodeURIComponent(editingAnnotation.id)}?coach_id=${encodeURIComponent(coachId)}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
        });
      } else {
        await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/annotations?coach_id=${encodeURIComponent(coachId)}`, {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...payload, timestamp_s: timestamp }),
        });
      }
      annotationEditor.hidden = true;
      annotationStatus.textContent = "Comentario guardado.";
      await load();
    } catch (saveError) {
      annotationStatus.textContent = saveError.message;
      saveButton.disabled = false;
    }
  };
  $("#coach-save-summary").onclick = async () => {
    const saveButton = $("#coach-save-summary");
    saveButton.disabled = true;
    summaryStatus.textContent = "Guardando resumen…";
    const payload = Object.fromEntries(Object.entries(summaryFields).map(([key, field]) => [key, field.value || null]));
    try {
      await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/summary?coach_id=${encodeURIComponent(coachId)}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      });
      summaryStatus.textContent = "Resumen guardado.";
      await load();
    } catch (summaryError) {
      summaryStatus.textContent = summaryError.message;
      saveButton.disabled = false;
    }
  };
  $("#coach-complete-review").onclick = async () => {
    const completeButton = $("#coach-complete-review");
    completeButton.disabled = true;
    summaryStatus.textContent = "Finalizando revisión…";
    try {
      await apiJson(`/api/coach/reviews/${encodeURIComponent(id)}/complete?coach_id=${encodeURIComponent(coachId)}`, { method: "POST" });
      summaryStatus.textContent = "Revisión finalizada.";
      await load();
    } catch (completeError) {
      summaryStatus.textContent = completeError.message;
      completeButton.disabled = false;
    }
  };
  try {
    await load();
  } catch (loadError) {
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
else if (path.endsWith("/request-review")) setupCoachSelection(path.split("/")[2]);
else if (path.startsWith("/analyses/") && path !== "/analyses/new") setupDetail(path.split("/")[2]);
else if (path === "/") { showView("landing-view"); setupLandingInteractions(); }
else setupNew();

if (path !== "/" && !["/login", "/demo", "/para-atletas", "/para-coaches"].includes(path)) {
  sessionUser().then((user) => {
    const label = $("#session-user");
    if (label) label.textContent = user.name;
    configureNavigation(user);
    setupLogout();
  }).catch(() => {});
}

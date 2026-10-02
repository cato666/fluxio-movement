(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.AthleteState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function reviewAction(item) {
    const reviews = item.coach_reviews || [];
    if (item.completed_coach_reviews?.length || reviews.some(r => r.status === "COMPLETED")) return {
      state: "AVAILABLE", label: "Ver revisión del coach", badge: "Revisión disponible",
      href: `/analyses/${item.id}#athlete-coach-feedback`,
      copy: "Tu coach dejó feedback. Revisa el punto principal y prepara tu próxima sesión.",
    };
    if (reviews.some(r => ["PENDING", "IN_REVIEW"].includes(r.status))) return {
      state: "WAITING", label: "Esperando revisión del coach", badge: "Esperando coach",
      href: `/analyses/${item.id}#review-status`,
      copy: "La solicitud está enviada. Puedes volver desde Mis análisis para ver si la revisión está disponible.",
    };
    return {state: "NONE", label: "Solicitar revisión a un coach", href: `/analyses/${item.id}/request-review`,
      copy: "Elige un coach para interpretar estos resultados y definir qué trabajar después."};
  }
  function requirements(fields) {
    return [
      {label: "Selecciona un ejercicio", ready: !!fields.exercise},
      {label: "Escribe tu objetivo", ready: !!fields.objective?.trim()},
      {label: "Selecciona la vista del video", ready: !!fields.view},
      {label: fields.file ? "Usa un video MP4, MOV, M4V o AVI" : "Selecciona un video", ready: !!fields.file && /\.(mp4|mov|m4v|avi)$/i.test(fields.file.name)},
    ];
  }
  function refreshDelay(item) {
    if (["PENDING", "PROCESSING"].includes(item.status) || ["PENDING", "RUNNING"].includes(item.ai_reasoning?.status)) return 1500;
    if (item.status === "COMPLETED" && (item.coach_reviews || []).some(r => ["PENDING", "IN_REVIEW"].includes(r.status))) return 15000;
    return null;
  }
  // Serial reads: an interrupted connection never changes the processing status.
  function createPoller({read, onData, onError, schedule = setTimeout, cancel = clearTimeout}) {
    let timer, stopped = false, busy = false;
    const plan = delay => { if (!stopped && delay != null) timer = schedule(retry, delay); };
    async function retry() {
      if (stopped || busy) return;
      cancel(timer); busy = true;
      try {
        const item = await read();
        if (!stopped) { onData(item); plan(refreshDelay(item)); }
      } catch (error) {
        if (!stopped) { onError(error); if (![401, 403, 404].includes(error.status)) plan(3000); }
      } finally { busy = false; }
    }
    return {retry, stop() { stopped = true; cancel(timer); }};
  }
  return {reviewAction, requirements, refreshDelay, createPoller};
});

/* Review-only state; no routes, storage or API contracts. */
(function (root, factory) {
  const exports = factory();
  if (typeof module === "object" && module.exports) module.exports = exports;
  else root.ReviewState = exports;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const keys = ["strengths", "main_focus", "next_session", "summary"];
  const normalize = data => Object.fromEntries(keys.map(key => [key, data?.[key] || ""]));
  function createDraft() {
    let values = normalize(), saved = normalize(), initialized = false;
    return {
      hydrate(server) {
        const next = normalize(server);
        for (const key of keys) if (!initialized || values[key] === saved[key]) values[key] = next[key];
        saved = next; initialized = true;
        return { ...values };
      },
      edit(key, value) { if (keys.includes(key)) values[key] = value; },
      snapshot() { return { ...values }; },
      get dirty() { return keys.some(key => values[key] !== saved[key]); },
      acknowledge(sent, server = sent) {
        const next = normalize(server);
        for (const key of keys) if (values[key] === sent[key]) values[key] = next[key];
        saved = next;
        return { ...values };
      },
    };
  }
  function requirements(status, annotations, summary) {
    return [
      { label: "Revisión iniciada", met: status === "IN_REVIEW" || status === "COMPLETED" },
      { label: "Al menos una anotación", met: annotations.length > 0 },
      { label: "Punto principal", met: Boolean(summary.main_focus?.trim()) },
      { label: "Próxima sesión", met: Boolean(summary.next_session?.trim()) },
    ];
  }
  async function saveAndComplete({ draft, status, annotations, save, complete }) {
    const snapshot = draft.snapshot();
    // Persist pending fields even if other requirements still need attention.
    if (draft.dirty) draft.acknowledge(snapshot, await save(snapshot));
    const missing = requirements(status(), annotations(), draft.snapshot()).filter(row => !row.met);
    if (missing.length) throw new Error(`Falta: ${missing.map(row => row.label.toLowerCase()).join(", ")}.`);
    if (draft.dirty) throw new Error("El resumen cambió mientras se guardaba. Revisa los cambios y vuelve a completar.");
    return complete();
  }
  function momentsForReview(item) {
    const seen = new Set();
    return [...(item.review_moments || []), ...(item.ai_observations || [])].filter(moment => {
      if (moment.timestamp == null || !Number.isFinite(Number(moment.timestamp)) || seen.has(moment.id)) return false;
      seen.add(moment.id); return true;
    });
  }
  return { createDraft, requirements, saveAndComplete, momentsForReview };
});

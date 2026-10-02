// Presentation only: move the existing controls, preserving handlers and values.
(() => {
  const viewport = window.matchMedia('(max-width: 600px)');
  const disclosures = [];
  function disclose(node, label) {
    if (!node) return;
    const details = document.createElement('details');
    details.className = 'mobile-disclosure';
    const summary = document.createElement('summary');
    summary.textContent = label;
    node.before(details);
    details.append(summary);
    const content = document.createElement('div');
    content.className = 'mobile-disclosure-content';
    details.append(content);
    content.append(node);
    disclosures.push({ details, content, node });
  }
  const targets = [
    ['#coach-review-meta', 'Ver contexto del atleta'],
    ['#coach-review-detail-view > .review-readiness', 'Ver requisitos para completar'],
    ['#coach-review-detail-view > .grid > .card:last-child', 'Ver video original'],
    ['#coach-review-detail-view > .card:has(#coach-metrics)', 'Ver métricas del análisis'],
    ['#coach-repetition-correction', 'Corregir detecciones · Ver detalles'],
    ['.context-repetitions', 'Ver repeticiones y comentarios'],
    ['#detail-completed .card:has(#metrics)', 'Ver métricas'],
    ['#detail-completed .card:has(#reps)', 'Ver repeticiones'],
    ['#analysis-form label:has([name="load_kg"])', 'Agregar carga · opcional'],
    ['#coach-analysis-form label:has([name="load_kg"])', 'Agregar carga · opcional'],
  ];
  function update() {
    if (viewport.matches && !disclosures.length) {
      for (const [selector, label] of targets) disclose(document.querySelector(selector), label);
    } else if (!viewport.matches) {
      for (const {details, node} of disclosures) { details.before(node); details.remove(); }
      disclosures.length = 0;
    }
  }
  update();
  viewport.addEventListener('change', update);
})();

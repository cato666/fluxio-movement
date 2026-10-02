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

  // Labels, destinations and role visibility stay owned by the existing router.
  const paths = [
    'M12 5v14M5 12h14',
    'M6 4h12v16H6zM9 8h6M9 12h6M9 16h4',
    'M4 5h16v14H4zM4 13h5l2 3h2l2-3h5',
    'M12 16V4M7 9l5-5 5 5M4 15v5h16v-5',
    'M9 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M2 20v-2a5 5 0 0 1 10 0v2M18 12v8M14 16h8',
    'M5 20V10M12 20V4M19 20v-7',
  ];
  document.querySelectorAll('.functional-nav a').forEach((link, index) => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('class', 'mobile-nav-icon');
    const path = document.createElementNS(svg.namespaceURI, 'path');
    path.setAttribute('d', paths[index]);
    svg.append(path);
    link.prepend(svg);
  });

  // VisualViewport covers Safari's keyboard without guessing OS or blocking zoom.
  const visual = window.visualViewport;
  let frame = 0;
  let restingHeight = visual?.height || 0;
  let restingWidth = visual?.width || 0;
  function syncKeyboard() {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      const active = document.activeElement;
      const editing = active?.matches('input:not([type="file"]), textarea, select');
      if (visual && visual.scale === 1 && (!editing || Math.abs(visual.width - restingWidth) > 80)) {
        restingHeight = visual.height;
        restingWidth = visual.width;
      }
      const keyboard = viewport.matches && editing && visual && visual.scale === 1
        && Math.max(document.documentElement.clientHeight, restingHeight) - visual.height > 150;
      document.body.classList.toggle('mobile-keyboard-open', Boolean(keyboard));
      if (keyboard) {
        const bounds = active.getBoundingClientRect();
        const bottom = visual.offsetTop + visual.height;
        if (bounds.bottom > bottom - 16 || bounds.top < visual.offsetTop) {
          active.scrollIntoView({ block: 'nearest', behavior: 'instant' });
        }
      }
    });
  }
  visual?.addEventListener('resize', syncKeyboard);
  document.addEventListener('focusin', syncKeyboard);
  document.addEventListener('focusout', syncKeyboard);
  viewport.addEventListener('change', syncKeyboard);

  document.querySelectorAll('input[name="username"]').forEach(input => {
    input.setAttribute('autocapitalize', 'none');
    input.setAttribute('autocorrect', 'off');
    input.setAttribute('spellcheck', 'false');
    input.setAttribute('enterkeyhint', 'next');
  });
  document.querySelectorAll('input[type="password"]').forEach(input => input.setAttribute('enterkeyhint', 'done'));
  document.querySelectorAll('textarea').forEach(input => input.setAttribute('enterkeyhint', 'enter'));
})();

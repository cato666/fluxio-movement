/* Lucide 0.468.0, vendored locally. Brand marks remain brand artwork. */
window.fluxioIcon = function(name, className = 'fluxio-icon') {
  const node = window.lucide?.icons[name];
  if (!node) return null;
  const svg = window.lucide.createElement(node, {width:20,height:20,'stroke-width':1.75});
  svg.setAttribute('aria-hidden','true');
  svg.setAttribute('stroke-width','1.75');
  svg.classList.add(className);
  return svg;
};

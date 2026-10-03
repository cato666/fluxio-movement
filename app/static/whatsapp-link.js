/* Account linking uses the existing authenticated identity contracts. */
window.mountWhatsAppLink = function(root) {
  const make = (tag, text, className) => {
    const node = document.createElement(tag); node.textContent = text || '';
    if (className) node.className = className; return node;
  };
  const panel = make('details', '', 'training-whatsapp');
  const summary = make('summary', 'Registrar por WhatsApp');
  const content = make('div', '', 'training-whatsapp-content');
  const status = make('p', 'Vincula tu WhatsApp para enviar fotos, audio o texto. Solo necesitas hacerlo una vez.');
  status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const actions = make('div', '', 'training-whatsapp-actions');
  panel.append(summary, content); content.append(status, actions); root.append(panel);
  let disposed = false, busy = false, challenge = null, expiryTimer = null;
  const destination = document.querySelector('meta[name="whatsapp-destination"]')?.content || '';
  const request = async (method = 'GET', path = 'identity') => {
    const response = await fetch('/api/whatsapp/' + path, {method});
    if (response.status === 404) throw Error('WhatsApp no está disponible en este momento. Puedes registrar desde la web.');
    if (response.status === 401) throw Error('Tu sesión expiró. Vuelve a iniciar sesión.');
    if (response.status === 429) throw Error('Espera antes de generar otro código y vuelve a intentarlo.');
    if (!response.ok) throw Error('No pudimos completar la vinculación. Inténtalo nuevamente.');
    return response.json();
  };
  const button = (label, action, secondary = false) => {
    const node = make('button', label, secondary ? 'secondary-button' : ''); node.type = 'button';
    node.onclick = () => run(action); actions.append(node); return node;
  };
  async function run(action) {
    if (busy || disposed) return;
    busy = true; status.classList.remove('is-error');
    actions.querySelectorAll('button').forEach(node => { node.disabled = true; });
    try { await action(); }
    catch { if (!disposed) showError('No pudimos conectar o completar la acción. Revisa tu conexión y vuelve a intentarlo.'); }
    finally {
      busy = false;
      if (!disposed) actions.querySelectorAll('button').forEach(node => { node.disabled = false; });
    }
  }
  function clearQR() { content.querySelector('.training-whatsapp-qr')?.remove(); }
  function showError(message) {
    clearQR();
    status.textContent = message; status.classList.add('is-error'); actions.replaceChildren();
    button('Reintentar', check, true);
  }
  function pending() {
    clearQR();
    actions.replaceChildren();
    if (!challenge || Date.parse(challenge.expires_at) <= Date.now()) {
      challenge = null; status.textContent = 'El código venció. Genera otro para continuar.';
      button('Generar otro código', generate); return;
    }
    status.textContent = 'Envía el mensaje preparado desde tu WhatsApp. Al volver, comprobaremos la vinculación.';
    if (/^[1-9][0-9]{7,14}$/.test(destination)) {
      const open = make('a', 'Abrir WhatsApp', 'button-link');
      open.href = 'https://wa.me/' + destination + '?text=' + encodeURIComponent(challenge.code);
      open.target = '_blank'; open.rel = 'noopener noreferrer'; actions.append(open);
      if (window.qrcodegen) {
        try {
          const qr = window.qrcodegen.QrCode.encodeText(open.href, window.qrcodegen.QrCode.Ecc.MEDIUM);
          const figure = make('figure', '', 'training-whatsapp-qr');
          const canvas = make('canvas');
          const border = 4, scale = 6, size = (qr.size + border * 2) * scale;
          canvas.width = canvas.height = size;
          canvas.setAttribute('role', 'img');
          canvas.setAttribute('aria-label', 'QR para abrir WhatsApp en tu teléfono con el mensaje de vinculación');
          const context = canvas.getContext('2d');
          context.fillStyle = '#fff'; context.fillRect(0, 0, size, size);
          context.fillStyle = '#000';
          for (let y = 0; y < qr.size; y++) for (let x = 0; x < qr.size; x++) {
            if (qr.getModule(x, y)) context.fillRect((x + border) * scale, (y + border) * scale, scale, scale);
          }
          figure.append(canvas, make('figcaption', 'Escanea con tu teléfono o haz clic en Abrir WhatsApp para continuar en este equipo. Envía el mensaje para completar la vinculación.'));
          content.insertBefore(figure, actions);
        } catch { /* The clickable link and copy alternative remain available. */ }
      }
    } else {
      status.textContent = 'Copia el código y envíalo al WhatsApp de Fluxio. La apertura automática aún no está configurada.';
    }
    button('Copiar código', async () => {
      try { await navigator.clipboard.writeText(challenge.code); status.textContent = 'Código copiado. Envíalo al WhatsApp de Fluxio antes de que venza.'; }
      catch {
        if (!content.querySelector('textarea')) {
          const label = make('label', 'Código de vinculación');
          const field = make('textarea'); field.readOnly = true; field.value = challenge.code;
          label.append(field); content.insertBefore(label, actions); field.focus(); field.select();
        }
        status.textContent = 'No pudimos copiar automáticamente. Selecciona y copia el código mostrado.';
      }
    }, true);
    button('Ya lo envié', check, true);
  }
  async function check() {
    status.textContent = 'Comprobando vinculación…';
    try {
      const identity = await request(); if (disposed) return;
      clearQR(); actions.replaceChildren(); status.classList.remove('is-error');
      if (identity.linked) {
        challenge = null; clearTimeout(expiryTimer); content.querySelector('label')?.remove();
        summary.textContent = 'WhatsApp vinculado';
        status.textContent = 'WhatsApp vinculado. Envía una foto de tu WOD y cuéntanos tu resultado.';
        button('Desvincular WhatsApp', async () => {
          if (!window.confirm('¿Desvincular WhatsApp? Los nuevos mensajes dejarán de asociarse a tu cuenta. Tus entrenamientos se conservan.')) return;
          await request('DELETE'); await check();
        }, true);
      } else {
        summary.textContent = 'Registrar por WhatsApp';
        if (challenge) pending();
        else {
          status.textContent = 'Vincula tu WhatsApp para registrar entrenamientos con fotos, audio o texto. Solo necesitas hacerlo una vez.';
          button('Vincular mi WhatsApp', generate);
        }
      }
    } catch (error) { if (!disposed) showError(error.message); }
  }
  async function generate() {
    status.textContent = 'Preparando tu vinculación…';
    try {
      const result = await request('POST', 'link-challenges'); if (disposed) return;
      challenge = result; content.querySelector('label')?.remove(); pending();
      clearTimeout(expiryTimer);
      expiryTimer = setTimeout(() => { if (!disposed) run(check); }, Math.max(0, Date.parse(result.expires_at) - Date.now()));
    } catch (error) { if (!disposed) showError(error.message); }
  }
  panel.addEventListener('toggle', () => { if (panel.open) run(check); });
  const onVisible = () => { if (!document.hidden && panel.open) run(check); };
  document.addEventListener('visibilitychange', onVisible);
  return () => { disposed = true; challenge = null; clearTimeout(expiryTimer); document.removeEventListener('visibilitychange', onVisible); panel.remove(); };
};

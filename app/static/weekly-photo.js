(() => {
  const openPhoto = (source, trigger) => {
    const dialog = document.createElement('dialog');
    dialog.className = 'weekly-photo-modal';
    dialog.setAttribute('aria-label', 'Foto del entrenamiento');
    const close = document.createElement('button');
    close.type = 'button'; close.textContent = 'Cerrar ×'; close.autofocus = true;
    const image = document.createElement('img'); image.alt = 'Foto del entrenamiento'; image.src = source;
    const error = document.createElement('p'); error.hidden = true; error.setAttribute('role', 'alert');
    error.textContent = 'No pudimos cargar la foto. Cierra y vuelve a intentarlo.';
    image.onerror = () => { image.hidden = true; error.hidden = false; };
    close.onclick = () => dialog.close();
    dialog.addEventListener('keydown', event => { if (event.key === 'Tab') { event.preventDefault(); close.focus(); } });
    dialog.onclick = event => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    };
    dialog.onclose = () => { dialog.remove(); trigger.focus(); };
    dialog.append(close, image, error); document.body.append(dialog); dialog.showModal();
  };
  document.querySelectorAll('.recap-feature-photo > img').forEach(image => {
    const button = document.createElement('button'); button.type = 'button'; button.className = 'weekly-photo-open';
    button.setAttribute('aria-label', 'Ampliar foto del entrenamiento');
    image.before(button); button.append(image); button.onclick = () => openPhoto(image.src, button);
  });
  document.querySelectorAll('.recap-photo-link').forEach(link => {
    link.onclick = event => { event.preventDefault(); openPhoto(link.href, link); };
  });
})();

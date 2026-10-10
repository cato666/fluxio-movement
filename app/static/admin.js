/* Administrative UI uses textContent for all account and audit data. */
window.setupAdministration = async function () {
  const view = element('section'); view.id = 'admin-view';
  $('#workspace').append(view); showView('admin-view');
  view.innerHTML = `<h1>Administración</h1><p class="muted">Gestiona cuentas, acceso y límites de uso.</p>
    <nav class="admin-tabs" aria-label="Secciones de administración">
      <button type="button" data-tab="users" aria-pressed="true">Usuarios</button><button type="button" data-tab="settings" aria-pressed="false">Planes y organización</button><button type="button" data-tab="audit" aria-pressed="false">Auditoría</button>
    </nav><p id="admin-status" role="status" aria-live="polite"></p><div id="admin-content"></div>`;
  const content = view.querySelector('#admin-content'), status = view.querySelector('#admin-status');
  const request = (url, method, body) => apiJson(url, {method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  const roles = {ATHLETE: 'Atleta', COACH: 'Coach', SYSTEM_ADMIN: 'Administrador'};
  const run = async (action) => { status.textContent = 'Cargando…'; try { await action(); status.textContent = ''; } catch (error) { status.textContent = error.message; } };
  function label(form, title, control) { const node = element('label', '', title); node.append(control); form.append(node); return control; }
  function input(form, title, name, value = '', type = 'text') { const node = document.createElement('input'); node.name = name; node.type = type; node.value = value ?? ''; return label(form, title, node); }
  function select(form, title, name, options, value) { const node = document.createElement('select'); node.name = name; for (const [key, text] of Object.entries(options)) { const option = element('option', '', text); option.value = key; node.append(option); } node.value = value; return label(form, title, node); }
  function editor(user = {}) {
    content.replaceChildren(element('h2', '', user.id ? 'Editar usuario' : 'Crear usuario'));
    const form = element('form', 'admin-form'); content.append(form);
    const name = input(form, 'Nombre', 'name', user.name); name.required = true; name.maxLength = 160;
    const username = input(form, 'Usuario de acceso', 'username', user.username); username.required = true; username.pattern = '[a-zA-Z0-9._-]{3,40}';
    input(form, 'Correo', 'email', user.email, 'email');
    const role = select(form, 'Rol', 'role', roles, user.role || 'ATHLETE'); role.disabled = Boolean(user.id);
    if (user.id) form.append(element('p', 'muted', 'El rol conserva las relaciones e historial de esta cuenta.'));
    select(form, 'Plan', 'plan', {FREE: 'Free', PAID: 'Pago'}, user.plan || 'FREE');
    select(form, 'Estado', 'is_active', {true: 'Activo', false: 'Desactivado'}, String(user.is_active ?? true));
    const password = input(form, user.id ? 'Nueva contraseña (opcional)' : 'Contraseña inicial', 'password', '', 'password'); password.minLength = 8; password.maxLength = 200; password.required = !user.id; password.autocomplete = 'new-password';
    const actions = element('div', 'admin-actions'); const save = element('button', 'primary', 'Guardar usuario'); save.type = 'submit';
    const cancel = element('button', '', 'Volver'); cancel.type = 'button'; cancel.onclick = () => run(users); actions.append(save, cancel); form.append(actions);
    form.onsubmit = async event => { event.preventDefault(); save.disabled = true; status.textContent = 'Guardando…';
      const body = Object.fromEntries(new FormData(form)); body.role = user.role || body.role; body.is_active = body.is_active === 'true'; body.email ||= null; body.password ||= null;
      try { await request(user.id ? `/api/admin/users/${user.id}` : '/api/admin/users', user.id ? 'PUT' : 'POST', body); await users(); status.textContent = 'Usuario guardado.'; } catch(error) { status.textContent = error.message; } finally { save.disabled = false; }
    };
  }
  async function users() {
    const data = await apiJson('/api/admin/users'); content.replaceChildren();
    const toolbar = element('div', 'admin-actions'); const search = document.createElement('input'); search.type = 'search'; search.placeholder = 'Buscar por nombre, usuario o correo'; search.setAttribute('aria-label', 'Buscar usuarios');
    const filter = document.createElement('select'); filter.setAttribute('aria-label', 'Filtrar usuarios');
    for (const [key, text] of Object.entries({all: 'Todos', FREE: 'Free', PAID: 'Pago', active: 'Activos', inactive: 'Desactivados', ...roles})) { const option = element('option', '', text); option.value = key; filter.append(option); }
    const create = element('button', 'primary', 'Crear usuario'); create.onclick = () => editor(); toolbar.append(search, filter, create); content.append(toolbar);
    const list = element('div', 'admin-list'); content.append(list);
    function render() { list.replaceChildren(); const rows = data.items.filter(user => `${user.name} ${user.username} ${user.email || ''}`.toLocaleLowerCase().includes(search.value.toLocaleLowerCase()) && (filter.value === 'all' || user.plan === filter.value || user.role === filter.value || (filter.value === 'active' && user.is_active) || (filter.value === 'inactive' && !user.is_active)));
      if (!rows.length) list.append(element('p', 'muted', 'No hay usuarios con estos filtros.'));
      for (const user of rows) { const row = element('article', 'admin-row'); const info = element('div'); info.append(element('h3', '', user.name), element('p', 'muted', `${user.username} · ${user.email || 'Sin correo'}`), element('p', '', `${roles[user.role]} · ${user.plan === 'FREE' ? 'Free' : 'Pago'} · ${user.is_active ? 'Activo' : 'Desactivado'}`), element('p', 'muted', `${user.usage.used}/${user.usage.monthly_limit} interacciones este mes · Último acceso: ${fmtDate(user.last_login_at)}`)); const edit = element('button', '', 'Editar'); edit.setAttribute('aria-label', `Editar a ${user.name}`); edit.onclick = () => editor(user); row.append(info, edit); list.append(row); }
    } search.oninput = render; filter.onchange = render; render();
  }
  async function settings() {
    const data = await apiJson('/api/admin/settings'); content.replaceChildren(element('h2', '', 'Planes y límites mensuales'), element('p', 'muted', 'Cada solicitud de análisis, reanálisis, interpretación o dictado consume una interacción, aunque falle. El periodo se reinicia cada mes en UTC.'));
    const form = element('form', 'admin-form'); content.append(form);
    const controls = {};
    for (const plan of ['FREE', 'PAID']) { const section = element('fieldset'); section.append(element('legend', '', plan === 'FREE' ? 'Free' : 'Pago')); form.append(section); const limit = input(section, 'Interacciones por mes', `${plan}-limit`, data.plans[plan].monthly_limit, 'number'); limit.min = 0; limit.max = 1000000; limit.required = true; const operations = {};
      for (const [key, title] of Object.entries({ANALYZE: 'Análisis y reanálisis de video', INTERPRET: 'Interpretación de WOD', TRANSCRIBE: 'Dictado de entrenamiento'})) { const control = input(section, title, key, key, 'checkbox'); control.checked = data.plans[plan].enabled_operations.includes(key); operations[key] = control; } controls[plan] = {limit, operations}; }
    const save = element('button', 'primary', 'Guardar planes'); form.append(save);
    form.onsubmit = async event => { event.preventDefault(); save.disabled = true; try { const body = {}; for (const [plan, fields] of Object.entries(controls)) body[plan] = {monthly_limit: Number(fields.limit.value), enabled_operations: Object.keys(fields.operations).filter(key => fields.operations[key].checked)}; await request('/api/admin/plans', 'PUT', body); status.textContent = 'Planes guardados.'; } catch(error) {status.textContent = error.message;} finally { save.disabled = false; } };
    content.append(element('h2', '', 'Organización')); const organization = element('form', 'admin-form'); content.append(organization); input(organization, 'Nombre', 'name', data.organization.name).required = true; input(organization, 'Correo de contacto', 'contact_email', data.organization.contact_email, 'email'); const orgSave = element('button', 'primary', 'Guardar organización'); organization.append(orgSave); organization.onsubmit = async event => { event.preventDefault(); orgSave.disabled = true; try { await request('/api/admin/organization', 'PUT', Object.fromEntries(new FormData(organization))); status.textContent = 'Organización guardada.'; } catch(error) {status.textContent = error.message;} finally {orgSave.disabled = false;} };
    content.append(element('h2', '', 'Permisos por rol')); for (const [role, description] of Object.entries(data.roles)) content.append(element('p', '', `${roles[role]}: ${description}`));
  }
  async function history() { const data = await apiJson('/api/admin/audit'); content.replaceChildren(element('h2', '', 'Últimos 100 cambios')); if (!data.items.length) content.append(element('p', 'muted', 'Todavía no hay cambios administrativos.')); for (const item of data.items) { const detail = element('details', 'admin-audit'); detail.append(element('summary', '', `${fmtDate(item.created_at)} · ${item.actor} · ${item.action}`), element('p', 'muted', item.target), element('pre', '', JSON.stringify(item.changes, null, 2))); content.append(detail); } }
  for (const button of view.querySelectorAll('[data-tab]')) button.onclick = () => { for (const tab of view.querySelectorAll('[data-tab]')) tab.setAttribute('aria-pressed', String(tab === button)); run(button.dataset.tab === 'users' ? users : button.dataset.tab === 'settings' ? settings : history); };
  await run(users);
};

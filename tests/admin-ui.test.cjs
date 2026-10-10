const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('C:/Users/desarrollo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

test('administration renders and saves users and policies on desktop and mobile', async () => {
  const server = http.createServer((req, res) => {
    const filename = req.url.split('?')[0].startsWith('/static/') ? path.join(process.cwd(), 'app', req.url.split('?')[0]) : path.join(process.cwd(), 'app/static/index.html');
    res.setHeader('Content-Type', filename.endsWith('.js') ? 'text/javascript' : filename.endsWith('.css') ? 'text/css' : filename.endsWith('.woff2') ? 'font/woff2' : 'text/html');
    try { res.end(fs.readFileSync(filename)); } catch { res.statusCode = 404; res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    const users = [{id:'test-user', name:'Atleta de prueba', username:'atleta', email:'atleta@example.com', role:'ATHLETE', plan:'FREE', is_active:true, usage:{used:2, monthly_limit:10}}];
    const settings = {plans: {FREE:{monthly_limit:10,enabled_operations:['ANALYZE','INTERPRET','TRANSCRIBE']},PAID:{monthly_limit:200,enabled_operations:['ANALYZE','INTERPRET','TRANSCRIBE']}},organization:{name:'Fluxio Movement',contact_email:''},roles:{SYSTEM_ADMIN:'Administración',ATHLETE:'Entrenamientos propios',COACH:'Revisiones'}};
    let saved;
    await page.route('**/api/**', route => {
      const url = new URL(route.request().url());
      if (route.request().method() !== 'GET') { saved = route.request().postDataJSON(); return route.fulfill({json:{ok:true}}); }
      return route.fulfill({json:url.pathname === '/api/auth/me' ? {name:'Administrador',role:'SYSTEM_ADMIN'} : url.pathname.endsWith('/users') ? {items:users} : url.pathname.endsWith('/settings') ? settings : {items:[]}});
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/admin`);
    await page.getByRole('heading',{name:'Atleta de prueba'}).waitFor();
    assert.equal(await page.locator('#training-view').count(), 0);
    await page.screenshot({path:'.impeccable/admin-desktop.png',fullPage:true});
    await page.getByRole('button',{name:'Editar a Atleta de prueba'}).click();
    await page.locator('select[name=plan]').selectOption('PAID');
    await page.getByRole('button',{name:'Guardar usuario'}).click();
    await page.getByRole('heading',{name:'Atleta de prueba'}).waitFor();
    assert.equal(saved.plan,'PAID');
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:'.impeccable/admin-mobile.png',fullPage:true});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
    await page.getByRole('button',{name:'Planes y organización'}).click();
    await page.getByRole('button',{name:'Guardar planes'}).waitFor();
    await page.getByRole('button',{name:'Guardar planes'}).click();
    await page.getByText('Planes guardados.',{exact:true}).waitFor();
    assert.equal(saved.FREE.monthly_limit,10);
    await page.screenshot({path:'.impeccable/admin-plans-mobile.png',fullPage:true});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
    assert.deepEqual(errors,[]);
  } finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
});

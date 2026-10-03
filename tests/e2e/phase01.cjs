// Real UI -> HTTP -> shared services -> disposable PostgreSQL.
// External AI and pose inference are deterministic in tests/e2e/app.py.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.PHASE01_E2E_URL;
if (!base || !/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(base)) {
  throw Error('PHASE01_E2E_URL must point to the isolated local fixture server');
}

(async () => {
  const browser = await chromium.launch({headless:true, args:[
    '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream',
  ]});
  const context = await browser.newContext({viewport:{width:390,height:844}, permissions:['microphone']});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.setDefaultTimeout(15000);
  async function login(username) {
    await page.goto(base + '/login');
    await page.locator('#login-form [name=username]').fill(username);
    await page.locator('#login-form [name=password]').fill('demo1234');
    await page.locator('#login-form button').click();
    await page.waitForURL(url => url.pathname === (username === 'gaston' ? '/analyses' : '/coach/reviews'));
  }
  async function save(label = 'Guardar sesión') {
    await page.getByRole('button',{name:label,exact:true}).click();
    await page.waitForURL(url => url.pathname === '/training');
    await page.locator('.training-entry').first().waitFor();
  }
  try {
    await login('gaston');
    // Text, explicit confirmation, read and edit through the existing UI.
    await page.goto(base + '/training/new');
    await page.getByLabel('Descripción del entrenamiento').fill('AMRAP 12 minutos: 10 thrusters');
    await page.getByRole('button',{name:'Interpretar WOD',exact:true}).click();
    await page.getByRole('heading',{name:'Revisa tu entrenamiento'}).waitFor();
    assert.equal((await (await context.request.get(base + '/api/training-sessions')).json()).items.length, 0);
    await page.locator('[name=result_text]').fill('5 rondas');
    await save();
    let sessions = (await (await context.request.get(base + '/api/training-sessions')).json()).items;
    assert.equal(sessions.length,1);
    const textSession = sessions[0];
    await page.goto(base + '/training/' + textSession.id);
    await page.getByRole('button',{name:'Editar entrenamiento',exact:true}).click();
    await page.locator('[name=result_text]').fill('6 rondas');
    await save('Guardar cambios');
    console.log('PASS Bitácora texto: propuesta no guardada, confirmación, lectura y edición');

    // Image passes real upload validation, private storage, interpretation and save.
    await page.goto(base + '/training/new');
    await page.locator('#training-view input[type=file]').setInputFiles('results/phase01/e2e-fixtures/board.png');
    await page.locator('img.training-photo').waitFor();
    await page.getByRole('button',{name:'Interpretar WOD',exact:true}).click();
    await page.getByRole('heading',{name:'Revisa tu entrenamiento'}).waitFor();
    await save();
    sessions = (await (await context.request.get(base + '/api/training-sessions')).json()).items;
    const photoSession = sessions.find(s => s.source_image_id);
    assert.ok(photoSession);
    const imageUrl = base + '/api/training-sessions/images/' + photoSession.source_image_id;
    const image = await context.request.get(imageUrl);
    assert.equal(image.status(),200);
    assert.equal(image.headers()['cache-control'],'private, no-store');
    const guest = await browser.newContext();
    assert.equal((await guest.request.get(imageUrl)).status(),401);
    await guest.close();
    console.log('PASS Bitácora foto: carga, interpretación, guardado y privacidad');

    // Browser recording -> actual FFmpeg normalization -> controlled provider -> save.
    await page.goto(base + '/training/new');
    await page.getByRole('button',{name:'Dictar entrenamiento',exact:true}).click();
    await page.getByRole('button',{name:'Terminar grabación',exact:true}).waitFor();
    await page.waitForTimeout(1400); // Obtain a non-empty MediaRecorder segment.
    await page.getByRole('button',{name:'Terminar grabación',exact:true}).click();
    await page.getByRole('button',{name:'Transcribir audio',exact:true}).click();
    await page.waitForFunction(() => document.querySelector('#training-view textarea').value.includes('Hice 5 rondas'));
    await page.getByRole('button',{name:'Interpretar WOD',exact:true}).click();
    await page.getByRole('heading',{name:'Revisa tu entrenamiento'}).waitFor();
    await save();
    assert.equal((await (await context.request.get(base + '/api/training-sessions')).json()).items.length,3);
    console.log('PASS Bitácora audio: micrófono, FFmpeg, transcripción, propuesta y confirmación');

    // Persisted analysis with controlled pose inference; real HTTP worker/media/reviews.
    const uploaded = await context.request.post(base + '/api/analyses', {multipart:{
      exercise:'Sentadilla',objective:'Revisar profundidad',view:'side',
      file:{name:'video.mp4',mimeType:'video/mp4',buffer:fs.readFileSync('results/phase01/e2e-fixtures/video.mp4')},
    }});
    assert.equal(uploaded.status(),202,await uploaded.text());
    const analysisId = (await uploaded.json()).id;
    await page.goto(base + '/analyses/' + analysisId);
    await page.locator('#detail-completed').waitFor({state:'visible'});
    assert.equal((await context.request.get(base + '/uploads/' + analysisId + '.mp4')).status(),200);
    await page.goto(base + '/analyses/' + analysisId + '/request-review');
    await page.getByRole('button',{name:'Solicitar a Carlos',exact:true}).click();
    await page.waitForURL(url => url.pathname === '/analyses/' + analysisId);
    const detail = await (await context.request.get(base + '/api/analyses/' + analysisId)).json();
    const reviewId = detail.coach_reviews[0].id;
    console.log('PASS Athlete UX: análisis persistido, media y solicitud de revisión');

    await login('carlos');
    await page.goto(base + '/coach/reviews/' + reviewId);
    await page.locator('#coach-start-review').click();
    await page.locator('#coach-add-annotation').click();
    await page.locator('#coach-annotation-text').fill('Mantén el tronco estable.');
    await page.locator('#coach-annotation-save').click();
    await page.locator('#coach-annotation-editor').waitFor({state:'hidden'});
    await page.locator('#coach-main-focus').fill('Profundidad');
    await page.locator('#coach-next-session').fill('Tres series con pausa');
    await page.locator('#coach-complete-review').click();
    await page.locator('#coach-completed-card').waitFor({state:'visible'});
    console.log('PASS Coach UX: iniciar, comentar, guardar y completar revisión');

    await login('gaston');
    await page.goto(base + '/analyses/' + analysisId);
    await page.locator('#athlete-coach-feedback').waitFor({state:'visible'});
    assert.match(await page.locator('#athlete-coach-feedback').innerText(), /Profundidad/);
    assert.match(await page.locator('#athlete-coach-feedback').innerText(), /Tres series con pausa/);
    assert.deepEqual(errors,[]);
    console.log('PASS Athlete UX: feedback del coach visible; sin errores JavaScript');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode=1;});

// Real HTTP, PostgreSQL, authentication and media. No paid services are called.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.WEEKLY_E2E_URL || 'http://localhost:18770';
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const owner = await browser.newContext({viewport:{width:1440,height:1000}});
    const page = await owner.newPage();
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    assert.equal((await owner.request.post(base+'/api/auth/login', {data:{username:'gaston',password:'demo1234'}})).status(),200);
    const photo = await owner.request.post(base+'/api/training-sessions/images', {multipart:{file:{
      name:'board.png',mimeType:'image/png',buffer:fs.readFileSync('results/phase01/e2e-fixtures/board.png')}}});
    assert.equal(photo.status(),201); const image = await photo.json();
    const today = new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Santiago'}).format(new Date());
    for (const [title,rpe] of [['Fuerza · Sentadilla',7],['Metcon · AMRAP 12',9]]) {
      assert.equal((await owner.request.post(base+'/api/training-sessions',{data:{trained_on:today,title,
        workout:'5 rondas: 10 sentadillas y 200 m de remo',result_text:'Completado · 50 kg',
        adaptations:'Menor carga en la última ronda',rpe,source_image_id:image.id}})).status(),201);
    }
    await page.goto(base+'/training');
    const week = page.locator('.training-week');
    await week.getByText('2 entrenamientos registrados · 1 día activo',{exact:true}).waitFor();
    await week.getByRole('button',{name:'Semana anterior',exact:true}).click();
    await week.getByText('No hay entrenamientos registrados en esta semana.',{exact:true}).waitFor();
    await week.getByRole('button',{name:'Esta semana',exact:true}).click();
    await week.getByText('2 entrenamientos registrados · 1 día activo',{exact:true}).waitFor();
    await week.getByRole('button',{name:'Crear enlace para compartir',exact:true}).click();
    const input = week.getByLabel('Enlace para compartir', {exact:true}); await input.waitFor();
    const url = await input.inputValue();
    assert.match(url,/\/shared\/week\/[A-Za-z0-9_-]{43}$/);
    const publicContext = await browser.newContext({viewport:{width:1440,height:1000}});
    const shared = await publicContext.newPage();
    assert.equal((await shared.goto(url)).status(),200);
    await shared.getByRole('heading',{name:'Semana de entrenamiento'}).waitFor();
    assert.equal(await shared.locator('img').count(),2);
    await shared.waitForFunction(()=>[...document.images].every(image=>image.complete && image.naturalWidth>0));
    fs.mkdirSync('results/weekly',{recursive:true});
    for (const [name, target] of [['journal',page],['shared',shared]]) {
      for (const width of [1440,390]) {
        await target.setViewportSize({width,height:1000});
        assert.equal(await target.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
        await target.screenshot({path:`results/weekly/${name}-${width}.png`,fullPage:true});
      }
    }
    await week.getByRole('button',{name:'Revocar enlaces de esta semana',exact:true}).click();
    await week.getByText('Los enlaces de esta semana ya no permiten acceder.',{exact:true}).waitFor();
    assert.equal((await shared.goto(url)).status(),404);
    assert.deepEqual(errors,[]);
    console.log('Weekly E2E passed: navigation, sharing, anonymous photos, desktop/mobile, revocation.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});

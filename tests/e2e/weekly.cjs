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
      name:'board.png',mimeType:'image/png',buffer:fs.readFileSync(process.env.WEEKLY_E2E_PHOTO || 'results/phase01/e2e-fixtures/board.png')}}});
    assert.equal(photo.status(),201); const image = await photo.json();
    const today = new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Santiago'}).format(new Date());
    for (const [title,rpe] of [['Fuerza · Sentadilla',7],['Metcon · AMRAP 12',9]]) {
      assert.equal((await owner.request.post(base+'/api/training-sessions',{data:{trained_on:today,title,
        workout:'5 rondas: 10 sentadillas y 200 m de remo',result_text:'Completado · 50 kg',
        adaptations:'Menor carga en la última ronda',rpe,source_image_id:image.id}})).status(),201);
    }
    await page.goto(base+'/training');
    const week = page.locator('.training-week');
    await week.locator('.weekly-compact-metrics dd').first().filter({hasText:'2'}).waitFor();
    await week.getByRole('button',{name:'Semana anterior',exact:true}).click();
    await week.getByText('No hay entrenamientos registrados en esta semana.',{exact:true}).waitFor();
    await week.getByRole('button',{name:'Esta semana',exact:true}).click();
    await week.locator('.weekly-compact-metrics dd').first().filter({hasText:'2'}).waitFor();
    await week.getByRole('button',{name:/Compartir semana/}).click();
    await week.getByRole('button',{name:'Crear enlace para compartir',exact:true}).click();
    const input = week.getByLabel('Enlace para compartir', {exact:true}); await input.waitFor();
    const url = await input.inputValue();
    assert.match(url,/\/shared\/week\/[A-Za-z0-9_-]{43}$/);
    const publicContext = await browser.newContext({viewport:{width:1440,height:1000}});
    const shared = await publicContext.newPage();
    assert.equal((await shared.goto(url)).status(),200);
    await shared.getByRole('heading',{name:'Tu semana en movimiento'}).waitFor();
    assert.equal(await shared.locator('img').count(),3);
    assert.equal(await shared.locator('.recap-feature').count(),1);
    assert.equal(await shared.locator('.recap-entry').count(),2);
    await shared.waitForFunction(()=>[...document.images].every(image=>image.complete && image.naturalWidth>0));
    const captureDir = process.env.WEEKLY_CAPTURE_DIR || 'results/weekly';
    fs.mkdirSync(captureDir,{recursive:true});
    await week.getByRole('button',{name:'Cerrar compartir semana'}).click();
    for (const [name, target] of [['journal',page],['shared',shared]]) {
      for (const width of [1440,768,430,390,320]) {
        await target.setViewportSize({width,height:1000});
        await target.getByRole('heading',{level:1}).click();
        await target.evaluate(()=>window.scrollTo(0,0));
        await target.waitForTimeout(240);
        assert.equal(await target.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
        if (name === 'journal') {
          assert.equal(await week.locator('.weekly-summary-overview').isVisible(),true);
          if(width===1440)assert.ok(await week.evaluate(node=>node.getBoundingClientRect().height)<280);
        } else {
          assert.equal(await target.locator('.recap-metrics dt').evaluateAll(labels=>labels.every(label=>{const text=document.createRange();text.selectNodeContents(label); const bounds=label.parentElement.getBoundingClientRect();return [...text.getClientRects()].every(rect=>rect.left>=bounds.left && rect.right<=bounds.right+1);})),true,'Las etiquetas de métricas deben caber en sus propias tarjetas');
        }
        await target.screenshot({path:`${captureDir}/${name}-${width}.png`,fullPage:true});
      }
    }
    for (const width of [1440,768,430,390,320]) {
      await page.setViewportSize({width,height:1000});
      await page.waitForTimeout(220);
      await page.screenshot({path:`${captureDir}/expanded-${width}.png`,fullPage:true});
      await week.getByRole('button',{name:/Compartir semana/}).click();
      await page.waitForTimeout(220);
      await page.screenshot({path:`${captureDir}/sheet-${width}.png`,fullPage:false});
      await week.getByRole('button',{name:'Cerrar compartir semana'}).click();
    }
    await page.reload();
    await week.getByRole('button',{name:/Compartir semana/}).click();
    await week.locator('.weekly-link-row').waitFor();
    await week.getByRole('button',{name:'Revocar enlaces de esta semana',exact:true}).click();
    await week.getByText('Los enlaces de esta semana ya no permiten acceder.',{exact:true}).waitFor();
    assert.equal((await shared.goto(url)).status(),404);
    assert.deepEqual(errors,[]);
    console.log('Weekly E2E passed: navigation, sharing, anonymous photos, desktop/mobile, revocation.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});

const fs = require('node:fs');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const exercises = JSON.parse(fs.readFileSync('app/services/exercise_library/exercises.json', 'utf8'));
  const categories = JSON.parse(fs.readFileSync('app/services/exercise_library/taxonomy.json', 'utf8'));
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('http://library.test/**', route => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/exercise-categories') return route.fulfill({json: categories});
    if (url.pathname === '/api/exercises') return route.fulfill({json: exercises.filter(item => [...url.searchParams].every(([key, value]) => item[key] === value))});
    const file = url.pathname === '/exercises' ? 'app/static/exercise-library.html' : `app${url.pathname}`;
    return route.fulfill({body: fs.readFileSync(file), contentType: file.endsWith('.html') ? 'text/html' : file.endsWith('.css') ? 'text/css' : 'application/javascript'});
  });
  await page.route('https://www.youtube.com/**', route => route.fulfill({body: '<p>External reference player</p>', contentType: 'text/html'}));
  await page.goto('http://library.test/exercises');
  await page.locator('#exercise-list button').first().waitFor();
  assert.equal(await page.locator('#exercise-list button').count(), 20);
  await page.getByRole('button', {name: /^Clean /}).click();
  assert.equal(await page.locator('#detail h2').textContent(), 'Clean');
  assert.ok((await page.locator('iframe').getAttribute('src')).includes('Ty14ogq_Vok'));
  fs.mkdirSync('results/exercise-library', {recursive: true});
  for (const width of [1440, 390]) {
    await page.setViewportSize({width, height: 900});
    await page.screenshot({path: `results/exercise-library/${width}.png`, fullPage: true});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  }
  await page.locator('[name=category]').selectOption('weightlifting');
  await page.waitForFunction(() => document.querySelector('#status').textContent === '4 ejercicios');
  await page.locator('[name=analysis_status]').selectOption('reference_only');
  await page.waitForFunction(() => document.querySelector('#status').textContent === '2 ejercicios');
  await page.locator('[name=priority]').selectOption('P2');
  await page.waitForFunction(() => document.querySelector('#status').textContent.includes('No hay ejercicios'));
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('Library UI passed: list, detail, embed URL, combined filters, empty state, desktop/mobile overflow.');
})().catch(error => { console.error(error); process.exit(1); });

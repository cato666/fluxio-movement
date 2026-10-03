const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
test('mobile navigation stays hidden until role is confirmed and revalidates on return without losing form',async()=>{
 const browser=await chromium.launch();
 try {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  let release;const initial=new Promise(resolve=>release=resolve);let calls=0,role='ATHLETE',failed=false;
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('http://localhost:18768/**',async route=>{
   const url=new URL(route.request().url());
   if(url.pathname==='/api/auth/me'){
    calls++;if(calls===1)await initial;
    return route.fulfill({status:failed?503:200,json:failed?{detail:'Sin conexión'}:{name:'Atleta',role}});
   }
   if(url.pathname.startsWith('/static/')){
    const path='app'+url.pathname;
    if(!fs.existsSync(path))return route.fulfill({status:404});
    return route.fulfill({body:fs.readFileSync(path),contentType:path.endsWith('.js')?'application/javascript':path.endsWith('.css')?'text/css':'application/octet-stream'});
   }
   return route.fulfill({contentType:'text/html',body:fs.readFileSync('app/static/index.html')});
  });
  await page.goto('http://localhost:18768/analyses/new',{waitUntil:'domcontentloaded'});
  assert.equal(await page.locator('.functional-nav').isVisible(),false);
  assert.equal(await page.locator('[data-nav-role]:not([hidden])').count(),0);
  release();await page.locator('.functional-nav').waitFor({state:'visible'});
  assert.equal(await page.locator('[data-nav-role]:not([hidden])').count(),3);
  await page.locator('[name=objective]').first().fill('Mi técnica');
  failed=true;
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})));
  await page.waitForFunction(()=>document.querySelector('.functional-nav').hidden);
  await page.waitForTimeout(100);
  assert.equal(await page.locator('[data-nav-role]:not([hidden])').count(),0);
  failed=false;role='COACH';
  await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));
  await page.locator('.functional-nav').waitFor({state:'visible'});
  assert.equal(await page.locator('[data-nav-role=ATHLETE]:not([hidden])').count(),0);
  assert.equal(await page.locator('[data-nav-role=COACH]:not([hidden])').count(),3);
  assert.equal(await page.locator('[name=objective]').first().inputValue(),'Mi técnica');
  assert.deepEqual(errors,[]);
 }finally{await browser.close()}
});

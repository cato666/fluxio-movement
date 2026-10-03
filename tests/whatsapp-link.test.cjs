const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
async function run(fn){
 const browser=await chromium.launch({headless:true});
 try{
 const page=await browser.newPage({viewport:{width:320,height:844}});
 let linked=false,issued=0;
 await page.route('http://localhost:18768/**',route=>{
  const url=route.request().url();
  if(url.endsWith('/identity')){if(route.request().method()==='DELETE')linked=false;return route.fulfill({json:{linked}});}
  if(url.endsWith('/link-challenges')){issued++;return route.fulfill({json:{code:'VINCULAR fixture',expires_at:new Date(Date.now()+600000).toISOString()}});}
  return route.fulfill({contentType:'text/html',body:'<meta name="whatsapp-destination" content="56911112222"><main id="root"></main>'});
 });
 await page.goto('http://localhost:18768');
 await page.addStyleTag({content:fs.readFileSync('app/static/styles.css','utf8')+fs.readFileSync('app/static/training.css','utf8')});
 await page.addScriptTag({content:fs.readFileSync('app/static/vendor/qrcodegen.js','utf8')});
 await page.addScriptTag({content:fs.readFileSync('app/static/whatsapp-link.js','utf8')});
 await page.evaluate(()=>window.cleanup=window.mountWhatsAppLink(document.querySelector('main')));
 await fn(page,()=>issued,()=>{linked=true;});
 }finally{await browser.close();}
}
test('linking requires explicit emission and verified identity, responsive and unlink',()=>run(async(page,issued,link)=>{
 await page.getByText('Registrar por WhatsApp',{exact:true}).click();
 await page.getByRole('button',{name:'Vincular mi WhatsApp'}).waitFor();
 assert.equal(issued(),0);
 await page.getByRole('button',{name:'Vincular mi WhatsApp'}).click();
 const open=page.getByRole('link',{name:'Abrir WhatsApp'});
 await open.waitFor();
 assert.equal(await open.getAttribute('href'),'https://wa.me/56911112222?text=VINCULAR%20fixture');
 assert.equal(issued(),1);
 await page.setViewportSize({width:1280,height:844});
 assert.equal(await page.locator('.training-whatsapp-qr canvas').isVisible(),true);
 await page.locator('.training-whatsapp-qr canvas').screenshot({path:'.impeccable/whatsapp-link-qr.png'});
 await page.getByRole('button',{name:'Ya lo envié'}).click();
 await open.waitFor();
 assert.equal(await page.getByText('WhatsApp vinculado',{exact:true}).count(),0);
 for(const width of [320,390,430,1280]){await page.setViewportSize({width,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);}
 if(process.env.WHATSAPP_UX_SCREENSHOTS){
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'.impeccable/whatsapp-link-mobile.png'});
 await page.setViewportSize({width:1280,height:844});await page.screenshot({path:'.impeccable/whatsapp-link-desktop.png'});
 }
 link();await page.getByRole('button',{name:'Ya lo envié'}).click();
 await page.getByRole('button',{name:'Desvincular WhatsApp'}).waitFor();
 assert.equal(await page.locator('.training-whatsapp-qr').count(),0);
 page.once('dialog',dialog=>dialog.accept());
 await page.getByRole('button',{name:'Desvincular WhatsApp'}).click();
 await page.getByRole('button',{name:'Vincular mi WhatsApp'}).waitFor();
 assert.equal(issued(),1);
 await page.evaluate(()=>cleanup());assert.equal(await page.locator('.training-whatsapp').count(),0);
}));
test('disabled channel is recoverable without emitting challenges',()=>run(async(page,issued)=>{
 await page.route('**/api/whatsapp/identity',r=>r.fulfill({status:404,json:{detail:'Canal no habilitado'}}));
 await page.getByText('Registrar por WhatsApp',{exact:true}).click();
 await page.getByText('WhatsApp no está disponible en este momento. Puedes registrar desde la web.').waitFor();
 assert.equal(issued(),0);assert.equal(await page.getByRole('button',{name:'Reintentar'}).count(),1);
}));

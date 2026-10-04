from pathlib import Path
from playwright.sync_api import sync_playwright
import json,time
root=Path(__file__).resolve().parents[1];out=root/'build/latest';errors=[];results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for name,w,h in [('desktop',1440,1100),('mobile',390,844)]:
  page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
  page.on('pageerror',lambda e: errors.append(str(e)))
  response=page.goto('http://127.0.0.1:4326/',wait_until='networkidle',timeout=90000)
  page.wait_for_timeout(5000)
  page.screenshot(path=str(out/f'web-{name}.png'),full_page=True)
  result={'viewport':name,'http':response.status,'horizontal_overflow':page.evaluate('document.documentElement.scrollWidth > innerWidth'),'revision':page.locator('#revision').inner_text(),'portrait_loaded':page.locator('#portrait').evaluate('(e)=>e.complete && e.naturalWidth>0')}
  page.locator('[data-mode="model"]').click()
  try:
   page.wait_for_function('document.querySelector("model-viewer").loaded',timeout=60000)
   result['glb_loaded']=True
   result['dimensions']=page.locator('model-viewer').evaluate('(e)=>e.getDimensions()')
   page.screenshot(path=str(out/f'web-{name}-3d.png'))
  except Exception as e:result['glb_loaded']=False;result['model_error']=str(e)[:200]
  results.append(result);page.close()
 browser.close()
report={'results':results,'page_errors':errors};(out/'web-test.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

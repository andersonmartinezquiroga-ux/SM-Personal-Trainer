"""SJM Executor: browser automation with explicit allowlist and dry-run default."""
import argparse, json, os, sys
from datetime import datetime, timezone
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def run(url, output, submit=False, allow_host='127.0.0.1'):
    parsed=urlparse(url)
    if parsed.scheme not in ('http','https') or parsed.hostname != allow_host:
        raise ValueError('Host not authorized. Set --allow-host explicitly for a verified destination.')
    result={'url':url,'time_utc':datetime.now(timezone.utc).isoformat(),'submitted':False,'mode':'submit' if submit else 'dry-run'}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True, executable_path=os.getenv('CHROMIUM_PATH') or None, args=['--no-sandbox'])
        page=browser.new_page()
        page.set_default_timeout(10000)
        page.route('**/*', lambda route: route.continue_() if urlparse(route.request.url).hostname == allow_host else route.abort())
        page.goto(url,wait_until='domcontentloaded',timeout=25000)
        result['title']=page.title()
        result['forms']=page.locator('form').count()
        result['inputs']=page.locator('input, textarea, select').count()
        if submit:
            # Submit is restricted to the included localhost test form. No real-world applications.
            if parsed.hostname not in ('localhost','127.0.0.1'):
                raise ValueError('External form submission disabled: requires site-specific reviewed workflow.')
            page.locator('input[name="name"]').fill('SJM Test')
            page.locator('input[name="email"]').fill('test@example.invalid')
            page.locator('button[type="submit"]').click()
            page.get_by_text('RECIBIDO',exact=True).wait_for(timeout=5000)
            result['submitted']=True
            result['confirmation']='RECIBIDO'
        browser.close()
    with open(output,'w',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('url');ap.add_argument('--allow-host',default='127.0.0.1');ap.add_argument('--submit',action='store_true');ap.add_argument('--output',default='result.json');a=ap.parse_args()
    try: print(json.dumps(run(a.url,a.output,a.submit,a.allow_host),ensure_ascii=False))
    except Exception as e: print('ERROR:',e,file=sys.stderr);sys.exit(1)

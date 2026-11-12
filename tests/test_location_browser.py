"""Browser consent and distance UI, using simulated device/store coordinates."""
import signal
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest
from playwright.sync_api import sync_playwright, expect

pytestmark = pytest.mark.browser


@pytest.fixture(scope='module')
def location_site():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
                                '--server.port', str(port), '--server.address', '127.0.0.1',
                                '--server.headless', 'true'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}'
    try:
        for _ in range(150):
            try:
                with urlopen(url + '/_stcore/health', timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.1)
        else:
            pytest.fail('Server did not start')
        yield url
    finally:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.mark.parametrize('viewport',[{'width':1440,'height':1000},{'width':390,'height':844}],ids=['desktop','mobile'])
def test_granted_location_google_points_nearest_sort_and_clear(location_site, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport=viewport, geolocation={'latitude':24.8,'longitude':120.97,'accuracy':5}, permissions=['geolocation'])
        page = context.new_page()
        errors=[]
        page.on('pageerror',lambda error: errors.append(str(error)))
        page.add_init_script('''window.geoRequests=0;const original=navigator.geolocation.getCurrentPosition.bind(navigator.geolocation);navigator.geolocation.getCurrentPosition=(...args)=>{window.geoRequests++;return original(...args);};''')
        try:
            page.goto(location_site)
            page.get_by_text('⌖ 找離我近的餐廳',exact=True).click()
            locate=page.get_by_role('button',name='⌖ 取得我的位置',exact=True)
            expect(locate).to_be_visible(timeout=30000)
            assert page.evaluate('window.geoRequests')==0
            locate.click()
            expect(page.get_by_text('已取得你的位置；裝置回報精度約 ±5 公尺。',exact=True)).to_be_visible(timeout=20000)
            expect(page.get_by_text('目前 0/10 間餐廳可計算距離。',exact=True)).to_be_visible()
            for name, value in [('包子商行','24.81,120.97'),('麥當勞','https://www.google.com/maps/place/test/@1,2,15z/data=!3d24.8001!4d120.97')]:
                page.get_by_role('button',name='設定餐廳位置',exact=True).click()
                dialog=page.get_by_role('dialog')
                expect(dialog).to_be_visible()
                dialog.get_by_role('combobox').first.click()
                page.get_by_role('option',name=name,exact=True).click()
                expect(dialog.get_by_text(f'目前選擇：{name}',exact=True)).to_be_visible()
                text=dialog.get_by_role('textbox',name='Google Maps 座標或完整店家網址',exact=True)
                text.fill(value)
                dialog.get_by_role('button',name='套用座標',exact=True).click()
                expect(dialog).not_to_be_visible(timeout=15000)
            cards=page.locator('.st-key-catalog_grid')
            expect(cards.locator('.food-card h3').first).to_have_text('麥當勞')
            expect(cards).to_contain_text('直線距離約 11 公尺')
            expect(cards).to_contain_text('直線距離約 1.11 公里')
            expect(cards).to_contain_text('店家尚無座標，無法計算距離')
            assert '24.8' not in page.url and '120.97' not in page.url
            page.get_by_role('button',name='清除位置',exact=True).click()
            expect(page.get_by_role('button',name='⌖ 取得我的位置',exact=True)).to_be_visible()
            expect(cards.locator('.food-card h3').first).to_have_text('包子商行')
            expect(cards.get_by_text('直線距離約 11 公尺',exact=True)).to_have_count(0)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert not errors,errors
        finally:
            context.close()
            browser.close()


@pytest.mark.parametrize('code,text',[(1,'未取得定位權限'),(3,'定位逾時')])
def test_denied_and_timeout_do_not_replace_catalog(location_site,code,text):
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=browser.new_page()
        page.add_init_script(f"navigator.geolocation.getCurrentPosition=(ok,fail)=>fail({{code:{code}}});")
        try:
            page.goto(location_site)
            page.get_by_text('⌖ 找離我近的餐廳',exact=True).click()
            locate=page.get_by_role('button',name='⌖ 取得我的位置',exact=True)
            expect(locate).to_be_visible(timeout=30000)
            locate.click()
            expect(page.get_by_text(text,exact=False)).to_be_visible(timeout=15000)
            expect(page.get_by_role('button',name='幫我決定這一餐',exact=True)).to_be_enabled()
            expect(page.locator('.st-key-catalog_grid .food-card')).to_have_count(6)
        finally:
            browser.close()


def test_clear_cancels_an_inflight_location_request(location_site):
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=browser.new_page()
        page.add_init_script('navigator.geolocation.getCurrentPosition=(ok)=>setTimeout(()=>ok({coords:{latitude:24.8,longitude:120.97,accuracy:5}}),800);')
        try:
            page.goto(location_site)
            page.get_by_text('⌖ 找離我近的餐廳',exact=True).click()
            locate=page.get_by_role('button',name='⌖ 取得我的位置',exact=True)
            expect(locate).to_be_visible(timeout=30000)
            locate.click()
            page.get_by_role('button',name='清除位置',exact=True).click()
            page.wait_for_timeout(1000)  # Outlive the deliberately delayed device callback.
            expect(page.get_by_text('已取得你的位置',exact=False)).to_have_count(0)
            expect(locate).to_be_visible()
        finally:
            browser.close()

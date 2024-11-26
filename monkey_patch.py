from typing import Optional, Union, List, Any
from time import sleep, time
import botasaurus_driver
from botasaurus_driver.core.tab import Tab
from botasaurus_driver.driver import block_if_should
# from botasaurus_driver.solve_cloudflare_captcha import wait_till_document_is_ready


def wait_till_document_is_ready(tab, wait_for_complete_page_load, max_wait_time):
    start_time = time()

    if wait_for_complete_page_load:
        script = "return document.readyState === 'complete'"
    else:
        script = "return document.readyState === 'interactive' || document.readyState === 'complete'"

    while True:
        sleep(0.1)
        try:
            response = tab._run(tab.evaluate(script, await_promise=False))
            if response:
                break
        except Exception as e:
            print("An exception occurred", e)

        elapsed_time = time() - start_time
        if elapsed_time > max_wait_time:
            raise TimeoutError("Document did not become ready within 30 seconds")


def get(
    self,
    link: str,
    bypass_cloudflare=False,
    wait: Optional[int] = None,
    max_wait_time: int = 60 * 5,
) -> Tab:
    self._tab = self._run(self._browser.get(link))
    self.sleep(wait)
    wait_till_document_is_ready(
        self._tab, self.config.wait_for_complete_page_load, max_wait_time
    )
    if bypass_cloudflare:
        self.detect_and_bypass_cloudflare()
    block_if_should(self)
    return self._tab


botasaurus_driver.driver.DriverBase.get = get

# def test2(tab, wait_for_complete_page_load):
#     print(test2)
#     import pdb

#     pdb.set_trace()


# botasaurus_driver.solve_cloudflare_captcha.wait_till_document_is_ready = test2

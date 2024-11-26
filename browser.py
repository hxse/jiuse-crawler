from botasaurus.browser import browser, Driver
from botasaurus.user_agent import UserAgent
from botasaurus.window_size import WindowSize
from botasaurus.user_agent import UserAgent
from botasaurus.window_size import WindowSize
from chrome_extension_python import Extension
from botasaurus.lang import Lang
import typer
from callback import get_home_page
from tool import get_meta_data


@browser(
    extensions=[
        Extension(
            # "https://chromewebstore.google.com/detail/adblock-%E2%80%94-best-ad-blocker/gighmmpiobklfepjocnamgkkbiglidom"
            "https://chromewebstore.google.com/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm"
        )
    ],
    output=None,
    reuse_driver=True,
    # run_async=True,
    lang=Lang.Chinese,
    add_arguments=["--mute-audio"],
    close_on_crash=True,
    raise_exception=True,
    tiny_profile=True,
    headless=lambda x: x["headless"],
    profile=lambda x: x["profile"],
    user_agent=lambda x: x["user_agent"],
    window_size=lambda x: x["window_size"],
    proxy=lambda x: x["proxy"],
    wait_for_complete_page_load=False,
    max_retry=3,
)
def browser_driver(driver: Driver, data):
    res = data["callback"](driver, data)
    meta_data = get_meta_data(driver)
    return [res, meta_data]


def run_browser(
    url, callback: any = get_home_page, headless: bool = False, output_dir: str = ""
):
    """
    目前用不着两个profile, 一个就行了
    """
    user_profile = [
        {
            "url": url,
            "callback": callback,
            "profile": "pikachu",
            "headless": headless,
            "user_agent": UserAgent.HASHED,
            "window_size": WindowSize.HASHED,
            "proxy": "http://127.0.0.1:7890",
            "output_dir": output_dir,
            "waitTime": 2,
            "timeout": 120,
        },
        {
            "url": url,
            "callback": callback,
            "profile": "pikachu2",
            "headless": headless,
            "user_agent": UserAgent.HASHED,
            "window_size": WindowSize.HASHED,
            "proxy": "http://127.0.0.1:7890",
            "output_dir": output_dir,
            "waitTime": 2,
            "timeout": 120,
        },
    ][0]
    return browser_driver(user_profile)


if __name__ == "__main__":
    typer.run(run_browser)

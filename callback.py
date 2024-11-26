from tool import get_meta_data, check_state, get_domain
from botasaurus.soupify import soupify
from botasaurus.browser import Wait


def get_home_page(driver, data):
    """
    https://www.ting13.cc/youshengxiaoshuo/29971
    提取章节目录url
    """
    url = data["url"]
    domain = get_domain(url)
    driver.get(url, wait=data["waitTime"])
    # check_state(driver, timeout=data["timeout"])
    driver.wait_for_element(".colVideoList", wait=Wait.LONG)
    soup = soupify(driver)

    videos = soup.select(".colVideoList .video-elem")
    video_arr = []
    for el in videos:
        t = el.select_one(".title")
        title = t.text.strip()
        title_href = t["href"].strip()

        a = el.select_one(".text-dark")
        author = a.text.strip()
        author_href = a["href"].strip()

        m = el.select_one(".text-muted:nth-child(2)")
        m2 = m.text
        date = m2.split("|")[0].strip("\xa0").strip()
        view = m2.split("|")[1].strip("\xa0").strip()

        video_arr.append(
            {
                "title": title,
                "title_href": domain + title_href,
                "author": author,
                "author_href": domain + author_href,
                "videoId": title_href.split("/")[-1],
                "date": date,
                "view": view,
            }
        )

    bar = soup.select(".pagination .page-link")
    page_count = 1 if len(bar) == 0 else int(bar[-2].text)

    return {
        "url": url,
        "title": title,
        "page_count": page_count,
        "video_arr": video_arr,
    }


def get_m3u8_page(driver, data):
    url = data["url"]
    domain = get_domain(url)
    driver.get(url, wait=data["waitTime"])
    # check_state(driver, timeout=data["timeout"])
    driver.wait_for_element("#video-play", wait=Wait.LONG)
    soup = soupify(driver)

    videos = soup.select_one("#video-play")
    m3u8_url = videos["data-src"]

    title = soup.select_one("#videoShowPage .container-title").text.strip()
    author = soup.select_one("#videoShowTabAbout div a").text.strip()
    date = soup.select("#videoShowTabAbout .text-small")[1].text.strip()
    view = soup.select("#videoShowTabAbout div")[-1].text.strip()

    return {
        "title": title,
        "author": author,
        "date": date,
        "view": view,
        "videoId": url.split("/")[-1],
        "m3u8_url": m3u8_url,
    }

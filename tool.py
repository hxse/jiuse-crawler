from time import time, sleep
from pathlib import Path
from pathvalidate import sanitize_filename
import urllib
import shutil
import json

download_dir = Path.home() / "Downloads" / "91porn"


def get_domain(url: str):
    return "/".join(url.split("/")[0:3])


def replace_url(url, domain="91porny.com"):
    url = url.split("?")[0]
    url_arr = url.split("/")
    url_arr[2] = domain
    return "/".join(url_arr)


def mkdir_path(file_path):
    if not file_path.parent.is_dir():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path.parent


def get_meta_data(driver):
    return {
        "cookies": driver.get_cookies_dict(),
        "headers": {"User-Agent": driver.user_agent},
    }


def check_state(driver, timeout=10):
    start = time()
    while 1:
        end = time()
        if end - start > timeout:
            raise TimeoutError(f"TimeoutError {timeout}")
        sleep(0.5)
        # resTitle = driver.run_js("return document.title")
        resState = driver.run_js("return document.readyState")
        # print(end - start, resState)

        if resState == "complete":
            print(f"document complete {end - start}/{timeout}")
            break


def get_cache_dir(
    file_path, output_dir: str = download_dir, cacheDir: str = "cache_files"
):
    return output_dir / Path(cacheDir) / file_path.parent.name / file_path.stem


def get_user_playlist_dir(output_dir: str = download_dir):
    return output_dir / "user_playlist"


def get_user_playlist_sort_dir(output_dir: str = download_dir):
    return output_dir / "user_playlist_sort"


def get_file_path(
    author: str,
    title: str,
    date: str,
    videoId: str,
    dataDir: str = "data_files",
    output_dir: str = download_dir,
):
    title = title.strip(".")  # windows会把末尾的.清空
    fileName = sanitize_filename(
        f"{date} {title} {videoId}.mp4", ""
    )  # 把文件名净化成windows安全的字符
    fileName = fileName.replace("[", "［").replace(
        "]", "］"
    )  # 有些播放器比如oplayer不认半角[], 所以换成全角的
    filePath = Path(dataDir) / author / fileName
    return output_dir / filePath


def get_video_path(
    author: str,
    title: str,
    date: str,
    videoId: str,
    dataDir: str = "data_files",
    output_dir: str = download_dir,
):
    file_path = get_file_path(
        author,
        title,
        date,
        videoId,
        dataDir="videos",
        output_dir=output_dir,
    )
    return output_dir / "videos" / file_path.name


def filter_video(url, pageInfoArr):
    author = urllib.parse.unquote(url.split("/")[4])
    _arr = []
    for i in pageInfoArr:
        if i["author"] == author:
            _arr.append(i)
    return _arr


def is_file(filePath):
    isSkip = False
    if Path(filePath).exists():
        size = Path(filePath).stat().st_size
        if size > 0:
            isSkip = True
    return [filePath, isSkip]


def check_skip_glob(info, file_path):
    for file_path_glob in Path(file_path.parent).glob(f'*{info["videoId"]}.mp4'):
        file_path_glob, is_skip = is_file(file_path_glob)
        if is_skip:
            return [file_path_glob, True]
    return [file_path, False]


def get_config(output_dir):
    try:
        with open(output_dir / "config.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "blacklist": {
                "videoId": [],
                "author": [],
            },
            "user_list": [],
        }


def blacklist_filter(pageInfoArrOrigin, config):
    pageInfoArr = []
    blacklistArr = []
    for info in pageInfoArrOrigin:
        if (
            info["author"] in config["blacklist"]["author"]
            or info["videoId"] in config["blacklist"]["videoId"]
        ):
            blacklistArr.append(info)
        else:
            pageInfoArr.append(info)
    return [pageInfoArr, blacklistArr]


def create_video_playlist(output_dir, file_dir, config):
    playlist_path = output_dir / "videos.m3u8"

    video_arr = [
        f"../{i.parent.parent.name}/{i.parent.name}/{i.name}"
        for i in file_dir.glob("*.mp4")
    ]
    with open(playlist_path, "w", encoding="utf8") as f:
        f.write("\n".join(video_arr))


def create_playlist(output_dir, file_dir, config):
    user_playlist_dir = get_user_playlist_dir(output_dir)
    user_playlist_sort_dir = get_user_playlist_sort_dir(output_dir)
    user_playlist_dir.mkdir(exist_ok=True)
    user_playlist_sort_dir.mkdir(exist_ok=True)

    playlist_path = user_playlist_dir / f"{file_dir.name}.m3u8"
    video_arr = [
        f"../{i.parent.parent.name}/{i.parent.name}/{i.name}"
        for i in file_dir.glob("*.mp4")
    ]
    with open(playlist_path, "w", encoding="utf8") as f:
        f.write("\n".join(video_arr))

    for i in user_playlist_sort_dir.glob("*"):
        if i.is_file():
            i.unlink()

    count = 0
    data = [i for i in user_playlist_dir.glob("*.m3u8")]
    for i in data:
        if i.stem in config["user_list"]:
            idx = str(config["user_list"].index(i.stem) + 1).zfill(len(str(len(data))))
            i2 = user_playlist_sort_dir / f"{idx} {i.name}"
            shutil.copy(str(i), str(i2))
            count += 1
    for i in data:
        if i.stem not in config["user_list"]:
            idx = str(count + 1).zfill(len(str(len(data))))
            i2 = user_playlist_sort_dir / f"{idx} {i.name}"
            shutil.copy(str(i), str(i2))
            count += 1

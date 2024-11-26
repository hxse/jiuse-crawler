import m3u8_multithreading_download
import monkey_patch
from browser import run_browser
import typer
from callback import get_home_page, get_m3u8_page
from tool import (
    download_dir,
    replace_url,
    mkdir_path,
    get_file_path,
    get_cache_dir,
    check_skip_glob,
    create_playlist,
    filter_video,
    get_config,
    blacklist_filter,
    get_video_path,
    create_video_playlist,
)
from rich import print
from m3u8_multithreading_download import m3u8_download
from pathlib import Path


def get_user(
    url,
    headless: bool = True,
    output_dir: str = download_dir,
    page: int = 1,
    config={},
):
    print(f"[bold yellow]get page 1 {url}[/]")
    [res, meta_data] = run_browser(
        url, callback=get_home_page, headless=headless, output_dir=output_dir
    )
    res["data"] = [*res.get("data", []), *filter_video(url, [*res["video_arr"]])]

    del res["video_arr"]
    assert len(res["data"]) != 0, f"number of videos is zero {url}"

    if res["page_count"] > 1:
        for value in range(2, res["page_count"] + 1):
            if value > page:
                print(f"[bold green]skip page {value}[/]")
                continue
            print(f"[bold yellow]get page {value} {url}[/]")
            [res2, meta_data] = run_browser(
                f"{url}?page={value}",
                callback=get_home_page,
                headless=headless,
                output_dir=output_dir,
            )
            res["data"] = [
                *res.get("data", []),
                *filter_video(url, [*res2["video_arr"]]),
            ]
            assert len(res["data"]) != 0, f"number of videos is zero {url}"

    [pageInfoArr, blacklistArr] = blacklist_filter(res["data"], config)
    res["data"] = pageInfoArr

    for index, value in enumerate(res["data"]):
        file_path = get_file_path(
            value["author"],
            value["title"],
            value["date"],
            value["videoId"],
            output_dir=output_dir,
        )
        [g_file_path, flag] = check_skip_glob(value, file_path)
        if flag:
            print(f"[bold green]skip {file_path}[/]")
            if not file_path.is_file():
                g_file_path.rename(file_path)
            continue

        print(
            f"[bold yellow]get m3u8 {index+1}/{len(res['data'])} {value['title_href']}[/]"
        )
        [res3, meta_data] = run_browser(
            value["title_href"],
            callback=get_m3u8_page,
            headless=headless,
            output_dir=output_dir,
        )

        mkdir_path(file_path)
        cache_dir = get_cache_dir(file_path, output_dir=output_dir)
        try:
            m3u8_download(res3["m3u8_url"], cache_dir, file_path, meta_data)
        except AssertionError as e:
            print(f"[bold red]{e}[/]")
            continue

    value = res["data"][0]
    file_path = get_file_path(
        value["author"],
        value["title"],
        value["date"],
        value["videoId"],
        output_dir=output_dir,
    )
    create_playlist(output_dir, file_path.parent, config)


def get_video(
    url,
    headless: bool = True,
    output_dir: str = download_dir,
    page: int = 1,
    config={},
):
    [res, meta_data] = run_browser(
        url,
        callback=get_m3u8_page,
        headless=headless,
        output_dir=output_dir,
    )

    file_path = get_video_path(
        res["author"],
        res["title"],
        res["date"],
        res["videoId"],
        dataDir="videos",
        output_dir=output_dir,
    )
    cache_dir = get_cache_dir(file_path, output_dir)

    [g_file_path, flag] = check_skip_glob(res, file_path)
    if flag:
        print(f"[bold green]skip {g_file_path}[/]")
        if not file_path.is_file():
            g_file_path.rename(file_path)
    else:
        try:
            m3u8_download(res["m3u8_url"], cache_dir, file_path, meta_data)
        except AssertionError as e:
            print(f"[bold red]{e}[/]")

    create_video_playlist(output_dir, file_path.parent, config)


def main(url, headless: bool = True, output_dir: str = download_dir, page: int = 1):
    output_dir = Path(output_dir)
    url = replace_url(url)
    config = get_config(output_dir)

    if "author" in url:
        get_user(url, headless, output_dir, page, config)
    elif "video" in url:
        get_video(url, headless, output_dir, page, config)


if __name__ == "__main__":
    app = typer.Typer(pretty_exceptions_show_locals=False)
    app.command(help="also ma")(main)
    app.command("ma", hidden=True)(main)
    app.command(help="also gu")(get_user)
    app.command("gu", hidden=True)(get_user)
    app.command(help="also gv")(get_video)
    app.command("gv", hidden=True)(get_video)
    app()

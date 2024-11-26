#!/usr/bin/env python3
# coding: utf-8
from ast import Try
import grequests
import requests
import m3u8
from pathlib import Path
import subprocess
import typer
from tool import is_file

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
}
http_proxy = "http://127.0.0.1:7890"
proxies = {
    "http": http_proxy,
    "https": http_proxy,
}

timeout = 30
size = 6
retryMax = 6


def createDir(path):
    dirPath = Path(".") / path
    dirPath.mkdir(parents=True, exist_ok=True)
    return dirPath


def getTsList(m3u8file):
    m3u8obj = m3u8.loads(m3u8file)
    return ["" + i for i in m3u8obj.files]


def getCachePath(cacheDirPath, url):
    return cacheDirPath / url.split("/")[-1]


def get_url(url, retry=1, tag="", meta_data={}, retryMax=2):
    assert retry <= retryMax, f"{tag} 超过最大重试次数:{retryMax} {url}"
    try:
        response = requests.get(
            url,
            headers=meta_data.get("headers", None),
            cookies=meta_data.get("cookies", None),
            proxies=proxies,
            timeout=timeout,
        )
        if response.status_code != 200:
            raise Exception(f"{tag} 服务器返回了 {response.status_code}")
        if len(response.text) == 0:
            raise Exception(
                f"m3u8 ts number is zero, please detect video player network"
            )
        return response
    except Exception as e:
        retry += 1
        print(f"{tag} retry {retry}/{retryMax} {e}")
        if str(e).split(" ")[-1] == "403":
            print(f"****已跳过,服务器返回403,可能是版权问题**** {url}")
            return
        return get_url(url, retry, tag=tag, meta_data=meta_data)


def imap_loop(tsUrlArrFull, cacheDirPath, filePath, retry=1, meta_data={}):
    tsUrlArr = [  # 已下载的话则去重
        tsUrl
        for tsUrl in tsUrlArrFull
        if not is_file(getCachePath(cacheDirPath, tsUrl))[1]
    ]
    print(
        "ts缓存已跳过: ",
        len(tsUrlArrFull) - len(tsUrlArr),
        "剩余: ",
        len(tsUrlArr),
        "总计: ",
        len(tsUrlArrFull),
    )

    reqs = (
        grequests.get(
            tsUrl,
            headers=meta_data.get("headers", None),
            cookies=meta_data.get("cookies", None),
            timeout=timeout,
        )
        for tsUrl in tsUrlArr
    )
    count = len(tsUrlArr)
    num = 0
    success = 0
    for res in grequests.imap(reqs, size=size):
        num += 1
        if res.status_code == 200:
            success += 1
            with open(getCachePath(cacheDirPath, res.url), "wb") as f:
                f.write(res.content)
                if len(res.content) == 0:
                    print(
                        "警告,下载到空文件,可能是服务器问题,稍后再试", filePath, res.url
                    )
                    import pdb

                    pdb.set_trace()
            print(
                f"{num}/{count}",
                "请求成功:",
                res.status_code,
                getCachePath(cacheDirPath, res.url).name,
            )
        else:
            print(
                f"{num}/{count}",
                "请求失败:",
                res.status_code,
                getCachePath(cacheDirPath, res.url).name,
            )

    if success != count:
        assert retry <= retryMax, f"""m3u8_download 超过最大重试次数:{retryMax}
            剩余: {len(tsUrlArr)} 总数: {len(tsUrlArrFull)}
            {cacheDirPath}
            """
        retry += 1
        print(f"m3u8_download 重试次数:{retry} 最大次数:{retryMax}")
        return imap_loop(
            tsUrlArrFull, cacheDirPath, filePath, retry, meta_data=meta_data
        )


def m3u8_download(url, cacheDirPath, filePath, meta_data):
    response = get_url(url, tag="get_m3u8_file", meta_data=meta_data)
    if response:
        urlParent = url.split("?")[0].rsplit("/", 1)[0]
        tsNameArr = getTsList(response.text)
        createDir(cacheDirPath)
        tsFileArr = [(cacheDirPath / i) for i in tsNameArr]
        tsUrlArrFull = [urlParent + "/" + i for i in tsNameArr]

        imap_loop(tsUrlArrFull, cacheDirPath, filePath, meta_data=meta_data)

        ts_merge(tsFileArr, cacheDirPath, filePath)
        delete(tsFileArr, cacheDirPath)


def trans_concat(name):
    return name.replace("\\", "\\\\").replace("'", "\\'").replace(" ", "\\ ")


def ts_merge(tsFileArr, cacheDirPath, output):
    concatFile = cacheDirPath / "concat.txt"
    createDir(output.parent)

    with open(concatFile, "w", encoding="utf-8") as f:
        # f.writelines([f"file .\\{trans_concat(str(i))}\n" for i in tsFileArr])
        f.writelines([f"file {str(i.name)}\n" for i in tsFileArr])
    command = f'ffmpeg -y -nostdin -f concat -safe 0 -i "{concatFile.as_posix()}"  -c copy "{output.as_posix()}"'  # 这里不用as_posix()ffmpeg中文会显示乱码,可能是\\转义符的原因
    subprocess.call(
        "chcp 65001", shell=True
    )  # 这里不用65001ffmpeg中文会显示乱码,不过不影响结果,可以正常运行
    subprocess.call(command, shell=True)
    concatFile.unlink()  # 清除concat文件


def delete(tsFileArr, cacheDirPath=False):
    for i in tsFileArr:
        i.unlink()
    if cacheDirPath:
        cacheDirPath.rmdir()
        for i in [i for i in cacheDirPath.parents][:-1]:
            try:
                i.rmdir()
            except OSError as e:
                print("无法删除:", i, e)
            if i.name == "cache_files":
                break


if __name__ == "__main__":
    app = typer.Typer(pretty_exceptions_show_locals=False)
    app.command()(m3u8_download)
    app()

import os
from functools import cache
from urllib import parse

from decouple import config
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


class CustomException(Exception):
    def __init__(self, code, details) -> None:
        self.code = code
        self.details = details


app = FastAPI()
app.mount("/public", StaticFiles(directory="../public"), "public")

templates = Jinja2Templates("../public")
links = [config("LINK1"), config("LINK2"), config("LINK3"), config("LINK4")]


@cache
def get_dirs(url_component_path, url_path, path):
    files = os.listdir(f"../files/{path}")

    dirs = []
    fs = []
    for f in files:
        if os.path.isdir(f"../files{path}/{f}"):
            dirs.append(f)
        else:
            fs.append(f)

    files = [*sorted(dirs), *sorted(fs)]

    files_paths = []
    for f in files:
        if os.path.isdir(f"../files{path}/{f}"):
            files_paths.append([f, f"/files{path}/{f}", "dir"])
        else:
            if (
                f.endswith(".docx")
                or f.endswith(".xlsx")
                or f.endswith(".pptx")
                or f.endswith(".pdf")
            ):
                file_path = f"{'/viewer' + url_component_path[6:]}/{f}"
            else:
                file_path = f"{'/download' + url_component_path[6:]}/{f}"
            files_paths.append([f, file_path, "file"])

    dirs = url_path.split("/")
    dir_paths = []
    for i, dir_path in enumerate(dirs):
        full_url_path = "/".join(dirs[j] for j in range(1, i + 1))
        dir_paths.append([dir_path, full_url_path])

    return files_paths, dir_paths


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return templates.TemplateResponse(
        "error.html", {"request": request, "exc": exc}, exc.code
    )


@app.get("/")
def root():
    return RedirectResponse("/files")


@app.get("/favicon.ico")
def favicon():
    return FileResponse("../public/favicon.ico")


@app.get("/robots.txt")
def robots():
    return FileResponse("../public/robots.txt")


@app.get("/files{path:path}")
def files(request: Request, path: str):
    if not os.path.isdir(f"../files/{path}"):
        raise CustomException(404, "Directory Not Found")

    files_paths, dir_paths = get_dirs(
        request.url.components.path, request.url.path, path
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "files": files_paths,
            "dir_paths": dir_paths[1:],
            "links": links,
        },
    )


@app.get("/download{path:path}")
def download(path: str):
    if not os.path.isfile(f"../files{path}"):
        raise CustomException(404, "File Not Found")

    return FileResponse(f"../files{path}")


@app.get("/viewer{path:path}")
def viewer(request: Request, path: str):
    if not os.path.isfile(f"../files{path}"):
        raise CustomException(404, "File Not Found")

    download_url = "https://ac.jeyy.xyz/download" + request.url.components.path[7:]
    if path.endswith(".pdf"):
        embed_url = download_url
    else:
        embed_url = f"https://view.officeapps.live.com/op/embed.aspx?src={parse.quote(download_url, safe='')}&amp;wdEmbedCode=0"

    file_name = request.url.components.path.split("/")[-1]
    prev_dir = ("https://ac.jeyy.xyz/files" + request.url.components.path[7:]).replace(
        file_name, ""
    )

    return templates.TemplateResponse(
        "viewer.html",
        {
            "request": request,
            "embed_url": embed_url,
            "file_name": file_name,
            "download_url": download_url,
            "prev_dir": prev_dir[:-1],
        },
    )


@app.get("/redirect")
def redirect():
    return RedirectResponse("https://jeyy.xyz")

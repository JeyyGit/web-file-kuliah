from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import os

app = FastAPI()
app.mount('/public', StaticFiles(directory='../public'), 'public')

templates = Jinja2Templates('../public')

@app.get('/')
def root():
    return RedirectResponse('/files')

@app.get("/files{path:path}")
def files(request: Request, path: str):
    files = os.listdir(f"../files/{path}")

    dirs = []
    fs = []
    for f in files:
        if os.path.isdir(f'../files{path}/{f}'):
            dirs.append(f)
        else:
            fs.append(f)

    files = [*sorted(dirs), *sorted(fs)]

    files_paths = []
    for f in files:
        if os.path.isdir(f'../files{path}/{f}'):
            files_paths.append([f, f"{request.url._url}/{f}", 'dir'])
        else:
            file_path = f"{'/download' + request.url.components.path[6:]}/{f}"
            files_paths.append([f, file_path, 'file'])

    dirs = request.url.path.split('/')
    dir_paths = []
    for i, dir_path in enumerate(dirs):
        full_url_path = '/'.join(dirs[j] for j in range(1, i+1))
        dir_paths.append([dir_path, full_url_path])

    return templates.TemplateResponse("index.html", {"request": request, "files": files_paths, 'dir_paths': dir_paths[1:]})

@app.get('/download{path:path}')
def download(path: str):
    return FileResponse(f'../files{path}')

@app.get('/redirect')
def redirect():
    return RedirectResponse('https://jeyy.xyz')
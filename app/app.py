import os
from functools import cache
from io import BytesIO

import mammoth
import xlsx2html
from decouple import config
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


class CustomException(Exception):
    def __init__(self, code, details) -> None:
        self.code = code
        self.details = details


app = FastAPI()
app.mount('/public', StaticFiles(directory='../public'), 'public')

templates = Jinja2Templates('../public')
links = [config('LINK1'), config('LINK2'), config('LINK3'), config('LINK4')]


@cache
def get_dirs(url_component_path, url_path, path):
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
            files_paths.append([f, f"/files{path}/{f}", 'dir'])
        else:
            if f.endswith('.docx') or f.endswith('.xlsx'):
                file_path = f"{'/display' + url_component_path[6:]}/{f}"
            else:
                file_path = f"{'/download' + url_component_path[6:]}/{f}"
            files_paths.append([f, file_path, 'file'])

    dirs = url_path.split('/')
    dir_paths = []
    for i, dir_path in enumerate(dirs):
        full_url_path = '/'.join(dirs[j] for j in range(1, i+1))
        dir_paths.append([dir_path, full_url_path])

    return files_paths, dir_paths

@cache
def get_display(path, document_type):
    res = f"""
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{path.split('/')[-1]}</title>
            </head>
            <body>

            <style>
                #nav {{
                    font-family: Arial, Helvetica, sans-serif;
                    background-color: #b6d3da;
                    word-wrap: break-word;
                    padding-top: 5px;
                    border-radius: 5px;
                }}

                #nav-title {{
                    padding: 5px; 
                    margin: 5px;
                    display: inline;
                }}

                #nav-text {{
                    display: block;
                    margin: 5px;
                }}

                #nav-btn {{
                    margin: 5px;
                }}

                @media screen and (min-width: 800px) {{
                    #nav-text {{
                        display: inline;
                        margin: 5px;
                    }}
                }}
            </style>

            <div id="nav">
                <h3 id="nav-title">Jeyy {document_type} Viewer | </h3> 
                <p id="nav-text">/files{path} | </p>
                <a target="_blank" id="nav-btn" href="/download{path}"><button>Download</button></a>
                <hr>
            </div>
            """

    if document_type == 'Word':
        with open(f'../files{path}', 'rb') as word:
            doc = mammoth.convert_to_html(word)
            
            res += doc.value
            buf = BytesIO(res.encode('utf-8'))
        
    elif document_type == 'Excel':
        with open(f'../files{path}', 'rb') as excel:
            buf = xlsx2html.xls2html(excel)
            buf.seek(0)

            res += buf.read()
            buf = BytesIO(res.encode('utf-8'))

    return buf

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return templates.TemplateResponse('error.html', {'request': request, 'exc': exc}, exc.code)


@app.get('/')
def root():
    return RedirectResponse('/files')

@app.get('/favicon.ico')
def favicon():
    return FileResponse('../public/favicon.ico')

@app.get('/robots.txt')
def robots():
    return FileResponse('../public/robots.txt')

@app.get("/files{path:path}")
def files(request: Request, path: str):
    if not os.path.isdir(f"../files/{path}"):
        raise CustomException(404, "Directory Not Found")

    files_paths, dir_paths = get_dirs(request.url.components.path, request.url.path, path)

    return templates.TemplateResponse("index.html", {"request": request, "files": files_paths, 'dir_paths': dir_paths[1:], 'links': links})

@app.get('/download{path:path}')
def download(path: str):
    if not os.path.isfile(f'../files{path}'):
        raise CustomException(404, "File Not Found")

    return FileResponse(f'../files{path}')


@app.get('/display{path:path}')
def display(path: str):
    if not os.path.isfile(f'../files{path}'):
        raise CustomException(404, "File Not Found")

    if path.endswith('.docx'):
        document_type = 'Word'
    elif path.endswith('.xlsx'):
        document_type = 'Excel'

    try:
        buf = get_display(path, document_type)
        buf.seek(0)
    except:
        return FileResponse(f'../files{path}')

    return StreamingResponse(buf, media_type='text/html')

@app.get('/redirect')
def redirect():
    return RedirectResponse('https://jeyy.xyz')
import base64
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

Path("static/").mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory="templates")

socket: WebSocket | None = None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    global socket
    socket = websocket

    try:
        while True:
            print(await websocket.receive_text())
    except Exception as e:
        print(e)
        socket = None
        await websocket.close()


@app.post("/print/")
async def create_upload_files(file: UploadFile):
    if file.content_type != "application/pdf":
        return RedirectResponse(url="/?status=PDF PLEASE!!", status_code=302)

    if socket is None:
        return RedirectResponse(url="/?status=Printer Disconnected 😭", status_code=302)

    await socket.send_text(base64.b64encode(await file.read()).decode("utf-8"))

    return RedirectResponse(url=f"/?status=Printing...🤞", status_code=302)


@app.get("/")
async def files(request: Request, status: str = ""):
    context = {
        "request": request,
        "status": status
    }

    return templates.TemplateResponse("index.html", context=context)

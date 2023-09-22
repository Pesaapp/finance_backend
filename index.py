from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount the 'static' folder for serving static files (e.g., CSS, JavaScript)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2Templates for rendering HTML templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Use the 'index.html' template
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

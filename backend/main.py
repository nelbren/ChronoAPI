import os
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Inicializar la aplicación FastAPI con metadatos descriptivos para Swagger UI
app = FastAPI(
    title="ChronoAPI",
    description=(
        "API interactiva para consultar la fecha y hora del sistema en "
        "tiempo real. También puedes acceder a la "
        "[Documentación en ReDoc](/redoc)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Habilitar CORS para permitir solicitudes desde cualquier origen
# si fuera necesario
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar el directorio de plantillas HTML de manera dinámica
current_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))


# Redireccionar /historial a /historial/ para evitar problemas con rutas
# relativas de activos (CSS/JS) en MkDocs
@app.get("/historial", include_in_schema=False)
async def redirect_historial():
    return RedirectResponse(url="/historial/")


# Configurar el directorio de documentación de MkDocs y montarlo estáticamente
site_path = os.path.abspath(os.path.join(current_dir, "..", "site"))
os.makedirs(site_path, exist_ok=True)
app.mount(
    "/historial",
    StaticFiles(directory=site_path, html=True),
    name="historial"
)


# Ruta principal: Servir el dashboard web interactivo con diseño glassmorphism
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# Endpoint 1: Retornar la fecha formateada como YYYY-MM-DD
@app.get(
    "/api/date",
    summary="Obtener fecha actual",
    description=(
        "Retorna la fecha actual del sistema formateada exactamente "
        "como YYYY-MM-DD."
    ),
    tags=["Servicios de Tiempo"]
)
def get_date():
    current_time = datetime.now()
    return {"date": current_time.strftime("%Y-%m-%d")}


# Endpoint 2: Retornar la hora formateada como HH:MM:SS
@app.get(
    "/api/time",
    summary="Obtener hora actual",
    description=(
        "Retorna la hora actual del sistema formateada exactamente "
        "como HH:MM:SS."
    ),
    tags=["Servicios de Tiempo"]
)
def get_time():
    current_time = datetime.now()
    return {"time": current_time.strftime("%H:%M:%S")}


# Endpoint 3: Retornar la fecha y hora formateadas como YYYY-MM-DD HH:MM:SS
@app.get(
    "/api/timestamp",
    summary="Obtener marca de tiempo completa",
    description=(
        "Retorna el timestamp del sistema conteniendo fecha y hora "
        "exactamente como YYYY-MM-DD HH:MM:SS."
    ),
    tags=["Servicios de Tiempo"]
)
def get_timestamp():
    current_time = datetime.now()
    return {"timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")}

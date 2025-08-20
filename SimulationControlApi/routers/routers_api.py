# app/routers/api.py
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from uuid import uuid4
import json, shutil, os
from Services.core.config import JOBS_ROOT
from Services.simulation_service import SimulationService   # start_job, cancel_job, get_status, etc.

router = APIRouter()
service = SimulationService()

# --- Endpoints ---
@router.post("/jobs", status_code=202)
async def create_job(
    background_tasks: BackgroundTasks,
    world_zip: UploadFile = File(...),
    hparams: str = Form(...),
):
    """
    Recibe world.zip (multipart) y hparams (JSON string). Responde job_id y arranca job en background.
    """
    job_path,job = service.set_job_directory()
    world_path =os.path.join(job_path, "world")
    world_zip_path=os.path.join(world_path,f"world_{job}.zip")
    config_path=os.path.join(job_path, "config","train_config.json")

    try:
        with open(world_zip_path,"wb",encoding='utf-8') as f:
            shutil.copyfileobj(world_zip.file, f)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo world.zip: {str(e)}")
    
    try:
        config = json.loads(hparams)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Los hiperparametros deben ser un JSON válido")
    
    try:
        with open(config_path,"w",encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo de configuración: {str(e)}")
    
    service.start_job(job, world_zip_path)

    return {"job_id": job, "status": "Entrenamiento iniciado", "message": "La simulacion se está ejecutando en segundo plano."}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    
    return ""


@router.get("/jobs/{job_id}/logs")
async def get_job_logs(job_id: str, tail: int = 200):
    """
    Devuelve las últimas 'tail' líneas de train.log (útil para polling rápido).
    Para streaming en tiempo real usá WebSocket/SSE por separado (stream_service).
    """
    job_dir = JOBS_ROOT / job_id
    log_file = job_dir / "logs" / "train.log"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log no encontrado")
    # Leer últimas 'tail' líneas de forma eficiente
    try:
        with log_file.open("rb") as f:
            # Simple tail: leer todo (ok para logs razonables)
            data = f.read().decode(errors="ignore").splitlines()
            return {"lines": data[-tail:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/artifacts/model")
async def download_model(job_id: str):
    model_file = JOBS_ROOT / job_id / "artifacts" / "model.zip"
    if not model_file.exists():
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return FileResponse(path=str(model_file), filename="model.zip", media_type="application/zip")


@router.delete("/jobs/{job_id}", status_code=204)
async def cancel_job(job_id: str):
    """
    Cancela y limpia un job: detiene contenedor y marca job como cancelado.
    """
    try:
        training_service.cancel_job(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelando job: {e}")
    return JSONResponse(status_code=204, content=None)

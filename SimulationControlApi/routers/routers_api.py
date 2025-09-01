# app/routers/api.py
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from uuid import uuid4
import json, shutil, os
#from Services.core.config import JOBS_ROOT
from Services.simulation_service import SimulationService   # start_job, cancel_job, get_status, etc.

router = APIRouter()
service = SimulationService()

# --- Endpoints ---
@router.post("/jobs", status_code=202)
async def create_job(
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
        with open(world_zip_path,"wb") as f:
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
    try:
        return {"job_id": job, "status": "Entrenamiento iniciado", "message": "La simulacion se está ejecutando en segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falló el inicio del job: {e}")
    

@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str):
    """
    Cancela y limpia un job: detiene contenedor y marca job como cancelado.
    """
    try:
        service.cancel_job(job_id)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelando job: {e}")
    

@router.get("/state/{job_id}", status_code=202)
async def get_job_state(job_id: str):
    try:
        status = service.get_complete_state(job_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado del job: {e}")


@router.get("/jobs/{job_id}/metrics", status_code=200)
async def get_metrics(job_id: str):
    """
    Devuelve las últimas 'tail' líneas de train.log (útil para polling rápido).
    Para streaming en tiempo real usá WebSocket/SSE por separado (stream_service).
    """
    try:
        return service.get_logs(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/download/tensorboard", status_code=200)
async def download_tensorboard(job_id: str):
    try:
        tb_path = service.get_tensorboard_path(job_id)
        response=FileResponse(tb_path, filename=f"tensorboard_file", media_type='application/octet-stream')
        return response
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando los logs de TensorBoard: {e}")


@router.get("/jobs/{job_id}/download/model", status_code=200)
async def download_model(job_id: str):
    """
    Descarga el archivo model.zip con el modelo entrenado.
    """
    try:
        model_path, message = service.get_model_path(job_id)
        response=FileResponse(model_path, filename=f"model_{job_id}.zip", media_type='application/zip')
        response.headers["X-Download-Message"] = message
        return response
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando el modelo: {e}")


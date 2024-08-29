from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["tasks"])


@router.get("/tasks/${task_id}")
async def status_task(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result,
    }
    return JSONResponse(result)

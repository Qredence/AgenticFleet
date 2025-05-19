"""
Routes for task management.
"""


from fastapi import APIRouter, Depends, HTTPException

from agentic_fleet.api.dependencies.services import get_task_service
from agentic_fleet.schemas.task import Task, TaskCreate, TaskUpdate
from agentic_fleet.services.task_service import TaskService

# Create router
router = APIRouter()


@router.get("/", response_model=dict[str, list[Task]])
async def list_tasks(
    task_service: TaskService = Depends(get_task_service),
) -> dict[str, list[Task]]:
    """
    List all tasks.
    """
    try:
        tasks = await task_service.list_tasks()
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Task)
async def create_task(
    task: TaskCreate, task_service: TaskService = Depends(get_task_service)
) -> Task:
    """
    Create a new task.
    """
    try:
        return await task_service.create_task(task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, task_service: TaskService = Depends(get_task_service)) -> Task:
    """
    Get details for a specific task.
    """
    try:
        task = await task_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str, task: TaskUpdate, task_service: TaskService = Depends(get_task_service)
) -> Task:
    """
    Update an existing task.
    """
    try:
        updated_task = await task_service.update_task(task_id, task)
        if not updated_task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return updated_task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}", response_model=dict[str, bool])
async def delete_task(
    task_id: str, task_service: TaskService = Depends(get_task_service)
) -> dict[str, bool]:
    """
    Delete a task.
    """
    try:
        success = await task_service.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/assign/{agent_id}", response_model=Task)
async def assign_task(
    task_id: str, agent_id: str, task_service: TaskService = Depends(get_task_service)
) -> Task:
    """
    Assign a task to an agent.
    """
    try:
        task = await task_service.assign_task(task_id, agent_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

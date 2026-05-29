from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
import requests
import os

from app.celery_tasks import parse_github_issues_task
from app.celery_app import celery_app
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/parser", tags=["Parser"])


class ParseRequest(BaseModel):
    url: str


class ParseResponse(BaseModel):
    task_id: str
    status: str
    message: str


class DirectParseResponse(BaseModel):
    success: bool
    message: str
    result: Optional[dict] = None
    error: Optional[str] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    ready: bool
    result: Optional[dict] = None
    error: Optional[str] = None


def call_parser_service_directly(url: str, user_id: int) -> dict:
    parser_service_url = os.getenv(
        "PARSER_SERVICE_URL", 
        "http://parser:8001"
    )
    
    try:
        response = requests.post(
            f"{parser_service_url}/parse",
            json={"url": url, "user_id": user_id},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Parser service returned error: {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to parser service: {str(e)}"
        )


def get_task_user_id(task_result) -> Optional[int]:
    if hasattr(task_result, 'info') and task_result.info:
        if isinstance(task_result.info, dict):
            if 'user_id' in task_result.info:
                return task_result.info['user_id']

    if task_result.ready() and task_result.successful():
        result = task_result.result
        if isinstance(result, dict) and 'user_id' in result:
            return result['user_id']

    if hasattr(task_result, 'kwargs') and task_result.kwargs:
        if isinstance(task_result.kwargs, dict) and 'user_id' in task_result.kwargs:
            return task_result.kwargs['user_id']
    
    return None


@router.post("/parse", response_model=DirectParseResponse)
def parse_github_issues_direct(
    request: ParseRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        result = call_parser_service_directly(request.url, current_user.id)
        
        return DirectParseResponse(
            success=True,
            message="Parsing completed successfully",
            result=result
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parsing failed: {str(e)}"
        )


@router.post("/parse/queue", response_model=ParseResponse)
def parse_github_issues_queue(
    request: ParseRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        task = parse_github_issues_task.delay(request.url, current_user.id)
        
        return ParseResponse(
            task_id=task.id,
            status="PENDING",
            message="Parsing task has been queued",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start parsing task: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=TaskStatusResponse, name="get_parsing_status")
def get_parsing_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING' and not task_result.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        task_user_id = get_task_user_id(task_result)
        
        if task_user_id is None or task_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this task"
            )
        
        result = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready()
        }
        
        if task_result.ready():
            if task_result.successful():
                result["result"] = task_result.result
            else:
                result["error"] = str(task_result.result)
                
        return TaskStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check task status: {str(e)}"
        )


@router.get("/health")
def parser_health_check():
    try:
        result = celery_app.control.ping(timeout=1)
        
        if result:
            return {
                "status": "healthy",
                "celery": "connected",
                "message": "Parser service is operational"
            }
        else:
            return {
                "status": "unhealthy",
                "celery": "disconnected",
                "message": "Cannot connect to Celery workers"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Parser service health check failed: {str(e)}"
        )
import os
import requests
from app.celery_app import celery_app


@celery_app.task(bind=True, name="parse_github_issues")
def parse_github_issues_task(self, url: str, user_id: int):
    task_id = self.request.id
    
    self.update_state(
        state='PROGRESS',
        meta={'user_id': user_id, 'url': url, 'message': 'Starting parsing...'}
    )
    
    parser_service_url = os.getenv(
        "PARSER_SERVICE_URL", 
        "http://parser:8001"
    )
    
    response = requests.post(
        f"{parser_service_url}/parse",
        json={"url": url, "user_id": user_id},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        return {
            "success": True,
            "task_id": task_id,
            "user_id": user_id,
            "result": result,
            "message": "Parsing completed successfully"
        }
    else:
        raise response.raise_for_status()
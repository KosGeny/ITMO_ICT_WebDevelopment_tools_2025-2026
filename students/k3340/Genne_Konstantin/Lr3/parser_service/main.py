from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from dotenv import load_dotenv

from parser import parse_github_issues

app = FastAPI()

load_dotenv()

class ParseRequest(BaseModel):
    url: str
    user_id: int


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "parser"}


@app.post("/parse")
def parse(request: ParseRequest):
    try:
        if not request.url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        if request.user_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid user_id")
        
        result = parse_github_issues(request.url, request.user_id)
        
        return {
            "message": "Parsing completed successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")
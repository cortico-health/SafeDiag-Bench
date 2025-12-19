import json
import os
import glob
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# Disable caching middleware for development
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

LEADERBOARD_DIR = '/app/leaderboard'

def get_leaderboard_data() -> List[Dict[str, Any]]:
    results = []
    if os.path.exists(LEADERBOARD_DIR):
        # Only load evaluation files (ending in -eval.json)
        for json_file in glob.glob(os.path.join(LEADERBOARD_DIR, '*-eval.json')):
            try:
                with open(json_file, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")

        # Sort results by safety pass rate (descending - higher is better), then by missed escalations
        results.sort(key=lambda x: (
            -(x.get('safety_pass_rate') or -1),  # Higher pass rate is better
            x.get('safety', {}).get('missed_escalations', 0),
            -(x.get('effectiveness', {}).get('top3_recall') or 0)
        ))
    return results

@app.get("/leaderboard-data.json")
async def leaderboard_data():
    return JSONResponse(content=get_leaderboard_data())

@app.get("/")
async def read_index():
    return FileResponse('static/leaderboard.html')

@app.get("/methodology.html")
async def read_methodology():
    return FileResponse('static/methodology.html')

@app.get("/README.md")
async def read_readme():
    return FileResponse('README.md', media_type='text/markdown')

app.mount("/", StaticFiles(directory="static"), name="static")

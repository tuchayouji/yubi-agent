"""驭笔 HarnessPen — Web UI 服务器 (FastAPI)。"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent
import basic_agent

app = FastAPI(title="驭笔 HarnessPen", description="基于 Harness Engineering 的智能写作助手")

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


class GenerateRequest(BaseModel):
    topic: str
    requirements: str = "1000字, 博客风格"


class RewriteRequest(BaseModel):
    original: str
    instruction: str


class CompareRequest(BaseModel):
    topic: str
    requirements: str = "500字"


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回主页面。"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    """生成文章（驭笔版，全链路管控）。"""
    try:
        result = agent.harness_write(req.topic, req.requirements)
        return JSONResponse(content={"success": True, "result": result})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@app.post("/api/rewrite")
async def rewrite(req: RewriteRequest):
    """改写文章（驭笔版，全链路管控）。"""
    try:
        result = agent.harness_rewrite(req.original, req.instruction)
        return JSONResponse(content={"success": True, "result": result})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@app.post("/api/compare")
async def compare(req: CompareRequest):
    """对比基础版 vs 驭笔版。"""
    try:
        basic_result = basic_agent.basic_write(req.topic, req.requirements)
        harness_result = agent.harness_write(req.topic, req.requirements)
        return JSONResponse(content={
            "success": True,
            "basic": basic_result,
            "harness": harness_result,
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

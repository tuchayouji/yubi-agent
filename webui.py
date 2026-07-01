"""驭笔 HarnessPen — Web UI 服务器 (FastAPI)。"""

import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent
import basic_agent
import context
import constraint
import pipeline
import quality

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


def _progress_yield(event_type: str, data: dict):
    """SSE 格式事件。"""
    yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/api/generate/stream")
async def generate_stream(topic: str, requirements: str = "1000字, 博客风格"):
    """生成文章（SSE 流式推送进度）。"""

    def generate():
        try:
            # ⑤ 结构化上下文
            yield from _progress_yield("progress", {"step": "context", "status": "running", "message": "⑤ 结构化上下文注入..."})
            messages = context.build_context(
                system_rules=agent.SYSTEM_RULES,
                current_request={"topic": topic, "requirements": requirements}
            )
            yield from _progress_yield("progress", {"step": "context", "status": "done", "message": "⑤ 结构化上下文注入 ✅"})

            # ① 行为约束
            yield from _progress_yield("progress", {"step": "constraint", "status": "running", "message": "① 行为约束应用..."})
            constrained = constraint.apply_constraint(messages, mode="generate")
            yield from _progress_yield("progress", {"step": "constraint", "status": "done", "message": "① 行为约束应用 ✅"})

            # ② 流程编排
            yield from _progress_yield("progress", {"step": "pipeline", "status": "running", "message": "② 流程编排（LLM 调用中）..."})
            output = pipeline.run_pipeline(constrained)
            yield from _progress_yield("progress", {"step": "pipeline", "status": "done", "message": "② 流程编排 ✅"})

            # ③ 质量校验
            yield from _progress_yield("progress", {"step": "quality", "status": "running", "message": "③ 质量校验中..."})
            result = quality.check_and_rewrite(
                article=output.article,
                outline=output.outline
            )
            yield from _progress_yield("progress", {"step": "quality", "status": "done", "message": "③ 质量校验 ✅"})

            # ④ 异常容错全程覆盖
            yield from _progress_yield("progress", {"step": "resilience", "status": "done", "message": "④ 异常容错全程守护 🤖"})

            yield from _progress_yield("result", {"result": result})

        except Exception as e:
            yield from _progress_yield("error", {"error": str(e)})

    return StreamingResponse(generate(), media_type="text/event-stream")


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

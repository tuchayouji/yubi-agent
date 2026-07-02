"""驭笔 HarnessPen — Web UI 服务器 (FastAPI)。"""

import json
import os
import time
import uuid
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent
import basic_agent
import context
import constraint
import pipeline
import quality
from utils import export

app = FastAPI(title="驭笔 HarnessPen", description="基于 Harness Engineering 的智能写作助手")

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── 文章存储 ───
GENERATED_DIR = "generated"
INDEX_FILE = os.path.join(GENERATED_DIR, "index.json")

os.makedirs(GENERATED_DIR, exist_ok=True)


def _load_index() -> list:
    if not os.path.exists(INDEX_FILE):
        return []
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index: list):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def save_article(topic: str, content: str, source: str = "generate", quality: dict = None) -> str:
    """保存文章到 generated/ 目录，返回 article_id。"""
    article_id = time.strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]
    filename = f"{article_id}.md"
    filepath = os.path.join(GENERATED_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    index = _load_index()
    entry = {
        "id": article_id,
        "topic": topic,
        "source": source,
        "filename": filename,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "char_count": len(content),
    }
    if quality:
        entry["quality"] = quality
    index.insert(0, entry)
    _save_index(index)

    return article_id


def get_article(article_id: str) -> str | None:
    """根据 ID 获取文章内容。"""
    filepath = os.path.join(GENERATED_DIR, f"{article_id}.md")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def list_articles(limit: int = 50) -> list:
    """返回文章列表（最新在前）。"""
    return _load_index()[:limit]


# ─── API ───


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
            # 再次校验以获取最终评分（含重写后的分数）
            quality_summary = quality.check_quality(result, output.outline)
            yield from _progress_yield("progress", {"step": "quality", "status": "done", "message": "③ 质量校验 ✅"})

            # ④ 异常容错全程覆盖
            yield from _progress_yield("progress", {"step": "resilience", "status": "done", "message": "④ 异常容错全程守护 🤖"})

            # 保存文章
            article_id = save_article(topic, result, source="generate", quality=quality_summary)

            yield from _progress_yield("result", {"result": result, "article_id": article_id, "quality": quality_summary})

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


@app.get("/api/articles")
async def get_articles(limit: int = 50):
    """获取文章列表（最新在前）。"""
    articles = list_articles(limit)
    return {"success": True, "articles": articles}


@app.get("/api/articles/{article_id}")
async def get_article_by_id(article_id: str):
    """获取单篇文章内容。"""
    content = get_article(article_id)
    if content is None:
        return JSONResponse(status_code=404, content={"success": False, "error": "文章不存在"})
    # 从索引中查找 quality 数据
    index = _load_index()
    quality = None
    for entry in index:
        if entry["id"] == article_id:
            quality = entry.get("quality")
            break

    # 对旧文章没有 quality 数据的，当场算一个
    if quality is None and content:
        from quality.validators import check_quality
        qr = check_quality(content)
        passed = sum(1 for c in qr.checks if c.passed)
        total = len(qr.checks)
        quality = {
            "passed": qr.passed,
            "score": passed / max(total, 1) * 100,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in qr.checks],
        }
        # 顺手存进索引，下次直接读取
        for entry in index:
            if entry["id"] == article_id:
                entry["quality"] = quality
                break
        _save_index(index)

    return {"success": True, "content": content, "quality": quality}


MIME_MAP = {"md": "text/markdown", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "pdf": "application/pdf"}
EXPORT_FUNCS = {"md": export.export_md, "docx": export.export_docx, "pdf": export.export_pdf}


@app.get("/api/download/{article_id}")
async def download_article(article_id: str, format: str = "md"):
    """下载文章（支持 md / docx / pdf）。"""
    content = get_article(article_id)
    if content is None:
        return JSONResponse(status_code=404, content={"success": False, "error": "文章不存在"})

    fmt = format.lower()
    if fmt not in EXPORT_FUNCS:
        return JSONResponse(status_code=400, content={"success": False, "error": f"不支持的格式: {fmt}，支持: md, docx, pdf"})

    try:
        data = EXPORT_FUNCS[fmt](content)
        filename = export._get_filename(article_id, fmt)
        return Response(
            content=data,
            media_type=MIME_MAP.get(fmt, "application/octet-stream"),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

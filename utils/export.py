"""文件导出模块：支持 PDF (.md), DOCX (.docx) 格式。"""

import os
import re
from io import BytesIO

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted,
    ListFlowable, ListItem, PageBreak
)
from reportlab.lib import colors


# ─── 公共 ───

def _get_filename(article_id: str, fmt: str) -> str:
    """生成下载文件名。"""
    return f"{article_id}.{fmt}"


# ─── MD ───

def export_md(content: str) -> bytes:
    """直接返回 UTF-8 编码的 Markdown 内容。"""
    return content.encode("utf-8")


# ─── DOCX ───

def export_docx(content: str) -> bytes:
    """将 Markdown 转换为 .docx 文件。"""
    doc = Document()

    # 设置默认字体
    style = doc.styles["Normal"]
    style.font.name = "Microsoft YaHei"
    style.font.size = Pt(11)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.space_after = Pt(6)

    # 设置标题样式
    for i in range(1, 4):
        hs = doc.styles[f"Heading {i}"]
        hs.font.name = "Microsoft YaHei"
        hs.font.color.rgb = RGBColor(0x31, 0x2E, 0x81)

    lines = content.split("\n")
    in_code_block = False
    code_buffer = []
    in_list = False

    for line in lines:
        # 代码块开关
        if line.startswith("```"):
            if in_code_block:
                # 结束代码块，写入
                code_text = "\n".join(code_buffer)
                p = doc.add_paragraph()
                p.style = doc.styles["Normal"]
                p.paragraph_format.left_indent = Inches(0.3)
                run = p.add_run(code_text)
                run.font.name = "Courier New"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x1E, 0x1B, 0x4B)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(4)
                code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # 空行
        if not line.strip():
            if in_list:
                in_list = False
            continue

        # 标题
        if line.startswith("### "):
            doc.add_heading(line[4:], level=3)
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:], level=2)
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
            continue

        # 列表
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            in_list = True
            p = doc.add_paragraph(line.strip()[2:], style="List Bullet")
            continue

        # 序号列表
        match = re.match(r"^\d+[\.\、]\s*(.*)", line.strip())
        if match:
            in_list = True
            p = doc.add_paragraph(match.group(1), style="List Number")
            continue

        # 普通段落（处理内联代码）
        in_list = False
        parts = re.split(r"(`[^`]+`)", line)
        p = doc.add_paragraph()
        for part in parts:
            if part.startswith("`") and part.endswith("`"):
                run = p.add_run(part[1:-1])
                run.font.name = "Courier New"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x43, 0x38, 0xCA)
            else:
                p.add_run(part)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ─── PDF ───

def export_pdf(content: str) -> bytes:
    """将 Markdown 转换为 PDF 文件。"""
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    # 自定义样式
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=18,
        textColor=colors.HexColor("#312E81"),
        spaceAfter=12,
    )
    heading1_style = ParagraphStyle(
        "CustomH1", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=16,
        textColor=colors.HexColor("#312E81"),
        spaceBefore=16, spaceAfter=8,
    )
    heading2_style = ParagraphStyle(
        "CustomH2", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=14,
        textColor=colors.HexColor("#312E81"),
        spaceBefore=12, spaceAfter=6,
    )
    heading3_style = ParagraphStyle(
        "CustomH3", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=12,
        textColor=colors.HexColor("#4338CA"),
        spaceBefore=8, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "CustomBody", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10.5,
        leading=16, spaceAfter=6,
    )
    code_style = ParagraphStyle(
        "CustomCode", parent=styles["Code"],
        fontName="Courier", fontSize=8,
        leading=11, leftIndent=12,
        spaceBefore=4, spaceAfter=4,
        backColor=colors.HexColor("#F5F3FF"),
    )

    elements = []
    lines = content.split("\n")
    in_code_block = False
    code_buffer = []

    for line in lines:
        if line.startswith("```"):
            if in_code_block:
                code_text = "\n".join(code_buffer)
                elements.append(Preformatted(code_text, code_style))
                code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        if not line.strip():
            elements.append(Spacer(1, 4))
            continue

        if line.startswith("### "):
            elements.append(Paragraph(line[4:], heading3_style))
        elif line.startswith("## "):
            elements.append(Paragraph(line[3:], heading2_style))
        elif line.startswith("# "):
            elements.append(Paragraph(line[2:], heading1_style))
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            text = line.strip()[2:]
            elements.append(Paragraph(f"• {text}", body_style))
        elif re.match(r"^\d+[\.\、]\s*(.*)", line.strip()):
            match = re.match(r"^\d+[\.\、]\s*(.*)", line.strip())
            elements.append(Paragraph(match.group(1), body_style))
        else:
            # 内联代码处理
            text = re.sub(r"`([^`]+)`", r'<font face="Courier" color="#4338CA">\1</font>', line)
            elements.append(Paragraph(text, body_style))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()

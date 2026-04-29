"""
Attachment extraction helpers for AI Copilot.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List
import csv
import json

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_TEXT_CHARS_PER_FILE = 6000


def _trim(text: str, limit: int = MAX_TEXT_CHARS_PER_FILE) -> str:
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "\n...[内容已截断]"


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _extract_csv(data: bytes) -> str:
    text = _decode_text(data)
    rows = list(csv.reader(text.splitlines()))
    preview = rows[:30]
    return "\n".join([" | ".join(cell.strip() for cell in row[:12]) for row in preview])


def _extract_excel(data: bytes) -> str:
    import pandas as pd

    xls = pd.ExcelFile(BytesIO(data))
    lines: List[str] = []
    for sheet_name in xls.sheet_names[:5]:
        df = pd.read_excel(xls, sheet_name=sheet_name, nrows=30)
        lines.append(f"Sheet: {sheet_name}")
        lines.append(df.fillna("").to_string(index=False, max_cols=12))
    return "\n\n".join(lines)


def _extract_pdf(data: bytes) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(BytesIO(data))
    pages: List[str] = []
    for page in reader.pages[:10]:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _extract_docx(data: bytes) -> str:
    from docx import Document as DocxDocument

    document = DocxDocument(BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _extract_image(data: bytes) -> Dict[str, Any]:
    from PIL import Image

    image = Image.open(BytesIO(data))
    return {
        "width": image.width,
        "height": image.height,
        "format": image.format,
        "mode": image.mode,
    }


def extract_attachment(filename: str, content_type: str | None, data: bytes) -> Dict[str, Any]:
    suffix = Path(filename or "").suffix.lower()
    base: Dict[str, Any] = {
        "filename": filename or "未命名附件",
        "content_type": content_type or "",
        "size": len(data),
        "kind": "file",
        "extract_status": "success",
    }

    if len(data) > MAX_FILE_SIZE:
        return {
            **base,
            "extract_status": "skipped",
            "summary": "文件超过10MB，未纳入AI上下文。",
        }

    try:
        if (content_type or "").startswith("image/") or suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
            info = _extract_image(data)
            return {
                **base,
                "kind": "image",
                "image": info,
                "summary": f"图片附件：{info.get('format') or suffix}，尺寸 {info['width']}x{info['height']}。当前文本模型无法直接识别图片内容，请结合用户文字说明分析。",
            }

        if suffix in {".txt", ".md", ".log"} or (content_type or "").startswith("text/"):
            return {**base, "text": _trim(_decode_text(data))}

        if suffix == ".csv":
            return {**base, "text": _trim(_extract_csv(data))}

        if suffix in {".xlsx", ".xls"}:
            return {**base, "text": _trim(_extract_excel(data))}

        if suffix == ".pdf":
            return {**base, "text": _trim(_extract_pdf(data))}

        if suffix == ".docx":
            return {**base, "text": _trim(_extract_docx(data))}

        if suffix == ".json":
            parsed = json.loads(_decode_text(data))
            return {**base, "text": _trim(json.dumps(parsed, ensure_ascii=False, indent=2))}

        return {
            **base,
            "extract_status": "unsupported",
            "summary": "暂不支持解析该文件类型，已作为附件记录但未纳入正文分析。",
        }
    except Exception as exc:
        return {
            **base,
            "extract_status": "failed",
            "summary": f"附件解析失败：{type(exc).__name__}",
        }

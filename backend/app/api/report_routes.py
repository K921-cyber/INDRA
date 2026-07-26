"""
TRINETRA — Word (.docx) Report Export Route
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.core.api_key_auth import require_api_key
from app.services.docx_report_service import build_report_docx

router = APIRouter(prefix="/api/report", tags=["report"])


class DocxReportRequest(BaseModel):
    target: Optional[str] = None
    markdown: str
    title: Optional[str] = None


@router.post("/docx")
async def export_docx(req: DocxReportRequest, _key: str = Depends(require_api_key)):
    title = req.title or (f"{req.target} — Investigation Report" if req.target else "Investigation Report")
    buf = build_report_docx(title=title, target=req.target or "", markdown_text=req.markdown)

    safe_target = "".join(c if c.isalnum() else "_" for c in (req.target or "report"))
    filename = f"trinetra-report-{safe_target}.docx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
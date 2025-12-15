# services/api/app/api/routes/b22_diff_export_routes.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import base64
import io
import json
import zipfile
from datetime import datetime

router = APIRouter()


class DiffExportRequest(BaseModel):
    mode: str
    layers: List[str]
    screenshotBefore: str  # data URL (e.g. "data:image/png;base64,...")
    screenshotAfter: str
    screenshotDiff: str
    # optional metadata if you want to pass file names, etc.
    beforeLabel: Optional[str] = None
    afterLabel: Optional[str] = None
    diffLabel: Optional[str] = None


@router.post("/diff-report")
def export_diff_report(payload: DiffExportRequest):
    """
    Build a ZIP file containing:
      - before.png
      - after.png
      - diff.png
      - metadata.json
    and return it as a streamed download.
    """

    def decode_data_url(data_url: str) -> bytes:
        """
        data_url is like: 'data:image/png;base64,AAAA....'
        We only need the base64 part.
        """
        if "," not in data_url:
            raise ValueError("Invalid data URL")
        header, encoded = data_url.split(",", 1)
        return base64.b64decode(encoded)

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        # decode + write images
        try:
            before_bytes = decode_data_url(payload.screenshotBefore)
            after_bytes = decode_data_url(payload.screenshotAfter)
            diff_bytes = decode_data_url(payload.screenshotDiff)
        except Exception as exc:
            # In a real app you'd want more robust error handling/logging
            raise ValueError(f"Failed to decode screenshots: {exc}") from exc

        # Choose filenames (you can tweak this)
        before_name = f"{payload.beforeLabel or 'before'}.png"
        after_name = f"{payload.afterLabel or 'after'}.png"
        diff_name = f"{payload.diffLabel or 'diff'}.png"

        zipf.writestr(before_name, before_bytes)
        zipf.writestr(after_name, after_bytes)
        zipf.writestr(diff_name, diff_bytes)

        # metadata.json
        metadata = {
            "mode": payload.mode,
            "layers": payload.layers,
            "beforeLabel": payload.beforeLabel,
            "afterLabel": payload.afterLabel,
            "diffLabel": payload.diffLabel,
            "exportedAt": datetime.utcnow().isoformat() + "Z",
        }
        zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

    zip_buffer.seek(0)

    filename = f"diff-report-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )

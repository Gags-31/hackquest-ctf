"""Lightweight CSV/PDF exporters with no extra runtime dependencies."""
import csv
import io
from datetime import datetime, timezone

from .security import utcnow


def to_csv(headers: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")


def _esc(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def to_pdf(title: str, headers: list[str], rows: list[list]) -> bytes:
    """Generate a minimal, valid single-page PDF containing tabular text."""
    safe = lambda v: _esc(str(v))[:90]
    lines = ["BT /F1 11 Tf 40 810 Td 14 TL", f"({safe(title)}) Tj T*",
             "/F1 9 Tf 12 TL"]
    header = "  |  ".join(safe(h) for h in headers)
    lines.append(f"({header}) Tj T*")
    for row in rows[:60]:
        text = "  |  ".join(safe(v) for v in row)
        lines.append(f"({text}) Tj T*")
    lines.append("ET")
    stream = "\n".join(lines).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 1191] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    )
    return out.getvalue()

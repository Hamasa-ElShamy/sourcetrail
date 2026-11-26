"""Split files into passages: (location, text). Locations are what you cite: page, cell, line."""
import re
from pathlib import Path

SUPPORTED = (".pdf", ".docx", ".xlsx", ".txt", ".md")
_SENT = re.compile(r"(?<=[.!?؟])\s+|\n+")


def _sentences(text):
    return [s.strip() for s in _SENT.split(text) if len(s.strip()) > 3]


def extract(path):
    ext = Path(path).suffix.lower()
    if ext in (".txt", ".md"):
        out = []
        for i, line in enumerate(Path(path).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for s in _sentences(line):
                out.append((f"line {i}", s))
        return out
    if ext == ".docx":
        import docx
        d = docx.Document(path)
        out = []
        for i, p in enumerate(d.paragraphs, 1):
            for s in _sentences(p.text):
                out.append((f"paragraph {i}", s))
        for ti, t in enumerate(d.tables, 1):
            for ri, row in enumerate(t.rows, 1):
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    out.append((f"table {ti} row {ri}", " ".join(cells)))
        return out
    if ext == ".pdf":
        import pypdfium2 as pdfium
        out = []
        doc = pdfium.PdfDocument(path)
        try:
            for n in range(len(doc)):
                page = doc[n]
                tp = page.get_textpage()
                text = tp.get_text_range()
                tp.close()
                page.close()
                for s in _sentences(text):
                    out.append((f"page {n + 1}", s))
        finally:
            doc.close()
        return out
    if ext == ".xlsx":
        return _xlsx(path)
    raise ValueError(f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED)}")


def _xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    out = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows())
        if not rows:
            continue
        header = {c.column: str(c.value) for c in rows[0] if c.value is not None}
        for row in rows[1:] if len(rows) > 1 else rows:
            label = next((str(c.value) for c in row if isinstance(c.value, str)), "")
            for c in row:
                if c.value is None:
                    continue
                if isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
                    v = c.value
                    shown = f"{v * 100:g}%" if "%" in (c.number_format or "") else f"{v:g}"
                    text = f"{label} {header.get(c.column, '')} {shown}".strip()
                else:
                    text = str(c.value)
                out.append((f"sheet {ws.title}, cell {c.coordinate}", text))
    return out

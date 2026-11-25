import openpyxl, docx, pytest
from reportlab.pdfgen import canvas
from sourcetrail import Library, trace
from sourcetrail.cli import main


@pytest.fixture
def lib(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    c = canvas.Canvas(str(src / "Research_Paper.pdf"))
    c.drawString(72, 700, "Introduction to the study.")
    c.showPage()
    c.drawString(72, 700, "The model achieved 92% accuracy on the held-out test set.")
    c.save()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["Metric", "Value"])
    ws.append(["Accuracy", 0.92])
    ws["B2"].number_format = "0%"
    ws.append(["Training time hours", 14])
    wb.save(src / "Experiment_Report.xlsx")
    d = docx.Document()
    d.add_paragraph("In an earlier run the model reached 89% accuracy on validation data.")
    d.save(src / "Old_Notes.docx")
    (src / "notes.txt").write_text("The team has twelve members.\nBudget was 5000 dollars.\n")
    lib = Library(str(tmp_path / "t.db"))
    lib.add_folder(src)
    return lib


def test_supported_with_page_and_cell(lib):
    r = trace(lib, "The model achieved 92% accuracy")
    assert r.status == "CONFLICTING"  # old notes say 89%
    locs = {(e.path.split("/")[-1], e.loc, e.kind) for e in r.evidence}
    assert ("Research_Paper.pdf", "page 2", "supports") in locs
    assert ("Experiment_Report.xlsx", "sheet Results, cell B2", "supports") in locs
    assert ("Old_Notes.docx", "paragraph 1", "differs") in locs


def test_only_support(tmp_path):
    (tmp_path / "a.txt").write_text("Training took 14 hours on one GPU.\n")
    lib = Library(str(tmp_path / "d.db"))
    lib.add_file(tmp_path / "a.txt")
    r = trace(lib, "Training took 14 hours")
    assert r.status == "SUPPORTED" and r.evidence[0].loc == "line 1"


def test_differs(tmp_path):
    (tmp_path / "a.txt").write_text("Training took 20 hours on one GPU.\n")
    lib = Library(str(tmp_path / "d.db"))
    lib.add_file(tmp_path / "a.txt")
    assert trace(lib, "Training took 14 hours").status == "DIFFERS"


def test_not_found(lib):
    assert trace(lib, "The company revenue grew 40% in Brazil").status == "NOT FOUND"


def test_mentioned_without_number(lib):
    assert trace(lib, "The team has twelve members").status == "MENTIONED"


def test_decimal_equals_percent(lib):
    r = trace(lib, "Accuracy was 0.92")
    assert r.status in ("SUPPORTED", "CONFLICTING")


def test_reindex_unchanged_and_changed(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("Budget is 100 dollars.\n")
    lib = Library(str(tmp_path / "d.db"))
    assert lib.add_file(f) == 1
    assert lib.add_file(f) is None
    f.write_text("Budget is 200 dollars.\n")
    assert lib.add_file(f) == 1
    assert trace(lib, "Budget is 200 dollars").status == "SUPPORTED"
    assert trace(lib, "Budget is 100 dollars").status == "DIFFERS"  # old text is gone


def test_cli(tmp_path, capsys):
    f = tmp_path / "a.txt"
    f.write_text("Revenue was 300 million.\n")
    db = str(tmp_path / "c.db")
    assert main(["--db", db, "add", str(f)]) == 0
    assert main(["--db", db, "trace", "Revenue was 300 million"]) == 0
    out = capsys.readouterr().out
    assert "Evidence Status: SUPPORTED" in out and "line 1" in out
    assert main(["--db", db, "trace", "Revenue was 999 million"]) == 1


def test_unsupported(tmp_path):
    (tmp_path / "x.zip").write_bytes(b"x")
    assert main(["--db", str(tmp_path / "d.db"), "add", str(tmp_path / "x.zip")]) == 3


def test_stem_and_synonym_and_magnitude(tmp_path):
    import importlib
    T = importlib.import_module('sourcetrail.trace')
    assert T._stem("growing") == T._stem("grew") == "increase"
    assert T._stem("revenues") == T._stem("sales")
    assert T._numbers("1.2 million users") == [(1200000.0, False)]
    assert T._numbers("40 percent") == [(40.0, True)]
    assert T._numbers("٤٠٪") == [(40.0, True)]
    assert T._stem("الإيرادات") == T._stem("ايرادات")
    assert T._same((2.5e6, False), (2500000.0, False))

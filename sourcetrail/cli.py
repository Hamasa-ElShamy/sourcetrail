import argparse
import sys
from pathlib import Path

from . import __version__
from .db import Library
from .trace import trace, format_result


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sourcetrail", description="Trace a claim back to its evidence in your files.")
    ap.add_argument("--db", help="database path (default: ~/.sourcetrail.db or $SOURCETRAIL_DB)")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a_ = sub.add_parser("add", help="index a file or folder")
    a_.add_argument("path")
    t = sub.add_parser("trace", help="find evidence for a claim")
    t.add_argument("claim")
    sub.add_parser("list", help="list indexed files")
    r = sub.add_parser("remove", help="remove a file from the index")
    r.add_argument("path")
    a = ap.parse_args(argv)
    try: lib = Library(a.db)
    except Exception as e:
        print(f"error: cannot open the database ({e}). Use --db with a path you can write to.", file=sys.stderr); return 3
    try:
        if a.cmd == "add":
            p = Path(a.path)
            if p.is_dir():
                res, errors = lib.add_folder(p)
                for f, n in res.items():
                    print(f"{'unchanged' if n is None else f'{n} passages'}  {f}")
                for f, e in errors.items():
                    why = "empty or damaged file" if type(e).__name__ in ("PackageNotFoundError", "BadZipFile") or "Package not found" in str(e) else ("damaged or password-protected PDF" if "PDFium" in str(e) or "Pdfium" in str(e) else str(e))
                    print(f"skipped  {f}  ({why})", file=sys.stderr)
            else:
                n = lib.add_file(p)
                print("unchanged" if n is None else f"indexed {n} passages")
        elif a.cmd == "trace":
            if not a.claim.strip():
                print("error: give the claim to check, for example: sourcetrail trace \"The model reached 92% accuracy\"", file=sys.stderr); return 3
            res = trace(lib, a.claim)
            print(format_result(res))
            return 0 if res.status in ("SUPPORTED", "MENTIONED") else 1
        elif a.cmd == "list":
            for f in lib.files():
                print(f)
        elif a.cmd == "remove":
            lib.remove_file(a.path)
            print("removed")
    except FileNotFoundError as e:
        print(f"error: file or folder not found: {e.filename or e}", file=sys.stderr)
        return 3
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

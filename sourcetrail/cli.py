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
    lib = Library(a.db)
    try:
        if a.cmd == "add":
            p = Path(a.path)
            if p.is_dir():
                res, errors = lib.add_folder(p)
                for f, n in res.items():
                    print(f"{'unchanged' if n is None else f'{n} passages'}  {f}")
                for f, e in errors.items():
                    print(f"skipped  {f}  ({e})", file=sys.stderr)
            else:
                n = lib.add_file(p)
                print("unchanged" if n is None else f"indexed {n} passages")
        elif a.cmd == "trace":
            res = trace(lib, a.claim)
            print(format_result(res))
            return 0 if res.status in ("SUPPORTED", "MENTIONED") else 1
        elif a.cmd == "list":
            for f in lib.files():
                print(f)
        elif a.cmd == "remove":
            lib.remove_file(a.path)
            print("removed")
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

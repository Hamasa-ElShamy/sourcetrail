# SourceTrail

[![tests](https://github.com/mohamed-elshamy-ai/sourcetrail/actions/workflows/tests.yml/badge.svg)](https://github.com/mohamed-elshamy-ai/sourcetrail/actions/workflows/tests.yml) ![tests: 10 passing](https://img.shields.io/badge/tests-10%20passing-brightgreen) ![license: MIT](https://img.shields.io/badge/license-MIT-blue)

**Where did I get that number from?**

SourceTrail indexes your own files (PDF, Word, Excel, text) in a local SQLite database. Give it a claim and it shows the exact page, cell or line that supports it, and warns when another file gives a different number for the same thing.

It is not "ask an AI about your files". It goes back from a piece of information to the evidence, and shows you the original sentence so you can judge for yourself. Everything stays on your machine. No AI model, no cloud.

PDF reading uses [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) (Apache-2.0 / BSD, PDFium). No AGPL code is installed.

## Install and use

```bash
git clone https://github.com/mohamed-elshamy-ai/sourcetrail
cd sourcetrail
pip install -e .

sourcetrail add ~/Research            # index a folder (re-running only re-reads changed files)
sourcetrail trace "The model achieved 92% accuracy"
sourcetrail list
sourcetrail remove ~/Research/old.pdf
```

Real output from [`demo/`](demo/) (full output in `demo/demo-output.txt`):

```
CLAIM:
The model achieved 92% accuracy

Sources:
1. Research_Paper.pdf  (supports)
   page 2
   "The model achieved 92% accuracy on the held-out test set."
2. Experiment_Report.xlsx  (supports)
   sheet Results, cell B2
   "Accuracy Value 92%"
3. Old_Notes.docx  (gives a different number)
   paragraph 1
   "In the first run the model reached 89% accuracy on validation data."

Evidence Status: CONFLICTING
Sources disagree on the number. Check which one is the original.
```

Statuses: `SUPPORTED`, `CONFLICTING` (some support, some differ), `DIFFERS` (only different numbers found), `MENTIONED` (claim has no number and relevant text exists), `NOT FOUND`. Exit code is 0 for SUPPORTED or MENTIONED and 1 otherwise.

The database is `~/.sourcetrail.db`, or set `SOURCETRAIL_DB` or pass `--db`.

## Install on Windows, macOS and Linux

Needs Python 3.9 or newer. On Windows install it from python.org and tick "Add python.exe to PATH".

```bash
# Windows (PowerShell):  py -m pip install git+https://github.com/mohamed-elshamy-ai/sourcetrail
# macOS:                 python3 -m pip install git+https://github.com/mohamed-elshamy-ai/sourcetrail
# Linux:                 python3 -m pip install --user git+https://github.com/mohamed-elshamy-ai/sourcetrail
```

Tested on Linux only. Android: not available (needs local files). Technical notes (architecture, algorithms, testing): [ARCHITECTURE.md](ARCHITECTURE.md). Website: https://mohamed-elshamy-ai.github.io/sourcetrail/

## How it works

1. **Index.** Each file is split into passages with a citable location: PDF page, Word paragraph or table row, text line, Excel cell. Excel numbers are stored with their row label and column header (for example "Accuracy Value 92%"; 0.92 in a percent-formatted cell is stored as 92%). Passages go into SQLite with FTS5 full-text search. A file is only re-read when its hash changes.
2. **Understand the claim.** Take its meaningful words (stop words removed) and its numbers.
3. **Find evidence.** Search passages that share the words. A passage counts as relevant if it has at least half of the claim's words (one word is enough for spreadsheet cells).
4. **Check the numbers.** A relevant passage with the same numbers supports the claim. One with different numbers of the same kind (percent vs percent) is reported as a difference. 0.92 and 92% are treated as equal, and Arabic digits are understood.
5. **Report** the status with every source and its exact location.

## Limitations

- Matching is by shared words and numbers. It does not understand meaning. Synonyms ("achieved" vs "reached") only count if enough other words match, and unrelated passages that share words can show up as a "different number". Always read the quoted sentence.
- `SUPPORTED` means a passage with the same numbers and similar words exists. It does not prove the claim is true or that the source is correct.
- Claims without numbers can only get `MENTIONED` or `NOT FOUND`.
- Scanned PDFs and images are not read (no OCR yet). Excel formulas are read as their last saved value.
- No semantic (embedding) search, entity extraction, LLM mode or browser extension yet.

## Development

```bash
pip install -e ".[dev]" && pytest
```

## Roadmap (not yet built)

OCR for scanned files, embeddings for meaning-based matching, entity extraction (names, dates), a window app, a browser extension.

## License

MIT

## Matching: what it does and does not understand (v0.2)

Examples with real output are in [`demo/demo-output-matching.txt`](demo/demo-output-matching.txt) (files in `demo/sources2/`).

- Word forms: `growing`, `grew`, `grow` match; `revenues` and `sales` match through a small hand-written synonym list (`SYN_GROUPS` in `sourcetrail/trace.py`, English and Arabic, about 13 groups).
- Number sizes: `1,200,000`, `1.2 million` and `١٫٢ مليون` are the same number; `40 percent`, `40%` and `٤٠٪` are the same.
- Arabic: light normalisation (alef and ta marbuta forms, the `ال` prefix, common plural endings).
- Still NOT understood: real meaning. There are no embeddings and no AI model. A claim worded in a way the synonym list does not cover returns NOT FOUND. That does not mean the claim is false.
- Arabic claims scan every indexed passage instead of using the search index, which is fine for a personal library and slower for very large ones.

## Related tools

Tools that check claims against sources exist: [proofpath](https://github.com/Yigtwxx/proofpath), [claim-grounding](https://github.com/vbcdng/claim-grounding) and [claimtrace](https://github.com/IzbassarO/claimtrace). SourceTrail is a smaller, offline word-matching version that points to the page, sheet or cell and handles Arabic. It has no semantic or embedding matching, so the tools above may find matches it misses.

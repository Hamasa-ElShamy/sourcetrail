# SourceTrail: technical notes

**Modules**
- `extract.py`: splits files into passages with citable locations. PDF per page (pypdfium2), Word per paragraph and table row, text per line, Excel per cell. For a numeric Excel cell the passage is "row label + column header + value" (a percent-formatted 0.92 becomes "92%"), so a bare number has context.
- `db.py`: `Library`, a SQLite file with a `passages` table and an FTS5 index. Files are hashed, and a file is only re-read when its hash changes.
- `trace.py`: claim analysis and evidence status. `cli.py`: command line.

**Algorithm**
1. Claim keywords: lower-cased words without stop words, with a light plural stripper. Claim numbers: digits (Arabic digits too), with a flag for percent.
2. FTS5 query: OR of the keywords with prefix matching, top 200 passages.
3. A passage is relevant when it contains at least half of the keywords (one keyword for spreadsheet cells).
4. For claims with numbers: relevant passage with all the claim's numbers supports; relevant passage with other numbers of the same kind (percent against percent) differs. 0.92 and 92% are equal.
5. Status: SUPPORTED, CONFLICTING, DIFFERS, MENTIONED (no number in claim), NOT FOUND.

**Design decisions**
- Return the original quoted sentence and exact location, so the user judges the evidence. The tool never states a claim is true.
- No cloud, no model: it is auditable and private. Semantic (embedding) matching is not built because shipping and verifying a local model was out of scope for this release, and it is listed as missing.
- Incremental indexing so large folders are cheap to refresh.

**Testing** (9 tests): support with page and cell locations across PDF, Excel and Word, conflicts, differs, not found, claims without numbers, decimal against percent, re-indexing when a file changes (old text disappears), CLI exit codes, unsupported files.

**Limits**: word and number matching only, false matches are possible, no OCR, no embeddings.

## v0.2 additions

`trace.py` now builds search terms from each word, its stem and its synonym group (`_fts_query`), normalises Arabic (`_norm_ar`), and reads magnitude words (`million`, `ألف`, `مليون`) into numbers. Arabic claims scan all passages because SQLite prefix search cannot find words with an attached `ال`. Tested in `tests/test_sourcetrail.py` (10 tests). Limit: the synonym list is small and hand-made, so meaning outside it is not matched.

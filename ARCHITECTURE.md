# SourceTrail: technical notes / الشرح التقني

## English

**Modules**
- `extract.py`: splits files into passages with citable locations. PDF per page (PyMuPDF), Word per paragraph and table row, text per line, Excel per cell. For a numeric Excel cell the passage is "row label + column header + value" (a percent-formatted 0.92 becomes "92%"), so a bare number has context.
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

## بالعربي

**الأجزاء**: `extract.py` بيقسم الملفات لفقرات بمكانها (صفحة PDF، فقرة Word، سطر، خلية Excel). الخلية الرقمية بتتخزن مع اسم الصف وعنوان العمود عشان الرقم يبقى ليه سياق. `db.py` قاعدة SQLite بفهرس FTS5 وبتعيد قراءة الملف بس لو اتغير. `trace.py` بيحلل الجملة ويحدد الحالة.

**الخوارزمية**: كلمات الجملة المهمة وأرقامها، بحث FTS5، الفقرة بتعتبر مرتبطة لو فيها نصف الكلمات على الأقل، لو فيها نفس الأرقام = بتدعم، ولو فيها أرقام تانية من نفس النوع = مختلفة. ٠.٩٢ = ٩٢٪. الحالات: SUPPORTED وCONFLICTING وDIFFERS وMENTIONED وNOT FOUND.

**قرارات التصميم**: بنرجع الجملة الأصلية ومكانها بالظبط عشان انت تحكم، والأداة ما بتقولش إن الجملة صح. من غير سحابة ولا موديل عشان تتراجع وتبقى خاصة. البحث بالمعنى (embeddings) لسه مش مبني وده مكتوب في الحدود.

**الاختبار**: ٩ اختبارات تغطي الدعم مع الصفحة والخلية، التعارض، الاختلاف، عدم الوجود، وإعادة الفهرسة.

**الحدود**: مطابقة كلمات وأرقام بس، ممكن تطلع مطابقات غلط، مفيش OCR ولا embeddings.


## v0.2 additions / إضافات الإصدار 0.2

**English.** `trace.py` now builds search terms from each word, its stem and its synonym group (`_fts_query`), normalises Arabic (`_norm_ar`), and reads magnitude words (`million`, `ألف`, `مليون`) into numbers. Arabic claims scan all passages because SQLite prefix search cannot find words with an attached `ال`. Tested in `tests/test_sourcetrail.py` (10 tests). Limit: the synonym list is small and hand-made, so meaning outside it is not matched.

**بالعربي.** أضفنا تجذيع بسيط للإنجليزي والعربي، وقائمة مرادفات صغيرة (زاد/ارتفع، إيرادات/مبيعات...)، وفهم الأرقام بالمليون والألف والأرقام الهندية. الحد: القائمة صغيرة ومكتوبة يدوي، فالمعنى خارجها مش بيتطابق، ومفيش نموذج ذكاء اصطناعي.

# Build, Vellum Profiles & Validation Gates

## Editions

`python3 scripts/build.py` builds both omnibus editions from local inputs after
dependency installation. Pass `--edition reading` or `--edition illustrated`
to build a single omnibus. Both commands rebuild the components.

1. **Reading Edition (`--edition reading`)**:
   - Crisp `#ede6d4` ground, `#161918` ink, and `#a32b24` rubrication on
     `504 × 720 pt` (`7 × 10 in`) pages, recto-aligned across book boundaries,
     with consolidated backmatter generated dynamically from
     `bibliography-records.json` and `SOURCES.json`.
2. **Illustrated Edition (`--edition illustrated`)**:
   - Applies deterministic `96 dpi` vellum finishing (`binding/vellum.py`)
     underneath pure vector typography, procedural plates, and cipher strokes,
     using protective masks (`PADDING_PT = 3`) so ink contrast and `#a32b24`
     rubric marks never muddy.
   - Default `--vellum-profile light` uses half-strength warm pigment without
     independent pixel noise; `--vellum-profile full` reproduces denser pigment.

| Output | Local path |
| --- | --- |
| Reading PDF and binding log | `binding/out/` |
| Illustrated PDF and binding log | `binding/out/illustrated/` |
| Component PDFs and plate maps | `books/*/out/` |
| Plotter SVGs and wash previews | `books/*/build/` |
| Books I–II WAVs and Pure Data patches | `books/*/canon/out/` |

With the same dependencies, the build fixes the PDF timestamp through
`SOURCE_DATE_EPOCH` unless the caller has set it. GitHub Actions packages these
outputs as artifacts. The source tree carries the builders and input files.

For file entries in [SOURCES.json](../SOURCES.json), `tree_sha256` is the SHA-256
of the imported bytes. The font entry hashes a path-sorted list of
`<sha256>  <relative path>` lines for the font binaries and license notices.

## Automated Validation (`binding/validate.py` & `binding/validate_typeset.py`)

Every build verifies:
- `504 × 720 pt` trim dimensions on every leaf.
- Recto (`start_page % 2 == 1`) book starts and clean blank alignment leaves.
- Exact `source_sha256` provenance and complete `binding-log.json` page maps.
- Survival of `lifted-pen` `M`/`L`/`Q` vector subpaths inside the bound PDF.
- Strict `(y, x)` ground ordering (`ground_ordered`) of all `#a32b24` / `#161918`
  two-point marks on *Nota Clausa* plates.
- Post-vellum rendered contrast and `#a32b24` rubric pixel presence on the
  illustrated edition.

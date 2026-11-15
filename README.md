# Codex Speculorum

*Liber Canonum — Of Symmetry, Logic, Canon & Remainder*

Volume II of the Codex series uses the 7 × 10 in setting, native procedural plates, and Right of Reply register of [Codex Intervallorum](https://github.com/JosiahAlanLee/Codex-Intervallorum). The current draft contains the prologue, Books I–II, and the closing *Quaestio* and *Nota Clausa*.

## Read the current draft

Download the artifacts from a successful [Build Codex Speculorum run](https://github.com/JosiahAlanLee/Codex_Speculorum/actions/workflows/build.yml).

- **Codex-Speculorum-reading** contains the reading PDF and binding log.
- **Codex-Speculorum-illustrated** contains the vellum-finished PDF and binding log.
- **Codex-Speculorum-components** contains the individual book proofs, plotter SVGs, washes, and Book I’s 48 kHz WAV and Pure Data canon.

## Manuscript and source

| Place | Text | Source |
| --- | --- | --- |
| Prologue | De Officio Mensuratoris | [Manuscript](books/00_prologus/manuscript/prologus.md) |
| I | Speculum Cancrizans | [Manuscript](books/01_liber_primus/manuscript/reading-edition.md) · [Plates I–V](books/01_liber_primus/plates/tabulae.py) · [Canon](books/01_liber_primus/canon/play_koopman_canon.py) |
| II | Bibliotheca Sine Periodo | [Manuscript](books/02_liber_secundus/manuscript/reading-edition.md) · [Plate VI](books/02_liber_secundus/plates/tabulae.py) |
| Closing gathering | Quaestio & Nota Clausa | [Quaestio](books/07_clausa/manuscript/quaestio.md) · [Regula](books/07_clausa/clausa/REGULA.md) · [Tabula](books/07_clausa/clausa/TABULA.md) |

The [volume manifest](volume.json) sets the binding order. The [bibliography](bibliography-records.json) supplies the shared backmatter, and [SOURCES.json](SOURCES.json) records the imported code and typefaces. See [AGENTS.md](AGENTS.md) for the Right of Reply and its [objections register](docs/objections/register.md).

## Build

Use Python 3.12 or later.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build.py
```

The build runs the project checks and unit tests, generates the components, and binds and validates both editions. See the [build instructions](docs/BUILD.md) for output paths and vellum profiles and the [typeface inventory](common/fonts/README.md) for font sources and notices.

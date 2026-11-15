# Regula Notae Clausae (Pluggable Lattice Specification)

1. **Key Derivation**: Three uppercase names from the bound volume separated by
   single spaces (`KEY`). Field `k` seeds `SplitMix64` from the first 8 big-endian
   bytes of `SHA-256(KEY + "/" + k)`.
2. **Simulation & Capacity**: `ClausaEngine` (`common/ciphers/clausa_base.py`)
   selects `1,440` (`240` characters × `6` bits) distinct arena cells inside an
   `89 × 89` circular ground (`1.4 mm` cell pitch). Replace `select_ordered_cells`
   with the deterministic integer simulation native to Volume II's domain.
3. **Ground-Order Invariant (Clause 17)**: Regardless of simulation trajectory or
   selection order, two-point strokes (`#a32b24` = `1`, `#161918` = `0`) are
   sorted strictly by `(gy, gx)` before SVG and PDF emission, verified at build
   time by `ground_ordered` in `binding/validate_typeset.py`.

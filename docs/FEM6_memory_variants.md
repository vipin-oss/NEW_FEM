# Memory-term sensitivity: where the memory acts, and KV vs fractional Zener

Both tables are produced by `python3 python/run_memory_variants.py`
(`results/memory_variants.{md,json}`). Configuration: the **application case**
(length-extensional, poling x, plane stress, 24×2, `μ = 0`), mode 4 at
6.727 MHz, `k_eff² = 0.4650`, `ωτ = 0.3`.

## S1 — the memory matrix matters more than expected

The model is `M q̈ + K q + τ^α K_d D^α q = f`, where `K_d` is either the full
condensed `K_eff` (baseline) or only the mechanical block `K_uu`. `K_uu` is
obtained exactly (not approximated) by re-assembling the same mesh with
`e = 0, μ = 0`, for which `K_eff = K_uu` by construction; the dof maps are then
identical (`assert`ed in the script).

`ζ_eff` is measured from the logarithmic decrement of the ring-down peaks of
`V(t)` (20 periods, 12000 steps, 10 nm initial end shortening):

| `K_d` | `α` | `V(0)` (V) | `ζ_eff` |
|---|---|---|---|
| `K_eff` (baseline) | 1.0 | 139.07 | **0.15023** |
| `K_eff` | 0.7 | 139.07 | 0.02600 |
| `K_uu` | 1.0 | 139.07 | 0.06749 |
| `K_uu` | 0.7 | 139.07 | 0.05006 |

Three statements, all measured:

1. **Validation at `α = 1`.** `ζ_eff(K_eff) = 0.15023` against the closed form
   `ζ = ωτ/2 = 0.150` — agreement to 0.15 %. The transient solver reproduces the
   Kelvin–Voigt decay on the *real* model, not just on a scalar test.
2. **The choice changes `ζ` by more than a factor of two.** `0.150` vs `0.067`
   at `α = 1`; the ratio is `K_uu/K_eff ≈ 1 − k_eff²`, i.e. the piezoelectric
   stiffening that the condensed operator carries. A paper that does not say
   which operator receives the memory is reporting an arbitrary damping.
3. **Baseline choice, justified.** `K_eff` is kept because (a) the relaxation is
   driven by the total stress including the depolarisation back-stress, (b) it
   keeps the modal system proportional, so a single `ζ(α)` per mode is defined,
   and (c) it is the only choice for which `k_eff² = (ω_oc² − ω_sc²)/ω_oc²`
   retains its meaning during relaxation. The `K_uu` column is the disclosed
   sensitivity, not an alternative baseline.

## S2 — the Kelvin–Voigt high-frequency artefact, quantified

`|C*|/C_0`: fractional Kelvin–Voigt `|1 + (iωτ)^α|` (grows as `(ωτ)^α`,
unbounded); fractional Zener `|(1 + r(iωτ)^α)/(1 + (iωτ)^α)|` with
`r = C_∞/C_0` (bounded by `r`).

| `ωτ` | `α` | KV | Zener `r=1.1` | Zener `r=2` | KV/Zener |
|---|---|---|---|---|---|
| 0.01 | 1.0 | 1.0000 | 1.0000 | 1.0001 | 1.000 |
| 0.10 | 1.0 | 1.0050 | 1.0010 | 1.0147 | 1.004 |
| 0.30 | 1.0 | 1.0440 | 1.0086 | 1.1170 | 1.035 |
| 1.00 | 1.0 | 1.4142 | 1.0512 | 1.5811 | 1.345 |
| 10.0 | 1.0 | 10.0499 | 1.0991 | 1.9926 | 9.144 |
| 100 | 1.0 | 100.0050 | 1.1000 | 1.9999 | 90.914 |
| 0.30 | 0.7 | 1.2555 | 1.0244 | 1.2652 | 1.226 |
| 1.00 | 0.7 | 1.7053 | 1.0504 | 1.5310 | 1.623 |
| 0.30 | 0.5 | 1.4403 | 1.0333 | 1.3443 | 1.394 |

**At the device operating point** (`ωτ = 0.3`):

| `α` | KV over-predicts the modulus by |
|---|---|
| 1.0 | **+3.5 %** |
| 0.7 | **+22.6 %** |

So KV is defensible at `α = 1` (3.5 % at the operating point) and is **not**
defensible for `α ≲ 0.7` at the same `ωτ`, and it fails completely at high
frequency (91× at `ωτ = 100`). The paper should: keep KV as the model, quote
this table, and state that the Zener form is the physically admissible
alternative whose effect at the operating point is a 3.5 % (α=1) / 22.6 %
(α=0.7) reduction of the dynamic modulus — a number, not a caveat.

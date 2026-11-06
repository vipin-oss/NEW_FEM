# Every number in the manuscript against the JSON it came from

69/69 claims agree; 0 disagree with the JSON, 0 are not found in the text.

| # | claim | manuscript | json | value | status |
|---|---|---|---|---|---|
| 1 | abstract, memory coupling | `0.4650` | `memory_variants.json k2` | `0.4650` | ok |
| 2 | abstract, zeta ratio | `0.449` | `memory_variants.json S1 Kuu/Keff` | `0.449` | ok |
| 3 | abstract, classical limit | `0.15023` | `memory_variants.json S1 Keff zeta` | `0.15023` | ok |
| 4 | abstract, piezo k^2 | `0.5581` | `demo.json flexo_thickness[0].k2_ext` | `0.5581` | ok |
| 5 | thickness, piezo k^2 series (h=10) | `0.55814` | `demo.json flexo_thickness[0].k2_ext` | `0.55814` | ok |
| 6 | thickness, piezo k^2 series (h=1) | `0.55861` | `demo.json flexo_thickness[3].k2_ext` | `0.55861` | ok |
| 7 | thickness, flexo k^2 at h=10 | `1.74e-4` | `demo.json flexo_thickness[0].k2_flexo` | `1.74e-4` | ok |
| 8 | thickness, flexo k^2 at h=1 | `4.2e-3` | `demo.json flexo_thickness[3].k2_flexo` | `4.2e-3` | ok |
| 9 | thickness, flexo growth factor | `24` | `demo.json flexo ratio` | `24` | ok |
| 10 | orientation, extensional f at 0 deg, AR=2 | `5012` | `paper_figures_data.json polar[AR=2,th=0].f_ext_kHz` | `5012` | ok |
| 11 | orientation, extensional f at 90 deg, AR=2 | `5296` | `paper_figures_data.json polar[AR=2,th=90].f_ext_kHz` | `5296` | ok |
| 12 | orientation, extensional f at 0 deg, AR=10 | `4907` | `paper_figures_data.json polar[AR=10,th=0].f_ext_kHz` | `4907` | ok |
| 13 | orientation, extensional f at 90 deg, AR=10 | `5288` | `paper_figures_data.json polar[AR=10,th=90].f_ext_kHz` | `5288` | ok |
| 14 | orientation, worst coupling change (AR=10) | `-18.7` | `paper_figures_data.json polar, min of k2/k2(0)-1` | `-18.7` | ok |
| 15 | orientation, symmetry deviation | `3e-11` | `paper_figures_data.json symmetry max` | `3e-11` | ok |
| 16 | coupling check, closed form | `0.5608` | `coupling_check.json closed_form.k2_2d_closed` | `0.56079` | ok |
| 17 | coupling check, free 48x4 | `0.5608` | `coupling_check.json fem.plane_stress.free_48x4` | `0.56079` | ok |
| 18 | coupling check, 2-D vs 3-D gap | `2.8` | `coupling_check.json rel_gap_2d_vs_3d x100` | `2.8` | ok |
| 19 | mode tracking, worst MAC | `0.9992` | `mode_tracking.json rows min mac` | `0.9992` | ok |
| 20 | orientation, k2 at 0 deg, AR=2 | `0.4448` | `paper_figures_data.json polar[AR=2,th=0]` | `0.4448` | ok |
| 21 | orientation, k2 at 90 deg, AR=2 | `0.3786` | `paper_figures_data.json polar[AR=2,th=90]` | `0.3786` | ok |
| 22 | orientation, k2 at 0 deg, AR=10 | `0.4677` | `paper_figures_data.json polar[AR=10,th=0]` | `0.4677` | ok |
| 23 | orientation, k2 at 90 deg, AR=10 | `0.3801` | `paper_figures_data.json polar[AR=10,th=90]` | `0.3801` | ok |
| 24 | orientation, f1 at 90 deg, AR=10 | `158.1` | `paper_figures_data.json polar[AR=10,th=90].f1_kHz` | `158.1` | ok |
| 25 | application, k2 extensional plane stress | `0.4580` | `application_table.json rows[3].k2` | `0.4580` | ok |
| 26 | application, V0 extensional plane stress | `138.99` | `application_table.json rows[3].V0_V` | `138.99` | ok |
| 27 | application, k2 bending plane stress | `0.1141` | `application_table.json rows[1].k2` | `0.1141` | ok |
| 28 | application, V0 bending plane stress | `2.41` | `application_table.json rows[1].V0_V` | `2.41` | ok |
| 29 | application, f1 extensional plane stress | `147.73` | `application_table.json rows[3].f1_kHz` | `147.73` | ok |
| 30 | application, f mode extensional plane strain | `7161.0` | `application_table.json rows[2].f_kHz` | `7161.0` | ok |
| 31 | closed form, 3-D free bar | `0.5771` | `k2_closed_form.json k2_3d_free` | `0.5771` | ok |
| 32 | closed form, 3-D uniaxial | `0.3748` | `k2_closed_form.json k2_3d_uniaxial` | `0.3748` | ok |
| 33 | closed form, 2-D plane strain | `0.5132` | `k2_closed_form.json k2_2d_plane_strain` | `0.5132` | ok |
| 34 | closed form, x_2D | `1.2768` | `k2_closed_form.json x_2d` | `1.2768` | ok |
| 35 | closed form, C_p[0][0] | `9.5500` | `k2_closed_form.json C_p[0][0] / 1e10` | `9.5500` | ok |
| 36 | closed form, e'C^-1 e | `6.3308` | `k2_closed_form.json eC x1e10` | `6.3308` | ok |
| 37 | independent, clamped-free EB | `143.8` | `independent F1 clamped-free f_EB_kHz` | `143.8` | ok |
| 38 | independent, clamped-free FEM 48x4 | `144.6` | `independent F1 clamped-free mesh[0] f_FEM_kHz` | `144.6` | ok |
| 39 | independent, clamped-clamped EB | `915.0` | `independent F1 clamped-clamped f_EB_kHz` | `915.0` | ok |
| 40 | independent, clamped-clamped FEM 48x4 | `919.2` | `independent F1 clamped-clamped mesh[0] f_FEM_kHz` | `919.2` | ok |
| 41 | independent, clamped-free FEM 128x4 | `144.08` | `independent F1 clamped-free mesh[2] f_FEM_kHz` | `144.08` | ok |
| 42 | independent, beam modulus | `7.63` | `independent F1 E_beam / 1e10` | `7.63` | ok |
| 43 | independent, zeta maximum in alpha | `0.179` | `independent F2 zeta at alpha=0.7, omega*tau=0.3` | `0.179` | ok |
| 44 | independent, zeta at alpha=0.3 | `0.108` | `independent F2 zeta at alpha=0.3, omega*tau=0.3` | `0.108` | ok |
| 45 | sensitivity, spread at h=1 um, per cent, upper bound | `0.5\,\%` | `sensitivity.json spread_h1_pct (range/midpoint)` | `<= 0.5` | ok |
| 46 | sensitivity, spread at h=10 um, per cent, upper bound | `10^{-4}\,\%` | `sensitivity.json spread_h10_pct (range/midpoint)` | `<= 0.0001` | ok |
| 47 | ring-down, decrement at alpha=1 | `0.064` | `paper_figures_data.json notes.P6 zeta_1.0` | `0.064` | ok |
| 48 | ring-down, peak decrement at alpha=0.6 | `0.105` | `paper_figures_data.json notes.P6 zeta_0.6` | `0.105` | ok |
| 49 | ring-down, decrement at alpha=0.4 | `0.085` | `paper_figures_data.json notes.P6 zeta_0.4` | `0.085` | ok |
| 50 | ring-down, error at alpha=0.6 against alpha=1 | `65` | `paper_figures_data.json notes.P6 zeta_0.6/zeta_1.0 - 1, in percent` | `65` | ok |
| 51 | config table, flexo only at h=10 | `1.76e-4` | `config_table rows[0] k2_flexo` | `1.76e-4` | ok |
| 52 | config table, flexo only at h=1 | `5.5e-3` | `config_table rows[3] k2_flexo` | `5.5e-3` | ok |
| 53 | config table, growth with e=0 | `31` | `config_table growth_flexo_only` | `31` | ok |
| 54 | config table, piezo shift at h=1, per cent | `24` | `config_table min flexo_shift x100` | `24` | ok |
| 55 | axes, C_xx poled y | `1.6946` | `independent F5 poling y C_xx / 1e11` | `1.6946` | ok |
| 56 | axes, E_b poled y | `1.3544` | `independent F5 E_beam_pol_y / 1e11` | `1.3544` | ok |
| 57 | axes, kappa11/kappa33 | `39` | `independent F5 kappa_ratio_11_over_33` | `39` | ok |
| 58 | pairing, the hybrid x | `6.34` | `independent F5 x_hybrid x1e4` | `6.34` | ok |
| 59 | pairing, distance from the FEM value | `77` | `independent F5 hybrid_vs_fem_rel x100` | `77` | ok |
| 60 | pairing, poled x on the long faces | `1.61` | `independent F5 poling x top/bottom x_fem x1e5` | `1.61` | ok |
| 61 | independent, flexo x, uniform curvature | `3.570415` | `independent F3 x_analytic x1e4` | `3.570415` | ok |
| 62 | closed form, 3-D free bar | `0.5771` | `k2_closed_form.json k2_3d_free` | `0.5771` | ok |
| 63 | closed form, 3-D uniaxial | `0.3748` | `k2_closed_form.json k2_3d_uniaxial` | `0.3748` | ok |
| 64 | closed form, FEM clamped 48x4 | `0.5596` | `k2_closed_form.json fem.FEM clamped 48x4` | `0.5596` | ok |
| 65 | modulus, Zener r=1.1 at w=0.3, alpha=1 | `1.0086` | `memory_variants.json S2[2].Zener_r1p1` | `1.0086` | ok |
| 66 | modulus, Zener r=1.1 at w=100, alpha=0.7 | `1.0981` | `memory_variants.json S2[11].Zener_r1p1` | `1.0981` | ok |
| 67 | modulus ratio, w=1, alpha=1 | `1.35` | `memory_variants.json S2[3].ratio_KV_over_Zener` | `1.35` | ok |
| 68 | modulus ratio, w=1, alpha=0.7 | `1.62` | `memory_variants.json S2[9].ratio_KV_over_Zener` | `1.62` | ok |
| 69 | modulus ratio, w=100, alpha=1 | `91` | `memory_variants.json S2[5].ratio_KV_over_Zener` | `91` | ok |

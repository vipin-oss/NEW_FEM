# Every number in the manuscript against the JSON it came from

47/47 claims agree; 0 disagree with the JSON, 0 are not found in the text.

| # | claim | manuscript | json | value | status |
|---|---|---|---|---|---|
| 1 | abstract, memory coupling | `0.4650` | `memory_variants.json k2` | `0.4650` | ok |
| 2 | abstract, zeta ratio | `0.449` | `memory_variants.json S1 Kuu/Keff` | `0.449` | ok |
| 3 | abstract, classical limit | `0.15023` | `memory_variants.json S1 Keff zeta` | `0.15023` | ok |
| 4 | abstract, piezo k^2 | `0.5581` | `demo.json flexo_thickness[0].k2_ext` | `0.5581` | ok |
| 5 | thickness, piezo k^2 series (h=10) | `0.55814` | `demo.json flexo_thickness[0].k2_ext` | `0.55814` | ok |
| 6 | thickness, piezo k^2 series (h=1) | `0.55861` | `demo.json flexo_thickness[3].k2_ext` | `0.55861` | ok |
| 7 | thickness, flexo k^2 at h=10 | `1.74e-4` | `demo.json flexo_thickness[0].k2_flexo` | `1.74e-4` | ok |
| 8 | thickness, flexo k^2 at h=1 | `4.17e-3` | `demo.json flexo_thickness[3].k2_flexo` | `4.17e-3` | ok |
| 9 | thickness, flexo growth factor | `23.9` | `demo.json flexo ratio` | `23.9` | ok |
| 10 | coupling check, closed form | `0.56079` | `coupling_check.json closed_form.k2_2d_closed` | `0.56079` | ok |
| 11 | coupling check, free 48x4 | `0.56079` | `coupling_check.json fem.plane_stress.free_48x4` | `0.56079` | ok |
| 12 | coupling check, 2-D vs 3-D gap | `2.8` | `coupling_check.json rel_gap_2d_vs_3d x100` | `2.8` | ok |
| 13 | mode tracking, worst MAC | `0.9992` | `mode_tracking.json rows min mac` | `0.9992` | ok |
| 14 | orientation, k2 at 0 deg, AR=2 | `0.4448` | `paper_figures_data.json polar[AR=2,th=0]` | `0.4448` | ok |
| 15 | orientation, k2 at 90 deg, AR=2 | `0.3786` | `paper_figures_data.json polar[AR=2,th=90]` | `0.3786` | ok |
| 16 | orientation, k2 at 0 deg, AR=10 | `0.4677` | `paper_figures_data.json polar[AR=10,th=0]` | `0.4677` | ok |
| 17 | orientation, k2 at 90 deg, AR=10 | `0.3801` | `paper_figures_data.json polar[AR=10,th=90]` | `0.3801` | ok |
| 18 | orientation, f1 at 0 deg, AR=2 | `149.5` | `paper_figures_data.json polar[AR=2,th=0].f1_kHz` | `149.5` | ok |
| 19 | orientation, f1 at 90 deg, AR=10 | `158.1` | `paper_figures_data.json polar[AR=10,th=90].f1_kHz` | `158.1` | ok |
| 20 | application, k2 extensional plane stress | `0.4580` | `application_table.json rows[3].k2` | `0.4580` | ok |
| 21 | application, V0 extensional plane stress | `138.99` | `application_table.json rows[3].V0_V` | `138.99` | ok |
| 22 | application, k2 bending plane stress | `0.1141` | `application_table.json rows[1].k2` | `0.1141` | ok |
| 23 | application, V0 bending plane stress | `2.41` | `application_table.json rows[1].V0_V` | `2.41` | ok |
| 24 | application, f1 extensional plane stress | `147.73` | `application_table.json rows[3].f1_kHz` | `147.73` | ok |
| 25 | application, f mode extensional plane strain | `7161.0` | `application_table.json rows[2].f_kHz` | `7161.0` | ok |
| 26 | closed form, 3-D free bar | `0.5771` | `k2_closed_form.json k2_3d_free` | `0.5771` | ok |
| 27 | closed form, 3-D uniaxial | `0.3748` | `k2_closed_form.json k2_3d_uniaxial` | `0.3748` | ok |
| 28 | closed form, 2-D plane strain | `0.5132` | `k2_closed_form.json k2_2d_plane_strain` | `0.5132` | ok |
| 29 | closed form, x_2D | `1.2768` | `k2_closed_form.json x_2d` | `1.2768` | ok |
| 30 | closed form, C_p[0][0] | `9.5500` | `k2_closed_form.json C_p[0][0] / 1e10` | `9.5500` | ok |
| 31 | closed form, e'C^-1 e | `6.3308` | `k2_closed_form.json eC x1e10` | `6.3308` | ok |
| 32 | criteria count | `fifty-one` | `summary.json n_total = 51` | `fifty-one` | ok |
| 33 | independent, clamped-free EB | `143.8` | `independent F1 clamped-free f_EB_kHz` | `143.8` | ok |
| 34 | independent, clamped-free FEM 48x4 | `144.6` | `independent F1 clamped-free mesh[0] f_FEM_kHz` | `144.6` | ok |
| 35 | independent, clamped-clamped EB | `915.0` | `independent F1 clamped-clamped f_EB_kHz` | `915.0` | ok |
| 36 | independent, clamped-clamped FEM 48x4 | `919.2` | `independent F1 clamped-clamped mesh[0] f_FEM_kHz` | `919.2` | ok |
| 37 | independent, clamped-free FEM 128x4 | `144.08` | `independent F1 clamped-free mesh[2] f_FEM_kHz` | `144.08` | ok |
| 38 | independent, beam modulus | `7.63` | `independent F1 E_beam / 1e10` | `7.63` | ok |
| 39 | independent, zeta maximum in alpha | `0.179` | `independent F2 zeta at alpha=0.7, omega*tau=0.3` | `0.179` | ok |
| 40 | independent, zeta at alpha=0.3 | `0.108` | `independent F2 zeta at alpha=0.3, omega*tau=0.3` | `0.108` | ok |
| 41 | axes, C_xx poled y | `1.6946` | `independent F5 poling y C_xx / 1e11` | `1.6946` | ok |
| 42 | axes, E_b poled y | `1.3544` | `independent F5 E_beam_pol_y / 1e11` | `1.3544` | ok |
| 43 | axes, kappa11/kappa33 | `39` | `independent F5 kappa_ratio_11_over_33` | `39` | ok |
| 44 | pairing, the hybrid x | `6.34` | `independent F5 x_hybrid x1e4` | `6.34` | ok |
| 45 | pairing, distance from the FEM value | `77` | `independent F5 hybrid_vs_fem_rel x100` | `77` | ok |
| 46 | pairing, poled x on the long faces | `1.61` | `independent F5 poling x top/bottom x_fem x1e5` | `1.61` | ok |
| 47 | independent, flexo x, uniform curvature | `3.570415` | `independent F3 x_analytic x1e4` | `3.570415` | ok |

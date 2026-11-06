# Every number in the manuscript against the JSON it came from

96/96 claims agree; 0 disagree with the JSON, 0 are not found in the text.

| # | claim | manuscript | json | value | status |
|---|---|---|---|---|---|
| 1 | abstract, memory coupling | `0.4650` | `memory_variants.json k2` | `0.4650` | ok |
| 2 | abstract, zeta ratio | `0.450` | `memory_variants.json S1 Kuu/Keff` | `0.450` | ok |
| 3 | abstract, classical limit | `0.15003` | `memory_variants.json S1 Keff zeta` | `0.15003` | ok |
| 4 | abstract, piezo k^2 | `0.5581` | `demo.json flexo_thickness[0].k2_ext` | `0.5581` | ok |
| 5 | thickness, piezo k^2 series (h=10) | `0.55814` | `demo.json flexo_thickness[0].k2_ext` | `0.55814` | ok |
| 6 | thickness, piezo k^2 series (h=1) | `0.55861` | `demo.json flexo_thickness[3].k2_ext` | `0.55861` | ok |
| 7 | thickness, flexo k^2 at h=10 | `1.74e-4` | `demo.json flexo_thickness[0].k2_flexo` | `1.74e-4` | ok |
| 8 | thickness, flexo k^2 at h=1 | `4.2e-3` | `demo.json flexo_thickness[3].k2_flexo` | `4.2e-3` | ok |
| 9 | time step, zeta at 1N | `0.150111` | `dt_study.json memory rows[mult=1].zeta` | `0.150111` | ok |
| 10 | time step, zeta at 2N | `0.150057` | `dt_study.json memory rows[mult=2].zeta` | `0.150057` | ok |
| 11 | time step, zeta at 4N | `0.150029` | `dt_study.json memory rows[mult=4].zeta` | `0.150029` | ok |
| 12 | thickness, flexo growth factor | `24` | `demo.json flexo ratio` | `24` | ok |
| 13 | worked, analytic flexo growth, h^-2 over 10 -> 1 um | `100` | `worked_example.json flexo (h_max/h_min)^2` | `100` | ok |
| 14 | worked, FEM flexo below the analytic x at h=10 | `2.05` | `worked_example.json x_analytic_h10 / demo k2_flexo[0]` | `2.05` | ok |
| 15 | orientation, extensional f at 0 deg, AR=2 | `5012` | `paper_figures_data.json polar[AR=2,th=0].f_ext_kHz` | `5012` | ok |
| 16 | orientation, extensional f at 90 deg, AR=2 | `5296` | `paper_figures_data.json polar[AR=2,th=90].f_ext_kHz` | `5296` | ok |
| 17 | orientation, extensional f at 0 deg, AR=10 | `4907` | `paper_figures_data.json polar[AR=10,th=0].f_ext_kHz` | `4907` | ok |
| 18 | orientation, extensional f at 90 deg, AR=10 | `5288` | `paper_figures_data.json polar[AR=10,th=90].f_ext_kHz` | `5288` | ok |
| 19 | orientation, worst coupling change (AR=10) | `-18.7` | `paper_figures_data.json polar, min of k2/k2(0)-1` | `-18.7` | ok |
| 20 | orientation, symmetry deviation | `3e-11` | `paper_figures_data.json symmetry max` | `3e-11` | ok |
| 21 | coupling check, closed form | `0.5608` | `coupling_check.json closed_form.k2_2d_closed` | `0.56079` | ok |
| 22 | coupling check, free 48x4 | `0.5608` | `coupling_check.json fem.plane_stress.free_48x4` | `0.56079` | ok |
| 23 | coupling check, 2-D vs 3-D gap | `2.8` | `coupling_check.json rel_gap_2d_vs_3d x100` | `2.8` | ok |
| 24 | mode tracking, worst MAC | `0.999` | `mode_tracking.json rows min mac` | `0.999` | ok |
| 25 | orientation, k2 at 0 deg, AR=2 | `0.4448` | `paper_figures_data.json polar[AR=2,th=0]` | `0.4448` | ok |
| 26 | orientation, k2 at 90 deg, AR=2 | `0.3786` | `paper_figures_data.json polar[AR=2,th=90]` | `0.3786` | ok |
| 27 | orientation, k2 at 0 deg, AR=10 | `0.4677` | `paper_figures_data.json polar[AR=10,th=0]` | `0.4677` | ok |
| 28 | orientation, k2 at 90 deg, AR=10 | `0.3801` | `paper_figures_data.json polar[AR=10,th=90]` | `0.3801` | ok |
| 29 | orientation, f1 at 90 deg, AR=10 | `158.1` | `paper_figures_data.json polar[AR=10,th=90].f1_kHz` | `158.1` | ok |
| 30 | application, k2 extensional plane stress | `0.4580` | `application_table.json rows[3].k2` | `0.4580` | ok |
| 31 | application, V0 extensional plane stress | `138.99` | `application_table.json rows[3].V0_V` | `138.99` | ok |
| 32 | application, k2 bending plane stress | `0.1141` | `application_table.json rows[1].k2` | `0.1141` | ok |
| 33 | application, V0 bending plane stress | `2.41` | `application_table.json rows[1].V0_V` | `2.41` | ok |
| 34 | application, f1 extensional plane stress | `147.73` | `application_table.json rows[3].f1_kHz` | `147.73` | ok |
| 35 | application, f mode extensional plane strain | `7161.0` | `application_table.json rows[2].f_kHz` | `7161.0` | ok |
| 36 | closed form, 3-D free bar | `0.5771` | `k2_closed_form.json k2_3d_free` | `0.5771` | ok |
| 37 | closed form, 3-D uniaxial | `0.3748` | `k2_closed_form.json k2_3d_uniaxial` | `0.3748` | ok |
| 38 | closed form, 2-D plane strain | `0.5132` | `k2_closed_form.json k2_2d_plane_strain` | `0.5132` | ok |
| 39 | closed form, x_2D | `1.2768` | `k2_closed_form.json x_2d` | `1.2768` | ok |
| 40 | closed form, C_p[0][0] | `9.5500` | `k2_closed_form.json C_p[0][0] / 1e10` | `9.5500` | ok |
| 41 | closed form, e'C^-1 e | `6.3308e-10` | `k2_closed_form.json eC` | `6.3308e-10` | ok |
| 42 | independent, clamped-free EB | `143.8` | `independent F1 clamped-free f_EB_kHz` | `143.8` | ok |
| 43 | independent, clamped-free FEM 48x4 | `144.6` | `independent F1 clamped-free mesh[0] f_FEM_kHz` | `144.6` | ok |
| 44 | independent, clamped-clamped EB | `915.0` | `independent F1 clamped-clamped f_EB_kHz` | `915.0` | ok |
| 45 | independent, clamped-clamped FEM 48x4 | `919.2` | `independent F1 clamped-clamped mesh[0] f_FEM_kHz` | `919.2` | ok |
| 46 | independent, clamped-free FEM 128x4 | `144.08` | `independent F1 clamped-free mesh[2] f_FEM_kHz` | `144.08` | ok |
| 47 | independent, beam modulus | `7.63` | `independent F1 E_beam / 1e10` | `7.63` | ok |
| 48 | independent, zeta maximum in alpha | `0.179` | `independent F2 zeta at alpha=0.7, omega*tau=0.3` | `0.179` | ok |
| 49 | independent, zeta at alpha=0.3 | `0.108` | `independent F2 zeta at alpha=0.3, omega*tau=0.3` | `0.108` | ok |
| 50 | sensitivity, spread at h=1 um, per cent, upper bound | `0.5\%` | `sensitivity.json spread_h1_pct (range/midpoint)` | `<= 0.5` | ok |
| 51 | sensitivity, spread at h=10 um, per cent, upper bound | `10^{-4}\%` | `sensitivity.json spread_h10_pct (range/midpoint)` | `<= 0.0001` | ok |
| 52 | ring-down, decrement at alpha=1 | `0.063` | `paper_figures_data.json notes.P6 zeta_1.0` | `0.063` | ok |
| 53 | ring-down, peak decrement at alpha=0.6 | `0.104` | `paper_figures_data.json notes.P6 zeta_0.6` | `0.104` | ok |
| 54 | ring-down, decrement at alpha=0.4 | `0.085` | `paper_figures_data.json notes.P6 zeta_0.4` | `0.085` | ok |
| 55 | ring-down, error at alpha=0.6 against alpha=1 | `64` | `paper_figures_data.json notes.P6 zeta_0.6/zeta_1.0 - 1, in percent` | `64` | ok |
| 56 | config table, flexo only at h=10 | `1.76e-4` | `config_table rows[0] k2_flexo` | `1.76e-4` | ok |
| 57 | config table, flexo only at h=1 | `5.5e-3` | `config_table rows[3] k2_flexo` | `5.5e-3` | ok |
| 58 | config table, growth with e=0 | `31` | `config_table growth_flexo_only` | `31` | ok |
| 59 | config table, piezo shift at h=1, per cent | `24` | `config_table min flexo_shift x100` | `24` | ok |
| 60 | axes, C_xx poled y | `1.6946` | `independent F5 poling y C_xx / 1e11` | `1.6946` | ok |
| 61 | axes, E_b poled y | `1.3544` | `independent F5 E_beam_pol_y / 1e11` | `1.3544` | ok |
| 62 | axes, kappa11/kappa33 | `39` | `independent F5 kappa_ratio_11_over_33` | `39` | ok |
| 63 | pairing, the hybrid x | `6.34` | `independent F5 x_hybrid x1e4` | `6.34` | ok |
| 64 | pairing, distance from the FEM value | `77` | `independent F5 hybrid_vs_fem_rel x100` | `77` | ok |
| 65 | independent, flexo x, uniform curvature | `3.570415` | `independent F3 x_analytic x1e4` | `3.570415` | ok |
| 66 | closed form, 3-D free bar | `0.5771` | `k2_closed_form.json k2_3d_free` | `0.5771` | ok |
| 67 | closed form, 3-D uniaxial | `0.3748` | `k2_closed_form.json k2_3d_uniaxial` | `0.3748` | ok |
| 68 | closed form, FEM clamped 48x4 | `0.55957` | `k2_closed_form.json fem.FEM clamped 48x4` | `0.55957` | ok |
| 69 | modulus ratio, w=1, alpha=1 | `1.35` | `memory_variants.json S2[3].ratio_KV_over_Zener` | `1.35` | ok |
| 70 | modulus ratio, w=1, alpha=0.7 | `1.62` | `memory_variants.json S2[9].ratio_KV_over_Zener` | `1.62` | ok |
| 71 | modulus ratio, w=100, alpha=1 | `91` | `memory_variants.json S2[5].ratio_KV_over_Zener` | `91` | ok |
| 72 | worked, window M11 | `3.000e-12` | `worked_example window M11` | `3.000e-12` | ok |
| 73 | worked, window M22 | `3.333e-13` | `worked_example window M22` | `3.333e-13` | ok |
| 74 | worked, equal-M ellipsoid over cuboid | `1.2910` | `worked_example sqrt(5/3)` | `1.2910` | ok |
| 75 | worked, equal-M cuboid over ellipsoid | `0.7746` | `worked_example sqrt(3/5)` | `0.7746` | ok |
| 76 | worked, plane-stress C11 poling x | `9.5500e10` | `materials C_p[0,0] poling x` | `9.5500e+10` | ok |
| 77 | worked, plane-stress C11 poling y | `1.6946e11` | `materials C_p[0,0] poling y` | `1.6946e+11` | ok |
| 78 | worked, plane-stress C12 | `5.7000e10` | `materials C_p[0,1]` | `5.7000e+10` | ok |
| 79 | worked, kappa33 | `4.9583e-10` | `k2_closed_form kappa_eff` | `4.9583e-10` | ok |
| 80 | worked, condensed capacitance beta | `2.4792e-11` | `worked_example beta` | `2.4792e-11` | ok |
| 81 | worked, x from the assembled matrices | `1.2631` | `worked_example x_fem` | `1.2631` | ok |
| 82 | worked, distance to the closed form | `0.47` | `worked_example diff_percent` | `0.47` | ok |
| 83 | worked, flexoelectric x at h=10 | `3.5704e-4` | `worked_example x_analytic_h10` | `3.5704e-4` | ok |
| 84 | worked, peak ratio of the ring-down | `2.5947` | `exp(delta) from memory_variants.json` | `2.5947` | ok |
| 85 | worked, logarithmic decrement | `0.95345` | `ln(peak ratio)` | `0.95345` | ok |
| 86 | worked, L1 weight b1 at alpha=0.5 | `0.414214` | `sqrt(2)-1` | `0.414214` | ok |
| 87 | worked, L1 weight b2 at alpha=0.7 | `0.159245` | `3^0.3-2^0.3` | `0.159245` | ok |
| 88 | design map, flexo k^2 at h=10, a2=0.25 | `1.648e-4` | `design_map.json [h=10][a2=0.25]` | `1.6483e-4` | ok |
| 89 | design map, change of k^2 at h=10 for a2 1 -> 0.25 um | `5.5` | `design_map.json 100*(1-k(a2=.25)/k(a2=1)) at h=10` | `5.5` | ok |
| 90 | design map, flexo k^2 at h=1, a2=0.25 | `1.03e-2` | `design_map.json [h=1][a2=0.25]` | `1.03e-2` | ok |
| 91 | design map, gain from the window at h=1 | `2.5` | `design_map.json k(a2=.25)/k(a2=1) at h=1` | `2.5` | ok |
| 92 | design map, flexo k^2 at h=1, a2=1 um | `4.17e-3` | `design_map.json [h=1][a2=1]` | `4.17e-3` | ok |
| 93 | design map, smallest flexo k^2 | `3.69e-6` | `design_map.json range k2_flexo_min` | `3.69e-6` | ok |
| 94 | design map, smallest flexo/piezo ratio | `6.6e-6` | `design_map.json range ratio_min` | `6.6e-6` | ok |
| 95 | design map, largest flexo/piezo ratio | `1.85e-2` | `design_map.json range ratio_max` | `1.85e-2` | ok |
| 96 | design map, thickness of the 0.1 % crossing at a2=1 um | `5.46` | `design_map.json thresholds h_at_0p1pct_a2_1um` | `5.46` | ok |

## Forbidden stale tokens

0 hits of 12 forbidden tokens.


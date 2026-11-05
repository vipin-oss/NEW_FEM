# Every number in the manuscript against the JSON it came from

32/32 claims agree; 0 disagree with the JSON, 0 are not found in the text.

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
| 32 | criteria count | `forty-one` | `summary.json n_total = 41` | `forty-one` | ok |

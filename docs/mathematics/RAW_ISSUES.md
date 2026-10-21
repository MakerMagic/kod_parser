# Mathematics RAW Issues

Generated from `data/raw/mathematics/*.raw.json`; this file contains RAW-stage findings only.

Total raw issues: **20** across **9** questions.

| Raw issue category | Findings | Questions |
|---|---:|---:|
| `option_boundary` | 2 | 2 |
| `raster_math_unverified` | 6 | 1 |
| `uncertain_formula` | 12 | 6 |

## Per-question findings

- **math_1.pdf — Q5** (`matdev_v1.1_9e6cc3f6b418fa0db4a7_q005`) — page 2 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q005_p002_formula_fallback_body_c2f0da736d13ef7d`.
- **math_11.pdf — Q10** (`matdev_v11.1_b246fe094d784eb70752_q010`) — page 4 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q010_p004_formula_fallback_body_33346b574109ee94`.
- **math_12.pdf — Q13** (`matdev_v12.1_6c8a6ddff0414bd51a85_q013`) — page 4 — `uncertain_formula`
  Reason: Radicand delimiter boundary is not fully supported by vinculum geometry; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q013_p004_formula_fallback_body_503cb001906a0828`.
- **math_2.pdf — Q7** (`matdev_v2.1_83f1de0e7bcdd8dbea9f_q007`) — page 3 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **math_2.pdf — Q26** (`matdev_v2.1_83f1de0e7bcdd8dbea9f_q026`) — page 7 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `option` `A`; diagnostic: method `native_glyph_geometry`, asset `q026_p007_formula_fallback_A_800b631d2585ec8e`.
- **math_2.pdf — Q26** (`matdev_v2.1_83f1de0e7bcdd8dbea9f_q026`) — page 7 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `option` `B`; diagnostic: method `native_glyph_geometry`, asset `q026_p007_formula_fallback_B_4097908ada9a93fd`.
- **math_2.pdf — Q26** (`matdev_v2.1_83f1de0e7bcdd8dbea9f_q026`) — page 7 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `option` `D`; diagnostic: method `native_glyph_geometry`, asset `q026_p007_formula_fallback_D_9086f76ba84c03d5`.
- **math_2.pdf — Q26** (`matdev_v2.1_83f1de0e7bcdd8dbea9f_q026`) — page 7 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `option` `E`; diagnostic: method `native_glyph_geometry`, asset `q026_p007_formula_fallback_E_381c6ca27a88ab2f`.
- **math_3.pdf — Q27** (`matdev_v3.1_5ff09cf01df7cf5bc0f8_q027`) — page 7 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **math_4.pdf — Q12** (`matdev_v4.1_d9d3b5564d35e43d7192_q012`) — page 4 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `option` `B`; diagnostic: method `native_glyph_geometry`, asset `q012_p004_formula_fallback_B_dbf4f97b06e8b8d2`.
- **math_4.pdf — Q12** (`matdev_v4.1_d9d3b5564d35e43d7192_q012`) — page 4 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `option` `C`; diagnostic: method `native_glyph_geometry`, asset `q012_p004_formula_fallback_C_264c831b6b65eea8`.
- **math_4.pdf — Q12** (`matdev_v4.1_d9d3b5564d35e43d7192_q012`) — page 4 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `option` `D`; diagnostic: method `native_glyph_geometry`, asset `q012_p004_formula_fallback_D_92e4137ad89ada22`.
- **math_4.pdf — Q12** (`matdev_v4.1_d9d3b5564d35e43d7192_q012`) — page 4 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `option` `E`; diagnostic: method `native_glyph_geometry`, asset `q012_p004_formula_fallback_E_bcfa25c2b3cfddc6`.
- **math_5.pdf — Q16** (`matdev_v5.1_46af027e8d6aa5fbb18f_q016`) — page 5 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q016_p005_formula_fallback_body_8e5abe4ff98c3758`.
- **math_6.pdf — Q27** (`matdev_v6.1_17589c9d9de3f79684bf_q027`) — page 8 — `raster_math_unverified`
  Reason: Compact visual in an explicit formula/expression task remains source imagery; mathematical OCR transcription is not verified; affected field: `option` `A`; diagnostic: method `source_visual_preservation`, asset `q027_p008_option_A_4a4e3871cceedf67`.
- **math_6.pdf — Q27** (`matdev_v6.1_17589c9d9de3f79684bf_q027`) — page 8 — `raster_math_unverified`
  Reason: Compact visual in an explicit formula/expression task remains source imagery; mathematical OCR transcription is not verified; affected field: `option` `B`; diagnostic: method `source_visual_preservation`, asset `q027_p008_option_B_ad64b60c749b7515`.
- **math_6.pdf — Q27** (`matdev_v6.1_17589c9d9de3f79684bf_q027`) — page 8 — `raster_math_unverified`
  Reason: Compact visual in an explicit formula/expression task remains source imagery; mathematical OCR transcription is not verified; affected field: `option` `C`; diagnostic: method `source_visual_preservation`, asset `q027_p008_option_C_89999ee4ae24f3e9`.
- **math_6.pdf — Q27** (`matdev_v6.1_17589c9d9de3f79684bf_q027`) — page 8 — `raster_math_unverified`
  Reason: Compact visual in an explicit formula/expression task remains source imagery; mathematical OCR transcription is not verified; affected field: `option` `D`; diagnostic: method `source_visual_preservation`, asset `q027_p008_option_D_a31315bcd780a9fb`.
- **math_6.pdf — Q27** (`matdev_v6.1_17589c9d9de3f79684bf_q027`) — page 8 — `raster_math_unverified`
  Reason: Compact visual in an explicit formula/expression task remains source imagery; mathematical OCR transcription is not verified; affected field: `option` `E`; diagnostic: method `source_visual_preservation`, asset `q027_p008_option_E_16c92997ab6b5b6f`.
- **math_6.pdf — Q27** (`matdev_v6.1_17589c9d9de3f79684bf_q027`) — page 8 — `raster_math_unverified`
  Reason: Compact visual in an explicit formula/expression task remains source imagery; mathematical OCR transcription is not verified; affected field: `question`; diagnostic: method `source_visual_preservation`, asset `q027_p008_body_body_b1eff4c2ad6429e5`.

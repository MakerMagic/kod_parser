# Mathematics RAW Issues

Generated from `data/raw/mathematics/*.raw.json`; this file contains RAW-stage findings only.

Total raw issues: **91** across **43** questions.

| Raw issue category | Findings | Questions |
|---|---:|---:|
| `answer_key_structure` | 6 | 6 |
| `ocr_question_number` | 3 | 3 |
| `option_boundary` | 32 | 32 |
| `raster_math_unverified` | 34 | 28 |
| `uncertain_formula` | 15 | 9 |
| `unmapped_glyph` | 1 | 1 |

## Per-question findings

- **Test_1.pdf — Q14** (`sky_trial_v1_ff5b79152aaa929e40fc_q014`) — page 5 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_3.pdf — Q10** (`sky_trial_v3_4807a29b9e04499e5859_q010`) — page 4 — `unmapped_glyph`
  Reason: Native prose contains an unmapped source glyph; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q010_p004_formula_fallback_body_eddb4451920e5212`.
- **Test_3.pdf — Q17** (`sky_trial_v3_4807a29b9e04499e5859_q017`) — page 6 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_4.pdf — Q23** (`sky_trial_v4_bc012afd538ad180abd3_q023`) — page 8 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_4.pdf — Q30** (`sky_trial_v4_bc012afd538ad180abd3_q030`) — page 10 — `uncertain_formula`
  Reason: Native integral limits and integrand require unsupported multi-baseline grouping; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q030_p010_formula_fallback_body_3c791820332f5fe8`.
- **Test_7.pdf — Q10** (`sky_trial_v7_f24d912481931ad90d8d_q010`) — page 4 — `ocr_question_number`
  Reason: Question number is observed in raster OCR; source number requires review; affected field: `question_number`; diagnostic: method `local_raster_label_recognition`, asset `q012_p004_number_anchor_body_d9fdfc9026ce9926`.
- **Test_7.pdf — Q10** (`sky_trial_v7_f24d912481931ad90d8d_q010`) — page 4 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_7.pdf — Q10** (`sky_trial_v7_f24d912481931ad90d8d_q010`) — page 4 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q010_p004_body_body_0a02545ad4a4d73b`.
- **Test_7.pdf — Q10** (`sky_trial_v7_f24d912481931ad90d8d_q010`) — page 4 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q010_p004_body_body_95b9f12c98a80057`.
- **Test_7.pdf — Q15** (`sky_trial_v7_f24d912481931ad90d8d_q015`) — page 5 — `ocr_question_number`
  Reason: Question number is observed in raster OCR; source number requires review; affected field: `question_number`; diagnostic: method `local_raster_label_recognition`, asset `q016_p005_number_anchor_body_119a46049e980a65`.
- **Test_7.pdf — Q15** (`sky_trial_v7_f24d912481931ad90d8d_q015`) — page 5 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_7.pdf — Q15** (`sky_trial_v7_f24d912481931ad90d8d_q015`) — page 5 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q015_p005_body_body_8cb818f3e89b7096`.
- **Test_7.pdf — Q19** (`sky_trial_v7_f24d912481931ad90d8d_q019`) — page 6 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q019_p006_formula_fallback_body_2bb43fbf090a79f1`.
- **Test_7.pdf — Q22** (`sky_trial_v7_f24d912481931ad90d8d_q022`) — page 7 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q022_p007_formula_fallback_body_5b923d2223a02255`.
- **Test_8.pdf — Q1** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q001`) — page 12 — `answer_key_structure`
  Reason: Answer-key row has no unambiguous native answer label; affected field: `answer_key`.
- **Test_8.pdf — Q1** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q001`) — page 2 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q1** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q001`) — page 2 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q001_p002_body_body_4bf3141184ea7afc`.
- **Test_8.pdf — Q2** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q002`) — page 2 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q2** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q002`) — page 2 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q002_p002_body_body_6857acdab6ce14a0`.
- **Test_8.pdf — Q3** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q003`) — page 2 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q3** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q003`) — page 2 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q003_p002_body_body_ab34aa1f9770d1be`.
- **Test_8.pdf — Q4** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q004`) — page 3 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q4** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q004`) — page 3 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q004_p003_body_body_620fcd7b5642b5fd`.
- **Test_8.pdf — Q5** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q005`) — page 3 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q5** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q005`) — page 3 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q005_p003_body_body_f73db31578b2cd7c`.
- **Test_8.pdf — Q6** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q006`) — page 3 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q6** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q006`) — page 3 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q006_p003_body_body_e02f7d33f34e8e6c`.
- **Test_8.pdf — Q7** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q007`) — page 3 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q7** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q007`) — page 3 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q007_p003_body_body_072fee7ebea91ed0`.
- **Test_8.pdf — Q8** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q008`) — page 12 — `answer_key_structure`
  Reason: Answer-key row has no unambiguous native answer label; affected field: `answer_key`.
- **Test_8.pdf — Q8** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q008`) — page 4 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q8** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q008`) — page 4 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q008_p004_body_body_26b5314e3c8da76b`.
- **Test_8.pdf — Q9** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q009`) — page 12 — `answer_key_structure`
  Reason: Answer-key row has no unambiguous native answer label; affected field: `answer_key`.
- **Test_8.pdf — Q9** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q009`) — page 4 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q9** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q009`) — page 4 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q009_p004_body_body_ad01ba2aa5614b71`.
- **Test_8.pdf — Q10** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q010`) — page 4 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q10** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q010`) — page 4 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q010_p004_body_body_aac37c0c61f20394`.
- **Test_8.pdf — Q11** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q011`) — page 5 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q11** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q011`) — page 5 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q011_p005_body_body_5c092a473fd7d08d`.
- **Test_8.pdf — Q12** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q012`) — page 5 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q12** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q012`) — page 5 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q012_p005_body_body_c2053fac51347a36`.
- **Test_8.pdf — Q13** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q013`) — page 5 — `ocr_question_number`
  Reason: Question number is observed in raster OCR; source number requires review; affected field: `question_number`; diagnostic: method `local_raster_label_recognition`, asset `q012_p005_number_anchor_body_b89f6c69755f6b08`.
- **Test_8.pdf — Q13** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q013`) — page 5 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q13** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q013`) — page 5 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q013_p005_body_body_19a563a993458a52`.
- **Test_8.pdf — Q14** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q014`) — page 6 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q14** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q014`) — page 6 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q014_p006_body_body_e0326e6ffa5c8493`.
- **Test_8.pdf — Q15** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q015`) — page 6 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q15** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q015`) — page 6 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q015_p006_body_body_b254e5283b5a7a5b`.
- **Test_8.pdf — Q16** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q016`) — page 12 — `answer_key_structure`
  Reason: Answer-key row has no unambiguous native answer label; affected field: `answer_key`.
- **Test_8.pdf — Q16** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q016`) — page 6 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q16** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q016`) — page 6 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q016_p006_body_body_18564742ba175849`.
- **Test_8.pdf — Q17** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q017`) — page 12 — `answer_key_structure`
  Reason: Answer-key row has no unambiguous native answer label; affected field: `answer_key`.
- **Test_8.pdf — Q17** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q017`) — page 7 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q17** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q017`) — page 7 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q017_p007_body_body_50dc38be2fbcc419`.
- **Test_8.pdf — Q18** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q018`) — page 7 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q18** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q018`) — page 7 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q018_p007_body_body_d5eae148af1fd175`.
- **Test_8.pdf — Q19** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q019`) — page 12 — `answer_key_structure`
  Reason: Answer-key row has no unambiguous native answer label; affected field: `answer_key`.
- **Test_8.pdf — Q19** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q019`) — page 7 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q19** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q019`) — page 7 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q019_p007_body_body_51a16c3c147fa98f`.
- **Test_8.pdf — Q20** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q020`) — page 8 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q20** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q020`) — page 8 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q020_p008_body_body_846864efdf9ab298`.
- **Test_8.pdf — Q22** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q022`) — page 8 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q22** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q022`) — page 8 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q022_p008_body_body_c6887a83bc658d75`.
- **Test_8.pdf — Q23** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q023`) — page 9 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q23** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q023`) — page 9 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q023_p009_body_body_d980a42879f4cce0`.
- **Test_8.pdf — Q24** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q024`) — page 9 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q24** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q024`) — page 9 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q024_p009_body_body_a96bbaa0b7bd129d`.
- **Test_8.pdf — Q25** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q025`) — page 10 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q25** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q025`) — page 10 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q025_p010_body_body_fb1fa7cbc22397fb`.
- **Test_8.pdf — Q26** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q026`) — page 10 — `option_boundary`
  Reason: No reliable contiguous source option anchors; affected field: `options`.
- **Test_8.pdf — Q26** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q026`) — page 10 — `raster_math_unverified`
  Reason: Raster question text/formulas have no native glyph layer; mathematical transcription is not verified; affected field: `question`; diagnostic: method `source_raster_text_preservation`, asset `q026_p010_body_body_34b2eb698db95726`.
- **Test_8.pdf — Q30** (`sky_trial_v8_fdfdc1303f5ec04d7a97_q030`) — page 11 — `uncertain_formula`
  Reason: Unexplained multiple baselines / possible system or matrix; affected field: `question`; diagnostic: method `native_glyph_geometry`, asset `q030_p011_formula_fallback_body_e155683a9e31058f`.
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

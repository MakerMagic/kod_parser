"""Source-key matching tests for the second mathematics set."""

import json

from processors.matching.mathematics import supplied

ANSWER_FILE = (
    supplied.ROOT / "acquisition/local/mathematics/sky (trial)/Answers 1-8.txt"
)


def test_authoritative_file_has_exact_source_question_coverage():
    answers = supplied.parse_answer_file(ANSWER_FILE)
    assert set(answers) == set(range(1, 9))
    assert all(set(rows) == set(range(1, 31)) for rows in answers.values())
    assert answers[1][1] == "C"
    assert answers[8][30] == "E"


def test_key_records_are_bound_to_test_source_and_question():
    merged = {
        "sources": {
            f"source-{number}": {"filename": f"Test_{number}.pdf"}
            for number in range(1, 9)
        }
    }
    key = supplied.build_answer_key(ANSWER_FILE, merged)
    assert len(key["entries"]) == 240
    assert key["entries"][0] == {
        "source_document_id": "source-1",
        "source_pdf": "Test_1.pdf",
        "test_number": 1,
        "question_number": 1,
        "correct_answer": "C",
    }
    assert key["entries"][-1]["correct_answer"] == "E"
    assert key["source_file"]["path"].endswith("Answers 1-8.txt")


def test_matching_validates_options_and_retains_unmatched_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(supplied, "ROOT", tmp_path)
    key_path = tmp_path / "answer_key.json"
    key_data = {
        "authority": "Answers 1-8",
        "source_file": {"path": "Answers 1-8.txt", "sha256": "source-hash"},
        "entries": [
            {
                "source_document_id": "source-1",
                "source_pdf": "Test_1.pdf",
                "test_number": 1,
                "question_number": 1,
                "correct_answer": "C",
            },
            {
                "source_document_id": "source-1",
                "source_pdf": "Test_1.pdf",
                "test_number": 1,
                "question_number": 2,
                "correct_answer": "A",
            },
        ],
    }
    key_path.write_text(json.dumps(key_data), encoding="utf8")
    q1 = {
        "id": "source-1_q001",
        "source_document_id": "source-1",
        "question_number": 1,
        "options": [
            {"label": label, "content": [{"type": "text", "text": label}]}
            for label in "ABCDE"
        ],
        "correct_answer": None,
        "matching": {"status": "unmatched", "issues": []},
        "issues": [],
    }
    q2 = {
        "id": "source-1_q002",
        "source_document_id": "source-1",
        "question_number": 2,
        "options": [],
        "correct_answer": None,
        "matching": {"status": "unmatched", "issues": []},
        "issues": [],
    }
    merged = {
        "sources": {"source-1": {"filename": "Test_1.pdf"}},
        "questions": [q1, q2],
        "summary": {},
    }

    updated, validation = supplied.update_matching(merged, key_data, key_path)
    assert updated["questions"][0]["correct_answer"] == "C"
    assert updated["questions"][0]["matching"]["status"] == "matched"
    assert (
        updated["questions"][0]["matching"]["key_reference"]["json_pointer"]
        == "/entries/0"
    )
    assert updated["questions"][1]["correct_answer"] is None
    assert updated["questions"][1]["matching"]["candidate_answer"] == "A"
    assert (
        "no complete extracted answer-option set"
        in updated["questions"][1]["matching"]["issues"][0]["reason"]
    )
    assert validation["summary"]["matched"] == 1
    assert validation["summary"]["unmatched"] == 1
    assert validation["issues"][0]["id"] == "source-1_q002"
    assert supplied.render_artifacts(updated, validation)[1].startswith(
        "# Mathematics second-set MATCHING issues"
    )


def test_existing_matching_answer_is_preserved_when_it_agrees(tmp_path, monkeypatch):
    monkeypatch.setattr(supplied, "ROOT", tmp_path)
    key_path = tmp_path / "answer_key.json"
    key_data = {
        "authority": "Answers 1-8",
        "source_file": {"path": "key.txt", "sha256": "source-hash"},
        "entries": [
            {
                "source_document_id": "source-8",
                "source_pdf": "Test_8.pdf",
                "test_number": 8,
                "question_number": 30,
                "correct_answer": "E",
            }
        ],
    }
    key_path.write_text(json.dumps(key_data), encoding="utf8")
    row = {
        "id": "source-8_q030",
        "source_document_id": "source-8",
        "question_number": 30,
        "options": [
            {"label": label, "content": [{"type": "text", "text": label}]}
            for label in "ABCDE"
        ],
        "correct_answer": "E",
        "matching": {"status": "matched", "key_reference": {"old": True}, "issues": []},
        "issues": [],
    }
    merged = {
        "sources": {"source-8": {"filename": "Test_8.pdf"}},
        "questions": [row],
        "summary": {},
    }

    updated, report = supplied.update_matching(merged, key_data, key_path)
    assert updated["questions"][0]["correct_answer"] == "E"
    assert report["summary"]["preserved_existing_matches"] == 1
    assert report["summary"]["newly_matched"] == 0


def test_generated_second_set_matches_current_raw_and_key():
    merged_path = supplied.ROOT / "data/merged/mathematics/questions.json"
    validation_path = (
        supplied.ROOT / "data/merged/mathematics/second_set_validation.json"
    )
    key_path = supplied.ROOT / "data/merged/mathematics/second_set_answer_key.json"
    merged = supplied.load(merged_path)
    validation = supplied.load(validation_path)
    key = supplied.load(key_path)
    raw_paths = sorted((supplied.ROOT / "data/raw/mathematics").glob("Test_*.raw.json"))
    assert supplied.validate_update(merged, validation, key, key_path, raw_paths)
    assert validation["summary"]["questions"] == 240
    assert validation["summary"]["matched"] == 210
    assert validation["summary"]["unmatched"] == 30

from parsers.bmat.occupancy import measure


def sample(end, start=50):
    return {
        "raw": {"page_spans": [{"page": 1}]},
        "options": [{"label": x} for x in "ABCDE"],
        "layout_blocks": [
            {
                "type": "text",
                "component": "question_body",
                "bbox": [50, start, 500, start + 10],
            },
            {
                "type": "text",
                "component": "option",
                "label": "E",
                "text": "E Last answer",
                "bbox": [70, end - 10, 400, end],
            },
            {
                "type": "text",
                "component": "question_body",
                "text": "END OF SECTION",
                "bbox": [50, 740, 500, 755],
            },
            {
                "type": "text",
                "component": "footer",
                "text": "Page 7",
                "bbox": [50, 780, 500, 795],
            },
        ],
    }


def test_sixty_percent_inclusive_and_final_answer_boundary():
    pages = [{"height": 800}]
    for end, expected in [(482, False), (482.001, True), (230, False), (690, True)]:
        result = measure(sample(end), pages)
        assert result["exceeds_threshold"] == expected
        assert result["final_option_bottom"] == end
        assert result["usable_page_height"] == 720


def test_mid_page_start_and_cross_page_are_explicit():
    assert not measure(sample(700, 400), [{"height": 800}])["exceeds_threshold"]
    q = sample(700)
    q["raw"]["page_spans"].append({"page": 2})
    assert measure(q, [{"height": 800}])["status"] == "not_applicable"


def test_visual_answer_extends_to_image_bottom_not_label():
    q = sample(230)
    q["options"][-1]["images"] = [
        {"page": 1, "belongs_to": "option", "bbox": [70, 230, 400, 690]}
    ]
    assert measure(q, [{"height": 800}])["final_option_bottom"] == 690


def test_ambiguous_options_are_not_a_confident_skip():
    q = sample(700)
    q["options"][-1]["label"] = "D"
    assert measure(q, [{"height": 800}])["status"] == "unresolved"

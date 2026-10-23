"""CLEAN prose formatting must leave mathematical and semantic structure intact."""

from copy import deepcopy

import pytest

from processors.normalization.mathematics.structure import reflow, split, token_ledger
from processors.normalization.mathematics.text_quality import polish, sync_prose


def text(value):
    return {'type': 'text', 'text': value}


@pytest.mark.parametrize('prompt_text', ['what is the value?', 'find the area.', 'in which case is this true?'])
def test_lowercase_prose_request_capitalized(prompt_text):
    body, prompt, edits = polish([text('Given the diagram, ')], [text(prompt_text)])
    assert prompt[0]['text'] == prompt_text[0].upper() + prompt_text[1:]
    assert body[0]['text'] == 'Given the diagram. '
    assert edits == ['capitalization', 'trailing_comma']


@pytest.mark.parametrize('block', [text('x + y = 3'), text('sin x = 1'), text('ln x = 2'), text('(a,b)'), {'type': 'math', 'latex': r'\sqrt{x}', 'display': False}])
def test_mathematical_starts_are_exact(block):
    assert polish([], [block])[1] == [block]


def test_internal_commas_math_lists_and_paragraphs_preserved():
    bs = [text('The points A, B and C are given, '), {'type':'math', 'latex':'(x,y)', 'display':False}, text(' respectively, ')]
    before = deepcopy(bs)
    body, _, _ = polish(bs, None)
    assert body[0] == before[0] and body[1] == before[1]
    assert body[2]['text'] == ' respectively. '
    assert bs == before
    assert reflow([text('First paragraph.\n\nSecond paragraph.\nI. Claim one.\nII. Claim two.')])[0]['text'] == 'First paragraph.\n\nSecond paragraph.\nI. Claim one.\nII. Claim two.'


def test_reflow_short_options_and_formula_variable_continuation():
    for value, expected in [('Infinitely \nmany', 'Infinitely many'), ('It will not\nchange', 'It will not change'), ('The least of them is\nx?', 'The least of them is x?'), ('any of the following\nEXCEPT', 'any of the following EXCEPT')]:
        assert reflow([text(value)])[0]['text'] == expected
    blocks = [text('Given these equations:'), {'type':'math','latex':'x+y=3','display':True,'break_before':True}, {'type':'math','latex':'x-y=1','display':True,'break_before':True}]
    assert reflow(blocks) == blocks
    assert reflow([text('x\ny')])[0]['text'] == 'x\ny'


def test_projection_changes_sync_to_full_content_without_loss():
    original = [text('Given this shape, what is its area?')]
    body, prompt, _ = split(original)
    body, prompt, _ = polish(body, prompt)
    updated = sync_prose(original, body, prompt)
    assert updated == [text('Given this shape. What is its area?')]
    assert token_ledger(updated) == token_ledger(body + prompt)
    assert original == [text('Given this shape, what is its area?')]
    assert polish(body, prompt)[:2] == (body, prompt)
    with pytest.raises(ValueError):
        sync_prose(original, body, [text('Another request?')])


def test_reviewed_category_rebinding_only_permits_verified_prose_edits():
    from categorization.core import digest
    from categorization.mathematics.bindings import rebind_structure
    from categorization.mathematics.core import semantic_content
    old = {'id':'example','assets':[], 'content':[text('Given the circle, what is its area?')], 'options':[]}
    old['main_body'],old['main_question'],_=split(old['content'])
    new=deepcopy(old)
    new['main_body'],new['main_question'],_=polish(old['main_body'],old['main_question'])
    new['content']=sync_prose(old['content'],new['main_body'],new['main_question'])
    key=digest(semantic_content(old))
    decision={'status':'needs_review','issue_code':'boundary','reason':'Preserve prior assessment'}
    reviews={'assessments':{key:decision}}
    cat={'questions':[{'id':'example','content_sha256':key,'assessment':decision}]}
    migrated=rebind_structure(reviews,{'questions':[old]},{'questions':[new]},cat)
    assert migrated['assessments'][digest(semantic_content(new))]==decision
    bad=deepcopy(new)
    bad['content'][0]['text']=bad['content'][0]['text'].replace('area','radius')
    with pytest.raises(ValueError,match='meaning'):
        rebind_structure(reviews,{'questions':[old]},{'questions':[bad]},cat)


def test_saved_clean_prose_invariants_and_math_start_safety():
    import json
    import re
    from pathlib import Path
    from parsers.mathematics.structure import walk
    from processors.normalization.mathematics.text_quality import PROSE_START
    data=json.loads(Path('data/clean/mathematics/questions.json').read_text(encoding='utf8'))
    for q in data['questions']:
        prompt=q['main_question'] or []
        if prompt and prompt[0]['type']=='text':
            start=prompt[0]['text'].lstrip()
            if PROSE_START.match(start):
                assert start[0].isupper(),q['id']
        for blocks in [q['main_body'],prompt,*[o['content'] for o in q['options']]]:
            if blocks and blocks[-1]['type']=='text':
                assert not blocks[-1]['text'].rstrip().endswith(','),q['id']
        # The retained stream and field projections have exactly the same
        # non-whitespace text/math structure, even after prose edits.
        from processors.normalization.mathematics.structure import projection_is_lossless
        assert projection_is_lossless(q['content'],q['main_body'],q['main_question'])

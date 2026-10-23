"""Conservative prose edits at CLEAN component boundaries; mathematics is opaque."""

import re
from copy import deepcopy

# Complete prose words, never a one-letter variable or a function identifier.
PROSE_START = re.compile(
    r"^(?:what|which|how|where|when|why|find|calculate|determine|evaluate|"
    r"simplify|solve|express|rearrange|describe|write|expand|factorise|factorize|"
    r"by|in|for|at|if|given|using|the|a|an|let|suppose|show|prove|select|choose|"
    r"work|make|use)\b", re.IGNORECASE
)


def polish(body, question):
    """Capitalize a prose request and close prose components at their boundary.

    Inline text blocks ending in commas are untouched. Only the terminal block
    of an entire component can change; formula blocks are never edited.
    Every edit replaces one character so source characters remain accountable.
    """
    body, question = deepcopy(body), deepcopy(question)
    changes = []
    if question and question[0]['type'] == 'text':
        value = question[0]['text']
        match = re.match(r'\s*', value)
        pos = match.end()
        if PROSE_START.match(value[pos:]) and value[pos:pos+1].islower():
            question[0]['text'] = value[:pos] + value[pos].upper() + value[pos+1:]
            changes.append('capitalization')
    for name, blocks in (('main_body', body), ('main_question', question)):
        if not blocks or blocks[-1]['type'] != 'text':
            continue
        text = blocks[-1]['text']
        if not text.rstrip().endswith(','):
            continue
        # Require prose in the component or an isolated separator after opaque
        # mathematical content. A coordinate/formula text fragment is not prose.
        prose = any(b['type'] == 'text' and re.search(r'\b[A-Za-z]{2,}\b', b['text']) for b in blocks)
        separator = text.strip() == ',' and any(b['type'] == 'math' for b in blocks)
        if not (prose or separator):
            continue
        pos = len(text.rstrip()) - 1
        start = ''.join(b.get('text', '') for b in blocks).lstrip()
        ending = '?' if name == 'main_question' and re.match(r'(?i)(what|which|how|where|when|why)\b', start) else '.'
        blocks[-1]['text'] = text[:pos] + ending + text[pos+1:]
        changes.append('trailing_comma')
    return body, question, changes


def sync_prose(content, body, question):
    """Apply verified projection edits to the retained full content stream.

    Visual relocation does not affect text order. Math and list content is not
    editable here. Each changed character must be a case edit or comma closure.
    """
    result = deepcopy(content)
    def chars(blocks):
        return [(b, i, c) for b in blocks if b['type'] == 'text'
                for i, c in enumerate(b['text']) if not c.isspace()]
    before = chars(result)
    after = chars(body + (question or []))
    if len(before) != len(after):
        raise ValueError('Prose formatting lost or duplicated characters')
    replacements = {}
    for (b, pos, old), (_, _, new) in zip(before, after, strict=True):
        if old == new:
            continue
        if not (old.islower() and old.upper() == new or old == ',' and new in '.?'):
            raise ValueError('Unapproved prose formatting edit')
        replacements.setdefault(id(b), {})[pos] = new
    for b in result:
        if id(b) in replacements:
            b['text'] = ''.join(replacements[id(b)].get(i, c) for i, c in enumerate(b['text']))
    return result

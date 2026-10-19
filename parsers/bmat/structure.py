"""Source-order BMAT prompt boundaries, not text normalization."""

import re

INTERROGATIVE = re.compile(
    r"\b(?:which|what|how|why|when|where|who|whose)\b", re.IGNORECASE
)
COLON_TASK = re.compile(
    r"\b(?:claimed|concluded|inferred|follows|assum\w*|reflect\w*|illustrat\w*|best described|must be|would be|is that)\b",
    re.IGNORECASE,
)


def prompt_start(text):
    """Require request intent in the final sentence, including conditional leads."""
    conditional = list(
        re.finditer(
            r"(?:^|\n)((?:If|After|Before|Given|Assuming|According to|On the basis of|In the context of)\b[^?]+\?(?:\s*\([^)]*\))?[.]?\s*)(?=$|\n?\s*1[.)]?\s+)",
            text,
        )
    )
    if conditional and INTERROGATIVE.search(conditional[-1][1]):
        candidate = conditional[-1][1]
        before_question = candidate.split("?", 1)[0]
        if not re.search(r"(?<!\d)\.(?!\d)|!", before_question):
            return conditional[-1].start(1)
    sentences = list(
        re.finditer(r"(?:^|(?<=[.!?])\s+)([^.!?]+(?:\?(?:\s*\([^)]*\))?|[.!]|$))", text)
    )
    for match in reversed(sentences):
        value = match[1].strip()
        if "?" in value and INTERROGATIVE.search(value):
            # Reject a quoted question followed by a separate declarative passage.
            if not text[match.end() :].strip() or re.match(
                r"\s*1[.)]?\s+", text[match.end() :]
            ):
                return match.start(1)
            break
    # Explicit completion/ordering instruction followed by numbered propositions.
    listed = re.search(
        r"(?:^|\n)((?:If|Using)\b[^?]+:\s*\n(?:[^\n]*should:\s*\n)?\s*1\s+.*)$",
        text,
        re.DOTALL,
    )
    if listed and re.search(
        r"\bwhich\b.*\bcorrect:|\bplace\b.*\border:",
        listed[1],
        re.DOTALL | re.IGNORECASE,
    ):
        return listed.start(1)
    # Sentence-completion prompts must be the final clause, not a data lead-in.
    tail = re.search(r"(?:^|(?<=[.!?])\s+)([^.!?]+)\s*$", text)
    if tail:
        value = tail[1].strip()
        if (
            value.endswith(":")
            and COLON_TASK.search(value)
            and not re.search(
                r"\b(?:as follows|shown below|following (?:table|data|information|list))\b",
                value,
                re.IGNORECASE,
            )
        ):
            return tail.start(1)
        if re.match(r"(?:If|Given|Assuming|When)\b", value) and re.search(
            r",?\s+(?:then\s+)?(?:the\s+)?[^:?!]+\b(?:are|is|would be|must be|will be)\s*$",
            value,
        ):
            return tail.start(1)
    conditional_completion = re.search(
        r"(?:^|\n)((?:If|Given|Assuming)\b[^?]+\b(?:would be|will be|are|is):?\s*)$",
        text,
    )
    if conditional_completion:
        return conditional_completion.start(1)
    return None


def components(question):
    text = question["question_text"]
    start = prompt_start(text)
    if start is not None:
        from .parser import PROMPT

        offset = 0
        for line in text.splitlines(keepends=True):
            if (
                offset > start
                and line.strip()[:1].isupper()
                and PROMPT.match(line.strip())
            ):
                prefix = text[start:offset].rstrip()
                if not (
                    prefix.endswith(",")
                    and re.match(r"(?:If|After|Before|Given|Assuming)\b", prefix)
                ):
                    start = offset
            offset += len(line)
    if start is None:
        # Imperative instructions retain the established explicit-request path.
        from .parser import PROMPT

        offset, starts = 0, []
        for line in text.splitlines(keepends=True):
            if line.strip()[:1].isupper() and PROMPT.match(line.strip()):
                starts.append(offset)
            offset += len(line)
        start = max(starts) if starts else None
        # Preserve the established sentence-internal request path, including
        # period-ended instructions and prompts followed by numbered premises.
        candidates = []
        for match in re.finditer(
            r"(?:^|(?<=[.!?])\s+)((?:Which|What|How|Why|Who|Whose|On the basis of|In the context of)\b)",
            text,
        ):
            if re.search(
                r"\b(?:which|what|how|deduce|identify|conclude)\b",
                text[match.start(1) :],
                re.IGNORECASE,
            ):
                candidates.append(match.start(1))
        if candidates:
            start = max(candidates)
    no_passage = start is not None and not text[:start].strip()
    question["raw_components"] = {
        "main_body": "Equals question"
        if no_passage
        else text[:start]
        if start is not None
        else text,
        "main_question": text[start:] if start is not None else None,
        "body_equals_question": no_passage,
        "method": "source_final_request_or_answer_completion"
        if start is not None
        else "unresolved",
        "normalization_applied": False,
    }

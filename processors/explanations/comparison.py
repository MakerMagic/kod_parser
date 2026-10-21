"""Compare archived pilot snapshots without invoking any provider."""

from pathlib import Path

from processors.matching.storage import load_matched

from .generator import candidate_length, canonical_status, refresh_metrics


def write_comparison(runs, output):
    """Runs are (label, path) pairs. Counts distinguish local checks from review."""
    lines = [
        "<!-- explanation-pilot-comparison -->",
        "# Same-question explanation pilot comparison",
        "",
        "Local validation checks structure and obvious defects; reasoning review can reject a locally valid response. No full batch was run. Credentials are not included.",
        "",
    ]
    reference_selection = None
    for label, path in runs:
        data = load_matched(path)
        refresh_metrics(data)
        pilot = data["explanation_pilot"]
        metrics = pilot["metrics"]
        selection = pilot["selected_identities"]
        if reference_selection is not None and selection != reference_selection:
            raise ValueError("Comparison requires the same pilot identities and order")
        reference_selection = selection
        entries = pilot["audit"]
        local_count = sum(
            entry["metadata"].get("validation_status") == "accepted"
            and canonical_status(entry)
            in ("accepted", "validation_rejected", "reasoning_review_rejected")
            for entry in entries
        )
        accepted = sum(entry["status"] == "accepted" for entry in entries)
        lines += [
            f"## {label}",
            "",
            f"Generation availability: {metrics['received_output']}/{metrics['selected']} received output. Local validation: {local_count} accepted / {metrics['quality_evaluated'] - local_count} not accepted among completed quality decisions.",
            "",
            f"Explanation quality among returned outputs with completed decisions: {accepted}/{metrics['quality_evaluated']} accepted; provider failures excluded. Overall completed: {accepted}/{metrics['selected']}.",
            "",
            f"Prompt SHA-256: `{pilot['prompt_sha256']}`.",
            "",
            "| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for entry in entries:
            meta = entry["metadata"]
            first = meta.get(
                "first_attempt_validation_status",
                meta.get("validation_status", "unavailable"),
            )
            reasons = meta.get(
                "first_attempt_validation_errors", meta.get("validation_errors", [])
            )
            count = meta.get(
                "character_count", candidate_length(entry.get("candidate"))
            )
            backtest = entry.get("backtest_path")
            if not backtest:
                legacy = (
                    Path("inspections/critical_thinking_problem_solving/tsa/matching")
                    / f"gemini_pilot_{entry['identity']['year']}_q{entry['identity']['question_number']}.html"
                )
                backtest = str(legacy.resolve()) if legacy.exists() else None
            link = (
                f"[HTML](<{Path(backtest).as_posix()}>)"
                if backtest
                else "not linked in snapshot"
            )
            lines.append(
                f"| {entry['identity']['year']} Q{entry['identity']['question_number']} | {meta.get('model', 'unavailable')} | {first} | {', '.join(reasons) or 'none'} | {bool(meta.get('retry_attempted', False))} | {meta.get('retry_result', 'not_attempted')} | {canonical_status(entry)} | {count if count is not None else 'unavailable'} | {link} |"
            )
        lines.append("")
        for entry in entries:
            reasons = entry["metadata"].get("quality_review_reasons", [])
            if reasons:
                lines.append(
                    f"- Q{entry['identity']['question_number']} reasoning-review finding: {'; '.join(reasons)}"
                )
        for finding in pilot.get("review_findings", []):
            lines.append(f"- {finding}")
        lines.append("")
    lines += ["Manual user review is required before any broader generation.", ""]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

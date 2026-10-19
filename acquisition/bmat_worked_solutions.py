"""Cache WordPress year -> Section 1 -> question sources; never parse solutions."""

import argparse
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from urllib3.util.retry import Retry

from acquisition.bmat.__main__ import SystemTLSAdapter
from parsers.html_tree import entry

INDEX = "https://bmatworkedsolutions.wordpress.com/past-paper-worked-solutions/"
YEARS = tuple(range(2003, 2022))


def links(html, base):
    _, content = entry(html)
    return [
        (" ".join(n.text().split()), urldefrag(urljoin(base, n.attrs["href"]))[0])
        for n in content.walk()
        if n.tag == "a" and n.attrs.get("href")
    ]


def image_urls(html, base):
    _, content = entry(html)
    return sorted(
        {
            urljoin(base, n.attrs.get("data-orig-file") or n.attrs.get("src", ""))
            for n in content.walk()
            if n.tag == "img" and n.attrs.get("src")
        }
    )


def question_links(html, base):
    """Split anchor text and repeated URLs do not hide a numbered list entry."""
    _, content = entry(html)
    found = set()
    for n in content.walk():
        if n.tag not in {"a", "li"}:
            continue
        text = " ".join(n.text().replace("\ufffd", "").split())
        match = re.fullmatch(r"Question\s*(\d{1,2})", text, re.IGNORECASE)
        if match:
            for a in n.walk():
                if a.tag == "a" and a.attrs.get("href"):
                    found.add(
                        (int(match[1]), urldefrag(urljoin(base, a.attrs["href"]))[0])
                    )
    # Some old pages split Question / number across adjacent anchors outside li.
    by_url = {}
    for text, url in links(html, base):
        by_url.setdefault(url, []).append(text)
    for url, texts in by_url.items():
        match = re.fullmatch(r"Question\s*(\d{1,2})", " ".join(texts), re.IGNORECASE)
        if match:
            found.add((int(match[1]), url))
    return sorted(found)


def session():
    client = requests.Session()
    client.headers["User-Agent"] = "BMAT-local-source-research/1.0"
    client.mount(
        "https://",
        SystemTLSAdapter(
            max_retries=Retry(
                total=2, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504]
            )
        ),
    )
    return client


def acquire(
    output, *, years=YEARS, workers=2, client_factory=session, retry_failed_hosts=False
):
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    previous = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    cache = {r["source_url"]: r for r in previous.get("resources", [])}
    resources = dict(cache)
    failures = Counter(
        urlparse(r["source_url"]).hostname
        for r in cache.values()
        if r.get("status") == "failed"
        and (r.get("previous_error") or r.get("error", "")).startswith(
            ("SSLError:", "ConnectionError:", "ReadTimeout:", "ConnectTimeout:")
        )
    )
    unavailable_hosts = (
        set()
        if retry_failed_hosts
        else {h for h, count in failures.items() if count >= 3}
    )
    issues, rows = [], []
    result = {
        "source_family": "bmat",
        "section": "section_1",
        "index_url": INDEX,
        "requested_years": list(years),
        "years": [],
        "questions": rows,
        "issues": issues,
        "resources": [],
        "version": "1",
    }

    def save():
        result["resources"] = sorted(resources.values(), key=lambda r: r["source_url"])
        manifest_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def fetch(url, kind="html"):
        parsed = urlparse(url)
        allowed = (
            {"bmatworkedsolutions.wordpress.com", "bmatsolutions.blogspot.com"}
            if kind == "html"
            else {
                "bmatworkedsolutions.wordpress.com",
                "bmatworkedsolutions.files.wordpress.com",
                "s0.wp.com",
                "www.blogger.com",
            }
        )
        if parsed.scheme != "https" or parsed.hostname not in allowed:
            raise ValueError("Unexpected source host/scheme: " + url)
        prior = cache.get(url)
        if prior and prior.get("status") == "acquired":
            if kind == "asset" and not prior.get("content_type", "").startswith(
                "image/"
            ):
                raise ValueError("Source image URL returned non-image content: " + url)
            path = Path(prior["local_path"])
            if (
                path.is_file()
                and sha256(path.read_bytes()).hexdigest() == prior["sha256"]
            ):
                resources[url] = prior
                return prior
            raise ValueError("Acquired source hash changed: " + str(path))
        record = {"source_url": url, "kind": kind, "status": "failed"}
        try:
            if parsed.hostname in unavailable_hosts:
                record["previous_error"] = (prior or {}).get("previous_error") or (
                    prior or {}
                ).get("error")
                raise ValueError(
                    "Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
                )
            with client_factory() as client:
                response = client.get(url, timeout=45)
                response.raise_for_status()
                payload = response.content
                mime = response.headers.get("Content-Type", "").split(";", 1)[0]
                if kind == "html" and "html" not in mime:
                    raise ValueError("Expected HTML response")
                if kind == "asset" and not mime.startswith("image/"):
                    raise ValueError("Expected image response, got " + mime)
                extension = (
                    ".html"
                    if kind == "html"
                    else {
                        "image/png": ".png",
                        "image/jpeg": ".jpg",
                        "image/gif": ".gif",
                        "image/svg+xml": ".svg",
                    }.get(mime, ".bin")
                )
                folder = root / ("html" if kind == "html" else "assets")
                folder.mkdir(exist_ok=True)
                path = folder / (sha256(url.encode()).hexdigest()[:24] + extension)
                if path.exists() and path.read_bytes() != payload:
                    raise ValueError("Refusing destructive source replacement")
                path.write_bytes(payload)
                record.update(
                    local_path=str(path),
                    sha256=sha256(payload).hexdigest(),
                    content_type=mime,
                    status="acquired",
                    acquired_at=datetime.now(timezone.utc).isoformat(),
                    final_url=response.url,
                )
        except (requests.RequestException, OSError, ValueError) as error:
            record["error"] = type(error).__name__ + ": " + str(error)
        resources[url] = record
        if record["status"] != "acquired":
            raise ValueError(record["error"])
        return record

    def html(url):
        return Path(fetch(url)["local_path"]).read_text(encoding="utf-8-sig")

    try:
        index_links = links(html(INDEX), INDEX)
    except (ValueError, OSError) as error:
        issues.append({"code": "index_unavailable", "reason": str(error)})
        save()
        return result
    jobs = []
    for year in years:
        info = {"year": year, "status": "unavailable", "section": "section_1"}
        result["years"].append(info)
        try:
            choices = sorted(
                {u for text, u in index_links if re.search(rf"\b{year}\b", text)}
            )
            if len(choices) != 1:
                raise ValueError(f"Expected one year link, found {len(choices)}")
            info["year_url"] = choices[0]
            sections = sorted(
                {
                    u
                    for text, u in links(html(choices[0]), choices[0])
                    if re.fullmatch(r"Section\s*1", text, re.IGNORECASE)
                }
            )
            if len(sections) != 1:
                raise ValueError(f"Expected one Section 1 link, found {len(sections)}")
            info["section_url"] = sections[0]
            discovered = question_links(html(sections[0]), sections[0])
            if not discovered:
                raise ValueError("No question links found")
            seen = set()
            for number, url in discovered:
                if (number, url) in seen:
                    issues.append(
                        {
                            "code": "duplicate_question_link",
                            "year": year,
                            "question_number": number,
                            "source_url": url,
                        }
                    )
                    continue
                seen.add((number, url))
                jobs.append(
                    {
                        "source_family": "bmat",
                        "year": year,
                        "section": "section_1",
                        "question_number": number,
                        "source_url": url,
                    }
                )
            info.update(status="discovered", question_links=len(seen))
        except (ValueError, OSError) as error:
            issues.append(
                {
                    "code": "year_or_section_unavailable",
                    "year": year,
                    "reason": str(error),
                }
            )
        save()

    def question(job):
        row = dict(job)
        try:
            source = fetch(row["source_url"])
            row.update(
                status="acquired",
                local_path=source["local_path"],
                sha256=source["sha256"],
                assets=[],
            )
            for url in image_urls(
                Path(source["local_path"]).read_text(encoding="utf-8-sig"),
                row["source_url"],
            ):
                try:
                    row["assets"].append(fetch(url, "asset"))
                except ValueError as error:
                    row["assets"].append(
                        {"source_url": url, "status": "failed", "error": str(error)}
                    )
        except (ValueError, OSError) as error:
            row.update(status="failed", error=str(error))
        return row

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for row in executor.map(question, jobs):
            rows.append(row)
            if row["status"] != "acquired":
                issues.append({"code": "question_download_failed", **row})
            if len(rows) % 25 == 0:
                save()
                print(
                    f"Processed {len(rows)}/{len(jobs)} Section 1 sources ({sum(r['status'] == 'acquired' for r in rows)} acquired)",
                    flush=True,
                )
    rows.sort(key=lambda r: (r["year"], r["question_number"], r["source_url"]))
    for year in result["years"]:
        selected = [r for r in rows if r["year"] == year["year"]]
        if selected:
            year["status"] = (
                "acquired"
                if all(r["status"] == "acquired" for r in selected)
                else "partial"
            )
            year["acquired_pages"] = sum(r["status"] == "acquired" for r in selected)
    save()
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--output", type=Path, default=Path("data/input/bmat_worked_solutions")
    )
    cli.add_argument("--years", nargs="+", type=int, choices=YEARS, default=YEARS)
    cli.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    cli.add_argument(
        "--retry-failed-hosts",
        action="store_true",
        help="Explicitly retry a source host with three or more prior connection/TLS failures",
    )
    args = cli.parse_args()
    result = acquire(
        args.output,
        years=args.years,
        workers=args.workers,
        retry_failed_hosts=args.retry_failed_hosts,
    )
    print(
        json.dumps({"pages": len(result["questions"]), "issues": len(result["issues"])})
    )


if __name__ == "__main__":
    main()

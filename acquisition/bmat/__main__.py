"""Download only PMT Past Papers / Section 1 question papers, 2003--2021."""

import argparse
import json
import re
import ssl
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

INDEX = "https://www.physicsandmathstutor.com/admissions/bmat/papers/"
YEARS = tuple(range(2003, 2022))


class SystemTLSAdapter(HTTPAdapter):
    """Use OS trust roots as well as requests' bundle; verification stays on."""

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = ssl.create_default_context()
        return super().init_poolmanager(*args, **kwargs)


class Papers(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading = None
        self.capture = None
        self.text = []
        self.past = False
        self.section = None
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in {"h4", "h5"}:
            self.heading, self.text = tag, []
        elif tag == "a":
            self.capture, self.text = dict(attrs).get("href"), []

    def handle_data(self, data):
        if self.heading or self.capture:
            self.text.append(data)

    def handle_endtag(self, tag):
        text = " ".join("".join(self.text).split())
        if tag == self.heading:
            if tag == "h4":
                self.past = text == "Past Papers"
            if tag == "h5":
                self.section = text.rstrip(":")
            self.heading = None
        elif tag == "a" and self.capture:
            if self.past and self.section == "Section 1":
                match = re.fullmatch(r"BMAT (\d{4}) Section 1 Question Paper", text)
                if match and int(match[1]) in YEARS:
                    self.links.append((int(match[1]), urljoin(INDEX, self.capture)))
            self.capture = None


def acquire(output_dir, *, session=None):
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    previous = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    previous = {r["year"]: r for r in previous.get("files", [])}
    client = session or requests.Session()
    if session is None:
        client.headers["User-Agent"] = "Mozilla/5.0 BMAT-research-downloader/1.0"
        client.mount(
            "https://",
            SystemTLSAdapter(
                max_retries=Retry(
                    total=2,
                    backoff_factor=2,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
            ),
        )
    records, index_issue = [], None
    parser = Papers()
    try:
        response = client.get(INDEX, timeout=60)
        response.raise_for_status()
        parser.feed(response.text)
        (root / "index.html").write_bytes(response.content)
    except requests.RequestException as error:
        index_issue = type(error).__name__ + ": " + str(error)
    for year in YEARS:
        urls = sorted({u for y, u in parser.links if y == year})
        path = root / f"BMAT {year} Section 1 Question Paper.pdf"
        row = {
            "year": year,
            "section": "section_1",
            "document_role": "question_paper",
            "source_url": urls[0] if len(urls) == 1 else None,
            "local_path": str(path),
            "status": "unavailable",
            "sha256": None,
            "error": None,
        }
        try:
            if index_issue:
                raise ValueError("Index unavailable: " + index_issue)
            if len(urls) != 1:
                raise ValueError(f"Expected one source link, found {len(urls)}")
            if path.exists():
                payload = path.read_bytes()
                old = previous.get(year) or {}
                if (
                    old.get("sha256") != sha256(payload).hexdigest()
                    or old.get("source_url") != urls[0]
                ):
                    raise ValueError(
                        "Existing input differs from its acquisition manifest; refusing overwrite"
                    )
                row["status"] = "already_downloaded"
            else:
                response = client.get(urls[0], timeout=90)
                response.raise_for_status()
                if urlparse(response.url).hostname not in {
                    "pmt.physicsandmathstutor.com",
                    "www.physicsandmathstutor.com",
                    "physicsandmathstutor.com",
                }:
                    raise ValueError("Unexpected download redirect host")
                payload = response.content
                if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-4096:]:
                    raise ValueError("Response is not a complete PDF")
                with path.open("xb") as stream:
                    stream.write(payload)
                row["status"] = "downloaded"
            row.update(sha256=sha256(payload).hexdigest(), size_bytes=len(payload))
        except (requests.RequestException, ValueError, OSError) as error:
            row.update(status="failed", error=type(error).__name__ + ": " + str(error))
        records.append(row)
        manifest = {
            "stage": "acquisition",
            "source": "bmat",
            "index_url": INDEX,
            "years": list(YEARS),
            "index_error": index_issue,
            "files": records,
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(year, row["status"], row.get("error") or "", flush=True)
    return manifest


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output-dir", type=Path, default=Path("data/input/bmat"))
    args = cli.parse_args(argv)
    data = acquire(args.output_dir)
    return int(any(r["status"] == "failed" for r in data["files"]))


if __name__ == "__main__":
    raise SystemExit(main())

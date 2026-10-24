"""SJM independent public job radar. READ ONLY. No personal data, no applications."""
from __future__ import annotations
import datetime as dt
import html
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

BOARDS = [
    ("Welo Data / Welocalize", "lever", "https://api.lever.co/v0/postings/weloglobal?mode=json"),
    ("Welocalize", "lever", "https://api.lever.co/v0/postings/welocalize?mode=json"),
    ("Appen", "greenhouse", "https://boards-api.greenhouse.io/v1/boards/appen/jobs"),
    ("Micro1", "lever", "https://api.lever.co/v0/postings/micro1?mode=json"),
]
GEO = re.compile(r"\b(colombia|latam|latin america|latin-america|south america|remote|remoto|anywhere)\b", re.I)
SKILL = re.compile(r"\b(spanish|espa[nñ]ol|annotat|data|quality|review|fitness|trainer|support|asist|digital|content|ai |ia |customer)\b", re.I)
ADVANCED_EN = re.compile(r"\b(fluent|native|advanced|c1|c2|bilingual)\s+(?:spoken\s+)?english\b|\benglish\s+(?:fluency|c1|c2|required)\b", re.I)
MAX_RESPONSE = 5_000_000
OUT = Path(os.getenv("SJM_RADAR_REPORT", "sjm-radar-public-results.json"))

def download(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "SJM-ReadOnly-Radar/1.0 (public-job-listing-check)", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=16) as response:
        if response.status != 200:
            raise ValueError("http_status_" + str(response.status))
        payload = response.read(MAX_RESPONSE + 1)
        if len(payload) > MAX_RESPONSE:
            raise ValueError("response_too_large")
    return json.loads(payload.decode("utf-8"))

def listings(kind: str, data):
    if kind == "lever":
        if not isinstance(data, list):
            raise ValueError("unexpected_lever_format")
        for item in data:
            categories = item.get("categories") or {}
            yield {
                "title": str(item.get("text") or "")[:180],
                "location": str(categories.get("location") or "")[:180],
                "url": str(item.get("hostedUrl") or "")[:350],
                "description": str(item.get("descriptionPlain") or "")[:1800],
            }
    elif kind == "greenhouse":
        for item in (data.get("jobs") or []):
            yield {
                "title": str(item.get("title") or "")[:180],
                "location": str((item.get("location") or {}).get("name") or "")[:180],
                "url": str(item.get("absolute_url") or "")[:350],
                "description": "",
            }

def main():
    result = {
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "purpose": "public_read_only_discovery",
        "notice": "Coincidencia de palabras NO significa vacante elegible ni candidatura enviada. Revisar cada anuncio, idioma, país, plazo y condiciones manualmente.",
        "personal_data_included": False,
        "applications_submitted": 0,
        "sources": [],
        "candidates": [],
    }
    unique = set()
    for company, kind, url in BOARDS:
        source = {"company": company, "official_feed": url, "state": "unavailable", "total_listings": 0, "matches": 0}
        try:
            data = download(url)
            positions = list(listings(kind, data))
            source["total_listings"] = len(positions)
            source["state"] = "fetched"
            for job in positions:
                title, location, description = job["title"], job["location"], job["description"]
                link = job["url"]
                if not link.startswith("https://"):
                    continue
                if not GEO.search(location + " " + title):
                    continue
                if not SKILL.search(title + " " + description):
                    continue
                if link in unique:
                    continue
                unique.add(link)
                source["matches"] += 1
                result["candidates"].append({
                    "organization": company,
                    "position": title,
                    "location": location,
                    "official_link": link,
                    "status": "requires_manual_eligibility_check",
                    "possible_advanced_english": bool(ADVANCED_EN.search(description)),
                    "confirmed_application": False,
                })
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            source["state"] = "unavailable"
            source["error_class"] = type(exc).__name__
        result["sources"].append(source)
    result["candidates"] = result["candidates"][:60]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "sources_checked": len(BOARDS), "sources_fetched": sum(s["state"] == "fetched" for s in result["sources"]),
        "candidates_for_review": len(result["candidates"]), "applications_submitted": 0,
        "report": str(OUT)
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()

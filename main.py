"""GitHub profile CLI.

Usage:
    python main.py octocat
    python main.py octocat torvalds gvanrossum
"""
import argparse
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

API_URL = "https://api.github.com/users/{username}"
OUTPUT_DIR = Path("output")
LOG_FILE = Path("logs") / "errors.log"
CSV_FIELDS = ["login", "name", "public_repos", "followers"]


def setup_logging() -> None:
    """Send errors to a file (not only to the screen)."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.ERROR,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def build_headers() -> dict:
    """Add the optional GITHUB_TOKEN from .env."""
    load_dotenv()
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_profile(username: str, headers: dict, retries: int = 3, delay: float = 1.0):
    """Return the profile dict, or None if it could not be fetched.

    Retries only problems that can fix themselves (timeout, no internet,
    429, 5xx). A 404 (no such user) or 401 (bad token) is never retried.
    """
    url = API_URL.format(username=username)

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 404:
                msg = f"User '{username}' not found"
                print(f"  X {msg}")
                logging.error(msg)
                return None
            if response.status_code == 401:
                msg = "Bad or missing GITHUB_TOKEN (401)"
                print(f"  X {msg}")
                logging.error(msg)
                return None
            if response.status_code == 403:
                msg = "403 Forbidden - probably GitHub's rate limit. Add a GITHUB_TOKEN to .env"
                print(f"  X {msg}")
                logging.error("%s: %s", username, msg)
                return None
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(
                    f"Retryable status {response.status_code}", response=response
                )

            response.raise_for_status()  # any other 4xx raises here
            return response.json()

        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
            if isinstance(e, requests.HTTPError) and e.response is not None:
                if e.response.status_code < 500 and e.response.status_code != 429:
                    logging.error("%s: HTTP %s", username, e.response.status_code)
                    print(f"  X HTTP error {e.response.status_code} for '{username}'")
                    return None
            logging.error("%s: attempt %d/%d failed: %s", username, attempt, retries, e)
            print(f"  ! attempt {attempt}/{retries} failed ({type(e).__name__})")
            if attempt < retries:
                time.sleep(delay)

    print(f"  X Giving up on '{username}' after {retries} attempts")
    return None


def save_profile(username: str, profile: dict) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{username}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    return path


def write_summary_csv(rows: list) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / "summary.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def summarize(profile: dict) -> dict:
    """Pick the 4 columns; .get() so a missing field never crashes us."""
    return {
        "login": profile.get("login", ""),
        "name": profile.get("name") or "",
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch GitHub profiles.")
    parser.add_argument("usernames", nargs="+", help="one or more GitHub usernames")
    args = parser.parse_args()

    setup_logging()
    headers = build_headers()
    rows = []

    for username in args.usernames:
        print(f"Fetching {username}...")
        profile = fetch_profile(username, headers)
        if profile is None:
            continue
        path = save_profile(username, profile)
        rows.append(summarize(profile))
        print(f"  OK saved to {path}")

    if rows:
        csv_path = write_summary_csv(rows)
        print(f"\nSummary written to {csv_path}")
        for r in rows:
            print(f"  {r['login']:<15} {r['name']:<25} repos={r['public_repos']:<4} followers={r['followers']}")
    else:
        print("\nNothing saved. Check logs/errors.log")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())

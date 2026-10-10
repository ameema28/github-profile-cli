# GitHub Profile CLI

A small command-line tool that fetches one or more GitHub user profiles from the
GitHub REST API, saves each one as JSON, and writes a summary CSV.

## What it does
- Fetches profiles for several usernames in one run
- Saves each profile to `output/<username>.json`
- Writes `output/summary.csv` with: login, name, public_repos, followers
- Retries failed requests up to 3 times (timeouts, no internet, 429, 5xx)
- Never retries a 404 (user not found) or 401 (bad token)
- Logs errors to `logs/errors.log` as well as printing them
- Optionally uses a `GITHUB_TOKEN` from `.env` for a higher rate limit

## Setup
```bash
git clone <your-repo-url>
cd github-profile-cli

# 1. create + activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. install dependencies
pip install -r requirements.txt

# 3. (optional) add your token
copy .env.example .env          # Windows  (macOS/Linux: cp .env.example .env)
# then open .env and paste:  GITHUB_TOKEN=your_token_here
```

## Run
```bash
python main.py octocat
python main.py octocat torvalds gvanrossum
```

## Example output
```
Fetching octocat...
  OK saved to output/octocat.json
Fetching this-user-does-not-exist...
  X User 'this-user-does-not-exist' not found

Summary written to output/summary.csv
  octocat         The Octocat               repos=8    followers=<number>
```

`output/summary.csv`
```
login,name,public_repos,followers
octocat,The Octocat,8,<number>
```

## Tests
```bash
pytest
```

## Known limitations
- Without a token GitHub allows only 60 requests per hour per IP
- Only public profile data is fetched
- Retries use a fixed 1-second delay (no exponential back-off)

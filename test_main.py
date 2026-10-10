from main import summarize


def test_summarize_handles_missing_name():
    profile = {"login": "octocat", "name": None, "public_repos": 8, "followers": 100}
    assert summarize(profile) == {
        "login": "octocat",
        "name": "",
        "public_repos": 8,
        "followers": 100,
    }

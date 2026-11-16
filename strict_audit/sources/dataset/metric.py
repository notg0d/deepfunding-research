"""Scorer for the Deep Funding Originality (Round 3) competition on Hugging Face.

One file, three uses:

* The competition's custom metric. The Hugging Face competitions app downloads this file from the
  private competition repo, imports it and calls ``compute(params)`` for every submission.
* A local checker for participants, published in the competition dataset:

      python metric.py my_submission.csv
      python metric.py my_submission.csv --solution public_leaderboard_targets.csv

* The parser and scorer behind ``organizer.py rescore``.

Score ("error"): for every repository in a leaderboard split, take the absolute difference between the
submitted originality and the repository's mean juror originality (the jurors' 0-100 ratings averaged,
divided by 100), then add them up. Lower is better. This is the rule of the Deep Funding Contest
Level II on Pond.

Only the Python standard library is needed, except in ``compute``, which downloads with huggingface_hub.
Written for Python 3.10, the version the competitions Space image runs.
"""

import csv
import io
import math
import os
import sys

ID_COLUMN = "repo"
VALUE_COLUMN = "originality"
SPLIT_COLUMN = "split"
SCORE_NAME = "error"
SPLITS = ("public", "private")
REPOS_FILE = "repos.csv"
SOLUTION_FILE = "solution.csv"
MAX_LISTED = 10


class SubmissionError(ValueError):
    """The submission breaks the format. The message lists every problem found."""


def normalize_repo(value):
    """Reduce 'https://github.com/Owner/Name/', 'github.com/owner/name.git' or 'owner/name' to 'owner/name'."""
    key = value.strip().lower()
    for prefix in ("https://", "http://"):
        if key.startswith(prefix):
            key = key[len(prefix):]
            break
    if key.startswith("www."):
        key = key[len("www."):]
    if key.startswith("github.com/"):
        key = key[len("github.com/"):]
    key = key.rstrip("/")
    if key.endswith(".git"):
        key = key[: -len(".git")]
    return key


def _text(data, what):
    if isinstance(data, bytes):
        try:
            data = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise SubmissionError(f"{what} is not UTF-8 text. Save it as a UTF-8 CSV file.")
    return data.lstrip("﻿")


def _records(text, what):
    """Return (row_number, cells) for every non-blank CSV record. Row 1 is the header."""
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as err:
        raise SubmissionError(f"{what} could not be read as CSV: {err}")
    return [(number, cells) for number, cells in enumerate(rows, start=1) if any(c.strip() for c in cells)]


def _header(cells):
    return [cell.strip().lower() for cell in cells]


def _cell(cells, index):
    return cells[index].strip() if index < len(cells) else ""


def load_repos(data):
    """Read repos.csv. Returns {normalized name: name as the markets spell it}, in file order."""
    records = _records(_text(data, REPOS_FILE), REPOS_FILE)
    if not records or ID_COLUMN not in _header(records[0][1]):
        raise ValueError(f"{REPOS_FILE} needs a '{ID_COLUMN}' column")
    index = _header(records[0][1]).index(ID_COLUMN)
    universe = {}
    for number, cells in records[1:]:
        name = _cell(cells, index)
        key = normalize_repo(name)
        if not key or key in universe:
            raise ValueError(f"{REPOS_FILE} row {number}: empty or duplicate repo {name!r}")
        universe[key] = name
    if not universe:
        raise ValueError(f"{REPOS_FILE} lists no repos")
    return universe


def load_solution(data, universe):
    """Read a targets file (repo, split, originality). Returns {split: {repo: originality}}."""
    records = _records(_text(data, SOLUTION_FILE), SOLUTION_FILE)
    needed = (ID_COLUMN, SPLIT_COLUMN, VALUE_COLUMN)
    header = _header(records[0][1]) if records else []
    if any(column not in header for column in needed):
        raise ValueError(f"the targets file needs the columns {', '.join(needed)}")
    i_repo, i_split, i_value = (header.index(column) for column in needed)
    truth = {split: {} for split in SPLITS}
    for number, cells in records[1:]:
        name, split, raw = _cell(cells, i_repo), _cell(cells, i_split).lower(), _cell(cells, i_value)
        key = normalize_repo(name)
        if key not in universe:
            raise ValueError(f"targets row {number}: {name!r} is not a competition repo")
        if split not in truth:
            raise ValueError(f"targets row {number}: split must be public or private, not {split!r}")
        value = float(raw)
        if not (math.isfinite(value) and 0.0 <= value <= 1.0):
            raise ValueError(f"targets row {number}: originality {raw!r} is outside [0, 1]")
        repo = universe[key]
        if repo in truth[split]:
            raise ValueError(f"targets row {number}: {repo} appears twice in the {split} split")
        truth[split][repo] = value
    return truth


def parse_submission(data, universe):
    """Check a submission and return {repo: originality} for every competition repo.

    Raises SubmissionError listing every problem: a missing header, an unknown, empty or repeated repo,
    a value that is not a number in [0, 1], or a competition repo that is absent.
    """
    records = _records(_text(data, "The file"), "The file")
    if not records:
        raise SubmissionError("The file is empty.")
    header = _header(records[0][1])
    if header.count(ID_COLUMN) != 1 or header.count(VALUE_COLUMN) != 1:
        found = ",".join(records[0][1])
        raise SubmissionError(f"The first row must be the header '{ID_COLUMN},{VALUE_COLUMN}'. Found: {found}")
    i_repo, i_value = header.index(ID_COLUMN), header.index(VALUE_COLUMN)

    problems = []
    seen = {}
    predictions = {}
    for number, cells in records[1:]:
        name, raw = _cell(cells, i_repo), _cell(cells, i_value)
        key = normalize_repo(name)
        if not key:
            problems.append(f"row {number}: the repo cell is empty")
            continue
        if key not in universe:
            problems.append(f"row {number}: {name!r} is not one of the {len(universe)} competition repos")
            continue
        repo = universe[key]
        if repo in seen:
            problems.append(f"row {number}: {repo} already appears in row {seen[repo]}")
            continue
        seen[repo] = number
        try:
            value = float(raw)
        except ValueError:
            problems.append(f"row {number}: originality {raw!r} for {repo} is not a number")
            continue
        if not (math.isfinite(value) and 0.0 <= value <= 1.0):
            problems.append(f"row {number}: originality {raw!r} for {repo} must be between 0 and 1")
            continue
        predictions[repo] = value

    missing = [repo for repo in universe.values() if repo not in seen]
    if missing:
        listed = ", ".join(missing[:MAX_LISTED]) + (", ..." if len(missing) > MAX_LISTED else "")
        problems.append(f"{len(missing)} competition repo(s) missing: {listed}")
    if problems:
        more = len(problems) - MAX_LISTED
        lines = problems[:MAX_LISTED] + ([f"... and {more} more problem(s)"] if more > 0 else [])
        raise SubmissionError("\n".join(lines))
    return predictions


def score_split(predictions, targets):
    """Sum of absolute errors over the repos in one split."""
    return sum(abs(predictions[repo] - value) for repo, value in targets.items())


def evaluate(predictions, truth):
    """Scores in the shape the competitions app stores.

    Until the Round 3 juror averages are added as private rows, the private score is a placeholder
    equal to the public score; organizer.py rescore replaces it once they exist.
    """
    public = score_split(predictions, truth["public"])
    private = score_split(predictions, truth["private"]) if truth["private"] else public
    return {"public_score": {SCORE_NAME: public}, "private_score": {SCORE_NAME: private}}


def submission_path(team_id, submission_id, repo_files):
    """The competitions app stores a submission as submissions/<team>-<id>.<extension of the upload>."""
    stem = f"submissions/{team_id}-{submission_id}."
    matches = [name for name in repo_files if name.startswith(stem)]
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one file named {stem}*, found {len(matches)}")
    return matches[0]


def compute(params):
    """Entry point for the Hugging Face competitions app (EVAL_METRIC "custom")."""
    from huggingface_hub import HfApi, hf_hub_download

    def fetch(filename):
        path = hf_hub_download(
            repo_id=params.competition_id,
            filename=filename,
            token=params.token,
            repo_type="dataset",
        )
        with open(path, "rb") as handle:
            return handle.read()

    universe = load_repos(fetch(REPOS_FILE))
    truth = load_solution(fetch(SOLUTION_FILE), universe)
    try:
        submission = fetch(f"submissions/{params.team_id}-{params.submission_id}.csv")
    except Exception:
        files = HfApi(token=params.token).list_repo_files(repo_id=params.competition_id, repo_type="dataset")
        submission = fetch(submission_path(params.team_id, params.submission_id, files))
    return evaluate(parse_submission(submission, universe), truth)


def _read(path):
    with open(path, "rb") as handle:
        return handle.read()


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        description="Check a Deep Funding Originality submission, and score it if you pass a targets file."
    )
    parser.add_argument("submission", help="your CSV with the columns repo,originality")
    parser.add_argument("--repos", help=f"the competition's {REPOS_FILE} (default: the one next to this script)")
    parser.add_argument("--solution", help="a targets file with repo,split,originality, e.g. public_leaderboard_targets.csv")
    args = parser.parse_args(argv)

    repos_path = args.repos or os.path.join(os.path.dirname(os.path.abspath(__file__)), REPOS_FILE)
    universe = load_repos(_read(repos_path))
    try:
        predictions = parse_submission(_read(args.submission), universe)
    except SubmissionError as err:
        print(f"INVALID: {args.submission}\n{err}", file=sys.stderr)
        return 1
    print(f"OK: {args.submission} has all {len(predictions)} repos, every value in [0, 1].")
    if args.solution:
        truth = load_solution(_read(args.solution), universe)
        for split in SPLITS:
            if truth[split]:
                error = score_split(predictions, truth[split])
                print(f"{split} {SCORE_NAME}: {error:.4f} (sum of absolute errors over {len(truth[split])} repos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

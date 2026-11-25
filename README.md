<p align="center">
  <img src="readme-banner.png" width="920" alt="Repo Pulse. See where your Git checkout stands · main  ↑ 2  ↓ 0 · Example local checkout.">
</p>

# Repo Pulse

A read-only snapshot of a local Git checkout. See the branch, working-tree changes, recent commit subjects, and ahead/behind counts against the local copy of the upstream ref.

## At a glance

| Task | How |
| --- | --- |
| **Check the working tree** | See the current branch and local changes. |
| **Compare with upstream** | Read ahead and behind counts from the upstream ref already on disk. |
| **Review history or export** | Use `--commits` to set the history length and `--json` for structured output. |

## Quick start

```sh
python3 repo_pulse.py /path/to/repo
python3 repo_pulse.py . --commits 10 --json
```

Requires Python 3.8+ and Git. Run from a project or pass any folder inside it. Repo Pulse reads local Git data without fetching, staging, or committing. Ahead and behind counts reflect the upstream ref already present in your checkout. A fresh repository with no commits still reports its working-tree changes.

[MIT license](LICENSE)

## Development

```sh
python3 -m unittest discover -s tests -v
ruff check .
ruff format --check .
```

To run the same lint and formatting checks before each local commit, install Ruff
and pre-commit on your PATH, then run `pre-commit install` in the checkout.

```mermaid
flowchart LR
    A[Checkout path] --> B[Read Git refs and working tree]
    B --> C[Build report]
    C --> D[Terminal output or JSON]
```

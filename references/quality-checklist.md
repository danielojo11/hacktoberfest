# Quality Checklist

Read this when you give improvement suggestions. Contents: how to give suggestions, code quality ideas, product quality ideas, good and bad suggestions.

## 1. How to give suggestions

- Start from the output of `python3 scripts/quality_report.py <project> --out QUALITY_REPORT.md`. Then add what the script cannot see (below).
- Give 3 to 5 suggestions, not 20. Order them by effect: security first, then tests, then docs, then style.
- For each one say: **what**, **why it matters** (one sentence), **how** (one concrete first step).
- Suggest only. Do not add features, tests, or CI files unless the user says yes. Refactoring is done through the plan, not here.
- PLAIN mode: say "people can install it more easily" instead of "dependency pinning".

## 2. Code quality ideas

| Area | Ask | Suggest |
|------|-----|---------|
| Safety | Any password, key, or token in the code? | Move to environment variables; change any key that was committed |
| Safety | Is user input passed to `eval`, `exec`, a shell, or an SQL string? | Use a parser, a list of command parts, or query parameters |
| Errors | What happens when a file is missing, the network is down, or the input is empty? | Catch the specific error and show a clear message |
| Tests | Is the main job covered by a test? | Add 3 tests: normal input, empty input, bad input |
| Names | Can a stranger tell what each function does from its name? | Rename; one verb per function (`load_orders`, `total_price`) |
| Size | Any function over 30 lines or file over 300 lines? | Run `scripts/make_refactor_plan.py` |
| Docs | Does each public function say what it does? | One-line docstring or comment |
| Types | Are inputs and outputs clear? | Add type hints (Python) or TypeScript |
| Tools | Is a formatter and linter set up? | Ruff (Python), ESLint and Prettier (JavaScript) |
| Speed | Any loop that reads a file or calls the network again and again? | Read once, keep the result |

## 3. Product quality ideas

| Area | Ask | Suggest |
|------|-----|---------|
| First 5 minutes | Can a new person run it using only the README? | Test the install steps in an empty folder; fix every gap |
| README | Does it say what, why, install, use, example? | Add a short example with real output or a screenshot |
| Demo | Can someone see it work without installing? | Add a GIF, screenshot, or short video link |
| Errors for users | Are messages written for users, not programmers? | "Could not open orders.csv. Does the file exist?" |
| Defaults | Does it work with no setup for the common case? | Choose safe defaults; ask only when needed |
| Accessibility | Works for keyboard users, readable colors, alt text on images? | Add alt text; check contrast; label buttons |
| Trust | Is there a LICENSE, a privacy note if it handles personal data? | Add MIT or another license; say what data is stored |
| Releases | Can people see what changed? | Add CHANGELOG.md and version tags |
| Community | Do contributors know how to help? | CONTRIBUTING.md, issue templates, "good first issue" labels |
| Automation | Do tests run on every push? | GitHub Actions workflow that runs the tests |

## 4. Good and bad suggestions

**Bad:** "Improve error handling and add more tests."
(No place, no first step.)

**Good:** "`load_orders()` crashes if the file is missing. Why it matters: new users will see a long error and give up. First step: catch `FileNotFoundError` and print 'Could not find orders.csv in this folder.'"

**Bad (PLAIN mode):** "Pin your transitive dependencies for reproducible builds."
**Good (PLAIN mode):** "Add a file that lists the extra tools your project needs, so other people can install them with one command."

## 5. Suggestion format

```
Suggestions (most important first)
1. <what> - <why it matters>. First step: <one concrete action>.
2. ...
```

# Refactor and Explain Skill

This skill helps an AI agent make a step-by-step refactor plan for your code, carry it out safely without changing what the code does, and explain it in plain words for beginners or in detail for developers. It also suggests how to improve code quality and product quality, and writes a `HOW_TO_RUN.txt` file so anyone can run the project.

## Example prompts

- "Make a refactor plan for this project and do it."
- "Refactor this code and explain what you changed."
- "I am not a developer. What does this script do?"
- "How can I improve the quality of this project?"
- "Clean up my project and write instructions for running it."
- "How do I run this?"

## What is in this repo

- `SKILL.md` is the instruction card. The agent always reads it first.
- `scripts/` holds small programs the agent can run to do exact jobs.
  - `scripts/make_refactor_plan.py` scans your code and writes `REFACTOR_PLAN.md`, a checklist in 5 phases. It can also count how many steps are done.
  - `scripts/quality_report.py` checks code quality (secrets, `eval`, docstrings, linter) and product quality (README, tests, license, CI) and lists what to fix first.
  - `scripts/make_run_guide.py` looks at a project (Python, Node, Rust, Go, Java, Make, HTML, shell) and writes `HOW_TO_RUN.txt`.
- `references/` holds extra reading the agent opens only when needed.
  - `references/refactor-rules.md` has safe refactoring rules, common fixes, a before and after example, and how to run a plan.
  - `references/quality-checklist.md` has code and product quality ideas and how to word good suggestions.
  - `references/explain-templates.md` has templates for explaining code to non-developers and developers.
- `LICENSE` is the MIT license. `.gitignore` keeps junk files out of git.

## Install with npx

```bash
npx skills add YOUR_GITHUB_USERNAME/refactor-explain-skill
```

## Check it before installing

```bash
npx skills add YOUR_GITHUB_USERNAME/refactor-explain-skill --list
```

## Manual install for Claude Code

1. Clone the repo:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/refactor-explain-skill.git
   ```
2. Copy the folder to one of these places:
   - Per project: `.claude/skills/refactor-explain/`
   - Personal (all projects): `~/.claude/skills/refactor-explain/`

   Example: `cp -r refactor-explain-skill ~/.claude/skills/refactor-explain`

## Other agents

Cursor, OpenCode and other agents are supported through the `npx` command above.

## Test that it works

1. Install the skill.
2. Open a project and ask your agent: "Explain this code simply and write instructions for running it."
3. The agent should explain the code and create a `HOW_TO_RUN.txt` file.
4. Or ask: "How can I improve this project?" The agent should create `QUALITY_REPORT.md` and give ranked suggestions.
5. Or ask: "Make a refactor plan for this project and do it." The agent should create `REFACTOR_PLAN.md` and tick the boxes as it works.

You can also run the scripts yourself (needs Python 3):

```bash
python3 scripts/make_refactor_plan.py path/to/project --out REFACTOR_PLAN.md
python3 scripts/make_refactor_plan.py --progress REFACTOR_PLAN.md
python3 scripts/quality_report.py path/to/project --out QUALITY_REPORT.md
python3 scripts/make_run_guide.py path/to/project --out HOW_TO_RUN.txt
```

## Hacktoberfest

Built for the Hacktoberfest hackathon. Contributions are welcome! Ideas: deeper checks for JavaScript and other languages, support for more project types (Docker, C#, PHP), more refactoring examples.

## License

MIT. See `LICENSE`.

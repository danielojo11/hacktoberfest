---
name: refactor-explain
description: Makes a step-by-step refactor plan for code, carries it out safely without changing what the code does, explains it in plain words for beginners or in detail for developers, suggests how to improve code quality and product quality, and writes a HOW_TO_RUN.txt file. Use when the user says "refactor this", "make a refactor plan", "clean up my code", "explain this code", "how can I improve this project", "review my code quality", "I am not a developer", or "how do I run this".
---

# Refactor and Explain

Plan the cleanup, do it safely, explain the code, suggest improvements, and write a plain-text guide for running it.

## Steps

1. **Read the code first.** Find the main file and what it is for. If the user pasted a snippet, work on the snippet.
2. **Pick the audience.** If the user says they are not a developer, or asks "what does this do", use PLAIN mode. Otherwise use DEV mode. If unsure, use PLAIN mode.
3. **Read `references/refactor-rules.md`** before you change anything. It has the golden rules, how to run a plan, and the change report template.
4. **Make the plan.** Run this on the project folder (or one file):

   ```bash
   python3 scripts/make_refactor_plan.py <project-folder> --out REFACTOR_PLAN.md
   ```

   It writes a checklist in 5 phases. Read it. Delete wrong or risky items, and add what a scanner cannot see (unclear names, confusing logic). If it prints "No code files found", write the plan by hand in the same 5 phases. Tell the user the plan in 3 or 4 lines.
5. **Run the plan.** If the user only asked for a plan, stop here and ask if they want it done. Otherwise:
   - Do the steps in order, one at a time. Never skip Phase 1 or Phase 5.
   - After each step, change `- [ ]` to `- [x]` in `REFACTOR_PLAN.md`.
   - After each phase, run the tests (or the program) and compare with Phase 1.
   - If something breaks, undo the last step, mark it `SKIPPED: reason`, and go on.
   - Check progress any time:

     ```bash
     python3 scripts/make_refactor_plan.py --progress REFACTOR_PLAN.md
     ```
6. **Explain.** Read `references/explain-templates.md` and follow the template for PLAIN or DEV mode.
7. **Suggest improvements.** Run:

   ```bash
   python3 scripts/quality_report.py <project-folder> --out QUALITY_REPORT.md
   ```

   It checks code quality (secrets, `eval`, docstrings, linter) and product quality (README, tests, license, CI). Read `references/quality-checklist.md`, add what the script cannot see, and give 3 to 5 suggestions in the format it shows. Only suggest. Do not add new features, tests, or CI files unless the user says yes.
8. **Write the run guide.** Run:

   ```bash
   python3 scripts/make_run_guide.py <project-folder> --out HOW_TO_RUN.txt
   ```

   It guesses from file names, so read the output and fix anything wrong (entry file, port, extra tools). If it prints "No project found", write HOW_TO_RUN.txt by hand.
9. **Reply** with: the change report (short), the explanation, the suggestions, and where `REFACTOR_PLAN.md`, `QUALITY_REPORT.md` and `HOW_TO_RUN.txt` are.

## Examples

**User:** "Make a refactor plan for my app and do it."
**Agent:** Runs `python3 scripts/make_refactor_plan.py . --out REFACTOR_PLAN.md`, trims the plan, works through it ticking boxes, tests after each phase, then explains the result and writes `HOW_TO_RUN.txt`.

**User:** "How can I improve my project?"
**Agent:** Runs `python3 scripts/quality_report.py . --out QUALITY_REPORT.md`, reads `references/quality-checklist.md`, and replies with 3 to 5 ranked suggestions, each with a why and a first step. It changes nothing.

**User:** "I am not a developer. What does this script do and how do I run it?" (attaches `report.py`)
**Agent:** PLAIN mode. No refactor unless asked. Explains with the plain template, runs `python3 scripts/make_run_guide.py report.py --out HOW_TO_RUN.txt`, and checks the file.

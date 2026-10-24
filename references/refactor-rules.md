# Refactor Rules

Read this before you change any code. Contents: golden rules, safe steps, common problems and fixes, a before and after example, things not to do, change report, running a plan.

## 1. Golden rules

1. **Same behavior.** The code must give the same results after the change. Refactoring is not adding features or fixing bugs.
2. **Small steps.** One kind of change at a time (rename, then split, then tidy).
3. **Keep public names.** Do not rename functions, files, routes, or options that other code or users depend on, unless the user asks.
4. **Test around it.** If tests exist, run them before and after. If not, run the program once before and after and compare the output.
5. **Tell the truth about bugs.** If you spot a bug, do not silently fix it. List it under "Found but not changed".

## 2. Safe order of work

1. Run the tests or the program. Save the result.
2. Rename unclear names.
3. Remove dead code (unused variables, old commented-out code).
4. Replace "magic numbers" with named constants.
5. Flatten deep nesting with early returns.
6. Split long functions (over about 30 lines) into small ones with one job.
7. Merge copy-pasted code into one function.
8. Run the tests or the program again. Compare.

## 3. Common problems and fixes

| Problem | Fix |
|---------|-----|
| Names like `x`, `tmp`, `data2` | Name it for what it holds: `user_age`, `price_with_tax` |
| Number like `86400` in code | `SECONDS_PER_DAY = 86400` |
| `if` inside `if` inside `if` | Check the bad case first and `return` early |
| One function does 5 jobs | One function per job, then one short function that calls them |
| Same code pasted 3 times | Make one function and call it 3 times |
| Comment says what the code obviously does | Delete the comment, or make the name say it |
| Comment explains why (a hidden reason) | Keep it |
| Bare `except:` that hides errors | Catch the specific error and say what failed |

## 4. Before and after (Python)

Before:
```python
def f(l):
    t = 0
    for i in l:
        if i["paid"] == True:
            if i["amount"] > 0:
                t = t + i["amount"] * 1.2
    return t
```

After:
```python
TAX_MULTIPLIER = 1.2

def total_paid_with_tax(orders):
    total = 0
    for order in orders:
        if not order["paid"] or order["amount"] <= 0:
            continue
        total += order["amount"] * TAX_MULTIPLIER
    return total
```

Summary to give the user: renamed `f` to `total_paid_with_tax`, named the tax number, flattened the nesting. Same results.
Note: `f` was renamed, so tell the user to update any code that calls it.

## 5. Do not

- Do not reformat the whole project in one go. It hides the real changes.
- Do not change the language, framework, or folder layout unless asked.
- Do not delete code you are not sure is unused. List it instead.
- Do not add new packages just to tidy code.

## 6. Change report template

```
Changed:
- <what and why, one line each>
Found but not changed:
- <bugs or risks>
Check: <tests run or how you compared output>
```

## 7. Running a refactor plan

The plan file is `REFACTOR_PLAN.md`, made by `scripts/make_refactor_plan.py`. Phases: 1 safety net, 2 quick clean-up, 3 structure, 4 copy-paste, 5 final check.

How to run it:
1. Do one checkbox at a time. Open the file and line it names.
2. Change `- [ ]` to `- [x]` only after the change is made and checked.
3. After each phase, run the tests (or the program) and compare with the Phase 1 result.
4. If a step breaks something, undo only that step. Write `SKIPPED: <reason>` after it.
5. If a step needs a decision (a rename that other people depend on, a risky split), ask the user before doing it.
6. Check where you are with `python3 scripts/make_refactor_plan.py --progress REFACTOR_PLAN.md`.

If you write a plan by hand, copy this layout:

```
# Refactor Plan: <name>
## Phase 1 - Safety net
- [ ] Run the tests (or the program) and save the result
- [ ] Save a restore point (git commit or folder copy)
## Phase 2 - Quick clean-up (low risk)
- [ ] `file:line` - what is wrong - how to fix it
## Phase 3 - Structure (medium risk)
## Phase 4 - Remove copy-paste
## Phase 5 - Final check
- [ ] Run the tests again and compare with Phase 1
```

#!/usr/bin/env python3
"""
make_refactor_plan.py - scans code and writes a step-by-step refactor plan.

What it does:
  Looks through a project folder (or one file) for things worth cleaning up:
  long functions, deep nesting, too many parameters, bare "except:", big files,
  copy-pasted blocks, TODO notes, very long lines, and console.log leftovers.
  It writes REFACTOR_PLAN.md: a checklist in a safe order (safety net, quick
  clean-up, structure, copy-paste, final check). Python files are checked in
  detail. Other languages get simpler checks.

How to run:
  python3 scripts/make_refactor_plan.py my-project --out REFACTOR_PLAN.md
  python3 scripts/make_refactor_plan.py --progress REFACTOR_PLAN.md

Options:
  --out       plan file to write (default: REFACTOR_PLAN.md in the project folder)
  --progress  do not scan; count the ticked boxes in an existing plan

Exit code: 0 = plan written (or plan complete with --progress),
           1 = no code found (or plan not complete with --progress), 2 = path not found.
Uses only the Python standard library.
"""
import argparse
import ast
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

SKIP = {"node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build",
        "target", ".idea", ".vscode", "tests", "test", "vendor"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb", ".php", ".c", ".cpp", ".cs"}
LONG_FUNC = 30
MAX_NEST = 3
MAX_PARAMS = 5
BIG_FILE = 300
LONG_LINE = 120
DUP_WINDOW = 6
CAP = 12
NEST = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)


def depth(node, d=0):
    best = d
    for child in ast.iter_child_nodes(node):
        nd = d + 1 if isinstance(child, NEST) else d
        if isinstance(node, ast.If) and isinstance(child, ast.If) and node.orelse == [child]:
            nd = d  # an "elif" is not deeper nesting
        best = max(best, depth(child, nd))
    return best


def python_findings(text, rel):
    out = []
    try:
        tree = ast.parse(text)
    except SyntaxError as err:
        return [("quick", f"`{rel}:{err.lineno or 1}`", "Syntax error. The scanner could not read this file. Fix or skip it.")]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            where = f"`{rel}:{node.lineno}`"
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > LONG_FUNC:
                out.append(("structure", where, f"`{node.name}` is {length} lines long. Split it into small functions with one job each."))
            nest = depth(node)
            if nest > MAX_NEST:
                out.append(("structure", where, f"`{node.name}` is nested {nest} levels deep. Use early `return` or `continue` to flatten it."))
            a = node.args
            names = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs if x.arg not in ("self", "cls")]
            if len(names) > MAX_PARAMS:
                out.append(("structure", where, f"`{node.name}` takes {len(names)} parameters. Group related ones into one object or dictionary."))
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            out.append(("quick", f"`{rel}:{node.lineno}`", "Bare `except:` hides errors. Catch the specific error instead."))
    return out


def text_findings(text, rel, ext):
    out = []
    lines = text.splitlines()
    if len(lines) > BIG_FILE:
        out.append(("structure", f"`{rel}`", f"File is {len(lines)} lines. Look for parts that can move to their own file."))
    for n, line in enumerate(lines, 1):
        if re.search(r"\b(TODO|FIXME|HACK)\b", line):
            out.append(("quick", f"`{rel}:{n}`", "TODO/FIXME note. Do it, delete it, or move it to the issue list."))
    long_count = sum(1 for ln in lines if len(ln) > LONG_LINE)
    if long_count:
        out.append(("quick", f"`{rel}`", f"{long_count} lines are longer than {LONG_LINE} characters. Break them up."))
    if ext in (".js", ".jsx", ".ts", ".tsx"):
        logs = [n for n, ln in enumerate(lines, 1) if "console.log" in ln]
        if logs:
            out.append(("quick", f"`{rel}:{logs[0]}`", f"{len(logs)} `console.log` call(s). Remove leftovers used for debugging."))
    return out


def duplicate_findings(files):
    seen = defaultdict(list)
    for rel, text in files:
        lines = [(n, ln.strip()) for n, ln in enumerate(text.splitlines(), 1)]
        lines = [(n, s) for n, s in lines if s and not s.startswith(("#", "//", "import", "from", "}", ")", "]"))]
        for i in range(len(lines) - DUP_WINDOW + 1):
            window = lines[i:i + DUP_WINDOW]
            if sum(len(s) for _, s in window) < 80:
                continue
            key = hashlib.md5("\n".join(s for _, s in window).encode()).hexdigest()
            seen[key].append((rel, window[0][0]))
    out, used = [], set()
    for places in seen.values():
        if len(places) < 2:
            continue
        spots = []
        for rel, n in places:
            if all(not (rel == r and abs(n - m) < DUP_WINDOW) for r, m in spots):
                spots.append((rel, n))
        if len(spots) >= 2 and not any(s in used for s in spots):
            used.update(spots)
            where = " and ".join(f"`{r}:{n}`" for r, n in spots[:3])
            out.append(("duplicates", where, f"Same {DUP_WINDOW}+ lines appear in {len(spots)} places. Move them into one function and call it."))
    return out


def collect(target):
    if target.is_file():
        return [target], target.parent
    files = []
    for p in sorted(target.rglob("*")):
        parts = set(p.relative_to(target).parts[:-1])
        if p.is_file() and p.suffix.lower() in CODE_EXT and not (parts & SKIP) and not any(x.startswith(".") for x in parts):
            files.append(p)
    return files, target


def section(title, findings, empty_text):
    out = [f"## {title}", ""]
    if not findings:
        return out + [empty_text, ""]
    for _, where, text in findings[:CAP]:
        out.append(f"- [ ] {where} - {text}")
    if len(findings) > CAP:
        out.append(f"- [ ] ...and {len(findings) - CAP} more like these. Re-run the scanner after this plan is done.")
    return out + [""]


def render(name, count, findings):
    by = defaultdict(list)
    for f in findings:
        by[f[0]].append(f)
    out = [f"# Refactor Plan: {name}", "",
           f"Scanned {count} code file(s). Tick each box (`- [x]`) when the step is done.", "",
           "Rules: same behavior after every step, one step at a time, run the tests after each phase.", "",
           "## Phase 1 - Safety net", "",
           "- [ ] Run the tests (or run the program once) and save the result to compare later.",
           "- [ ] Save a restore point (a git commit, or a copy of the folder).", ""]
    out += section("Phase 2 - Quick clean-up (low risk)", by["quick"], "Nothing found. Look for unclear names by hand.")
    out += section("Phase 3 - Structure (medium risk)", by["structure"], "Nothing found. The code is already well split.")
    out += section("Phase 4 - Remove copy-paste", by["duplicates"], "No copied blocks found.")
    out += ["## Phase 5 - Final check", "",
            "- [ ] Run the tests (or the program) again. The result must match Phase 1.",
            "- [ ] Re-write the run guide: `python3 scripts/make_run_guide.py . --out HOW_TO_RUN.txt`",
            "- [ ] Write the change report (template in `references/refactor-rules.md`).", ""]
    return "\n".join(out)


def show_progress(path):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    done = len(re.findall(r"^- \[[xX]\]", text, re.M))
    todo = len(re.findall(r"^- \[ \]", text, re.M))
    print(f"Done {done} of {done + todo} steps. Left: {todo}.")
    return 0 if todo == 0 and done else 1


def main():
    ap = argparse.ArgumentParser(description="Write a step-by-step refactor plan.")
    ap.add_argument("path", nargs="?", help="project folder or one code file")
    ap.add_argument("--out", help="plan file to write")
    ap.add_argument("--progress", metavar="PLAN", help="count ticked boxes in a plan file")
    args = ap.parse_args()

    if args.progress:
        if not Path(args.progress).exists():
            print(f"Plan not found: {args.progress}")
            return 2
        return show_progress(args.progress)
    if not args.path:
        ap.error("give a project folder or file (or use --progress PLAN)")
    target = Path(args.path).resolve()
    if not target.exists():
        print(f"Path not found: {args.path}")
        return 2

    files, base = collect(target)
    if not files:
        print("No code files found. Write the plan by hand (see references/refactor-rules.md).")
        return 1

    findings, contents = [], []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        rel = str(f.relative_to(base))
        contents.append((rel, text))
        if f.suffix.lower() == ".py":
            findings += python_findings(text, rel)
        findings += text_findings(text, rel, f.suffix.lower())
    findings += duplicate_findings(contents)

    plan = render(target.name, len(files), findings)
    out = Path(args.out) if args.out else base / "REFACTOR_PLAN.md"
    out.write_text(plan, encoding="utf-8")
    print(plan)
    print(f"Saved to: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

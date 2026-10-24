#!/usr/bin/env python3
"""
quality_report.py - checks a project and suggests how to improve its quality.

What it does:
  Runs simple checks and prints what is good, what to fix, and the top 3 things
  to do first. Two groups:
    CODE QUALITY    - possible secrets in code, eval/exec, mutable default
                      arguments, shell=True, missing docstrings and type hints
                      (Python), missing linter or formatter setup.
    PRODUCT QUALITY - README (install steps, demo), LICENSE, tests, CI, .gitignore,
                      dependency list, lock file, .env.example, CONTRIBUTING.
  It never prints the value of a possible secret, only the file and line.

How to run:
  python3 scripts/quality_report.py my-project --out QUALITY_REPORT.md
  python3 scripts/quality_report.py my-project

Options:
  --out   also save the report to this file

Exit code: 0 = report written, 1 = no code found, 2 = path not found.
Uses only the Python standard library.
"""
import argparse
import ast
import os
import re
import sys
from pathlib import Path

HEAVY = {"node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build", "target", ".idea", ".vscode", "vendor"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb", ".php", ".c", ".cpp", ".cs"}
TEST_DIRS = {"tests", "test", "__tests__", "spec"}
SEV = {"high": 0, "medium": 1, "low": 2}
SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*[\"'][^\"']{8,}[\"']")
FAKE_WORDS = ("example", "your_", "your-", "changeme", "xxxx", "<", "placeholder", "dummy", "test")
KEY_RES = [re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")]


def walk(base):
    paths = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in HEAVY and not d.startswith(".git")]
        for f in files:
            paths.append(Path(root) / f)
    return paths


def is_test_path(rel):
    name = rel.name.lower()
    return (set(rel.parts[:-1]) & TEST_DIRS or name.startswith("test_") or name.endswith(("_test.py", ".test.js", ".test.ts",
            ".spec.js", ".spec.ts", ".test.jsx", ".test.tsx", "_test.go")))


def where(items, limit=4):
    shown = ", ".join(f"`{i}`" for i in items[:limit])
    return shown + (f" and {len(items) - limit} more" if len(items) > limit else "")


def python_checks(py_files, base):
    res = {"secrets": [], "eval": [], "mutable": [], "shell": [], "funcs": 0, "documented": 0, "hinted": 0, "hint_total": 0, "imports": set()}
    for f in py_files:
        rel = f.relative_to(base)
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name) and fn.id in ("eval", "exec"):
                    res["eval"].append(f"{rel}:{node.lineno}")
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        res["shell"].append(f"{rel}:{node.lineno}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(isinstance(d, (ast.List, ast.Dict, ast.Set)) for d in node.args.defaults + [d for d in node.args.kw_defaults if d]):
                    res["mutable"].append(f"{rel}:{node.lineno}")
                if not node.name.startswith("_"):
                    res["funcs"] += 1
                    res["documented"] += 1 if ast.get_docstring(node) else 0
                res["hint_total"] += 1
                a = node.args
                if node.returns is not None or any(x.annotation for x in a.args + a.kwonlyargs + a.posonlyargs):
                    res["hinted"] += 1
            elif isinstance(node, ast.Import):
                res["imports"].update(n.name.split(".")[0] for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                res["imports"].add(node.module.split(".")[0])
    return res


def main():
    ap = argparse.ArgumentParser(description="Suggest ways to improve code and product quality.")
    ap.add_argument("path", help="project folder")
    ap.add_argument("--out", help="also save the report to this file")
    args = ap.parse_args()

    base = Path(args.path).resolve()
    if not base.exists():
        print(f"Path not found: {args.path}")
        return 2
    if base.is_file():
        base = base.parent

    paths = walk(base)
    names = {p.name.lower() for p in paths if p.parent == base}
    code = [p for p in paths if p.suffix.lower() in CODE_EXT and not is_test_path(p.relative_to(base))]
    if not code:
        print("No code files found.")
        return 1
    py = [p for p in code if p.suffix == ".py"]
    texts = {}
    for p in code:
        texts[p] = p.read_text(encoding="utf-8", errors="ignore")

    results = []  # (area, severity, ok, good_text, bad_text)

    def add(area, sev, ok, good, bad):
        results.append((area, sev, ok, good, bad))

    # ---------- CODE QUALITY ----------
    secrets = []
    for p, text in texts.items():
        for n, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            hit = (SECRET_RE.search(line) and not any(w in low for w in FAKE_WORDS)) or any(r.search(line) for r in KEY_RES)
            if hit:
                secrets.append(f"{p.relative_to(base)}:{n}")
    add("code", "high", not secrets, "No passwords or keys found in the code.",
        f"Possible secret in code at {where(secrets)}. Move it to an environment variable, remove it from git history, and change the key.")

    pyres = python_checks(py, base) if py else None
    if pyres:
        add("code", "high", not pyres["eval"], "No `eval` or `exec` calls.",
            f"`eval`/`exec` at {where(pyres['eval'])}. They run any text as code. Use a safe parser or a lookup table.")
        add("code", "medium", not pyres["shell"], "No `shell=True` calls.",
            f"`shell=True` at {where(pyres['shell'])}. Pass the command as a list instead so input cannot inject commands.")
        add("code", "medium", not pyres["mutable"], "No mutable default arguments.",
            f"Mutable default argument (list/dict/set) at {where(pyres['mutable'])}. Use `None` and create the value inside the function.")
        if pyres["funcs"]:
            doc = pyres["documented"] / pyres["funcs"]
            add("code", "medium", doc >= 0.5, f"{round(doc * 100)}% of public functions have docstrings.",
                f"Only {round(doc * 100)}% of public functions have docstrings. Add a one-line docstring saying what each does.")
        if pyres["hint_total"]:
            hint = pyres["hinted"] / pyres["hint_total"]
            add("code", "low", hint >= 0.5, f"{round(hint * 100)}% of functions have type hints.",
                f"Only {round(hint * 100)}% of functions have type hints. Add hints to function inputs and outputs so tools catch mistakes.")

    pyproject = (base / "pyproject.toml").read_text(errors="ignore") if (base / "pyproject.toml").exists() else ""
    pkgjson = (base / "package.json").read_text(errors="ignore") if (base / "package.json").exists() else ""
    lint_names = {".flake8", ".pylintrc", "ruff.toml", ".ruff.toml", "biome.json", ".golangci.yml", "rustfmt.toml", ".prettierrc"}
    has_lint = (names & lint_names or any(n.startswith((".eslintrc", "eslint.config", ".prettierrc")) for n in names)
                or any(t in pyproject for t in ("[tool.ruff", "[tool.black", "[tool.flake8", "[tool.pylint"))
                or "eslint" in pkgjson)
    add("code", "medium", bool(has_lint), "A linter or formatter is set up.",
        "No linter or formatter found. Add one (Ruff for Python, ESLint and Prettier for JavaScript) so style problems are caught automatically.")

    # ---------- PRODUCT QUALITY ----------
    readme_name = next((n for n in ("readme.md", "readme", "readme.rst", "readme.txt") if n in names), None)
    add("product", "high", bool(readme_name), "A README exists.",
        "No README. Add one that says what the project does, how to install it, and how to use it.")
    if readme_name:
        rt = (base / next(p.name for p in paths if p.parent == base and p.name.lower() == readme_name)).read_text(errors="ignore")
        rl = rt.lower()
        add("product", "high", any(k in rl for k in ("install", "getting started", "usage", "how to run", "quick start")),
            "README explains how to install or use it.", "README has no install or usage steps. Add the exact commands a new person should type.")
        add("product", "medium", ("![" in rt or "demo" in rl or "screenshot" in rl),
            "README shows a demo or screenshot.", "README has no screenshot, GIF, or demo link. A picture helps people understand it in 5 seconds.")
        add("product", "low", len(rt.splitlines()) >= 15, "README has a good amount of detail.",
            "README is very short. Add examples, limits, and how to get help.")

    add("product", "medium", any(n.startswith(("license", "licence", "copying")) for n in names), "A LICENSE file exists.",
        "No LICENSE. Without one, others are not allowed to use or change your code. MIT is a simple choice.")
    has_tests = any(is_test_path(p.relative_to(base)) and p.suffix.lower() in CODE_EXT for p in paths)
    add("product", "high", has_tests, "Tests exist.",
        "No tests found. Add tests for the 3 most important functions first. Tests make later changes safe.")
    has_ci = (base / ".github" / "workflows").exists() or ".gitlab-ci.yml" in names
    add("product", "medium", has_ci, "Automatic checks (CI) are set up.",
        "No CI found. Add a GitHub Actions file that runs your tests on every push.")
    add("product", "medium", ".gitignore" in names, "A .gitignore exists.",
        "No .gitignore. Add one so junk files, secrets, and installed packages are not committed.")

    uses_env = any(re.search(r"os\.environ|os\.getenv|process\.env|getenv\(", t) for t in texts.values())
    if uses_env:
        add("product", "medium", bool(names & {".env.example", ".env.sample", "example.env"}), "Settings are documented in an example file.",
            "The code reads settings from the environment but there is no `.env.example`. Add one listing each setting name (no real values).")

    if pyres:
        std = getattr(sys, "stdlib_module_names", None)
        if std:
            local = {p.stem for p in code} | {d.name for d in base.iterdir() if d.is_dir()}
            third = sorted(m for m in pyres["imports"] if m not in std and m not in local)
            if third:
                has_dep = bool(names & {"requirements.txt", "pyproject.toml", "pipfile", "setup.py"})
                add("product", "high", has_dep, "Python packages are listed in a dependency file.",
                    f"The code imports outside packages ({', '.join(third[:5])}) but no `requirements.txt` or `pyproject.toml` lists them. Add one so others can install them.")
    if pkgjson:
        add("product", "medium", bool(names & {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"}),
            "A lock file pins package versions.", "No lock file. Commit `package-lock.json` so everyone installs the same versions.")
    add("product", "low", "contributing.md" in names, "CONTRIBUTING.md exists.",
        "No CONTRIBUTING.md. Tell new contributors how to set up, test, and send changes.")

    # ---------- REPORT ----------
    out = [f"# Quality Report: {base.name}", "", f"Scanned {len(code)} code file(s).", ""]
    failed = sorted((r for r in results if not r[2]), key=lambda r: SEV[r[1]])
    for area, title in (("code", "Code quality"), ("product", "Product quality")):
        rows = [r for r in results if r[0] == area]
        passed = sum(1 for r in rows if r[2])
        out += [f"## {title} ({passed} of {len(rows)} checks passed)", ""]
        out += [f"- [{r[1]}] {r[4]}" for r in sorted((r for r in rows if not r[2]), key=lambda r: SEV[r[1]])]
        out += [f"- OK: {r[3]}" for r in rows if r[2]]
        out.append("")
    out += ["## Do these first", ""]
    if failed:
        out += [f"{i}. {r[4]}" for i, r in enumerate(failed[:3], 1)]
    else:
        out.append("Nothing urgent. Nice work.")
    out += ["", "For structure problems (long functions, deep nesting, copy-paste) run `scripts/make_refactor_plan.py`.", ""]

    text = "\n".join(out)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Saved to: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

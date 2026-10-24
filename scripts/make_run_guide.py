#!/usr/bin/env python3
"""
make_run_guide.py - writes a plain-text "how to run this code" file.

What it does:
  Looks at a project folder (or one file), finds what kind of code it is
  (Python, Node.js, Rust, Go, Java, Make, HTML, shell), and writes simple
  steps: what to install, what to type, and what to do if it breaks.
  It looks in the folder and one level of sub-folders. It only guesses from
  file names, so a human should read the result once.

How to run:
  python3 scripts/make_run_guide.py my-project --out HOW_TO_RUN.txt
  python3 scripts/make_run_guide.py script.py

Options:
  --out   file to write (default: HOW_TO_RUN.txt inside the project folder)

Exit code: 0 = guide written, 1 = no project found, 2 = path not found.
Uses only the Python standard library.
"""
import argparse
import json
import sys
from pathlib import Path

SKIP = {"node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build",
        "target", ".idea", ".vscode", "tests", "test"}
PY_ENTRY = ["main.py", "app.py", "run.py", "server.py", "index.py", "__main__.py"]
JS_ENTRY = ["index.js", "main.js", "app.js", "server.js"]
ENV_FILES = [".env.example", ".env.sample", "example.env"]


def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def find_py_entry(folder):
    for name in PY_ENTRY + ["manage.py"]:
        if (folder / name).exists():
            return name
    for f in sorted(folder.glob("*.py")):
        if "__main__" in read(f):
            return f.name
    return None


def env_steps(folder):
    for name in ENV_FILES:
        if (folder / name).exists():
            return [f"Copy the settings file: cp {name} .env  (then open .env and "
                    "type in your own values. Never share this file.)"]
    return []


def part(title, needs, setup, run, notes=None, folder=None):
    return {"title": title, "needs": needs, "steps": setup + (env_steps(folder) if folder else []) + run,
            "notes": notes or []}


def python_part(folder, title):
    markers = ["requirements.txt", "pyproject.toml", "setup.py"]
    if not (any((folder / m).exists() for m in markers) or list(folder.glob("*.py"))):
        return None
    setup = ["Make a private space for the packages: python3 -m venv .venv",
             "Turn it on: source .venv/bin/activate   (Windows: .venv\\Scripts\\activate)"]
    reqs = read(folder / "requirements.txt").lower()
    if (folder / "requirements.txt").exists():
        setup.append("Install the packages: pip install -r requirements.txt")
    elif (folder / "pyproject.toml").exists() or (folder / "setup.py").exists():
        setup.append("Install the project: pip install -e .")
    else:
        setup = []  # a plain script needs no setup
    entry = find_py_entry(folder)
    notes = []
    if entry is None:
        run = ["Find the file that starts the program and run it with: python3 FILE.py"]
        notes.append("No main file was found. Check the README or ask the author.")
    elif entry == "manage.py":
        run = ["Start the website: python manage.py runserver",
               "Open http://127.0.0.1:8000 in your browser."]
    elif "fastapi" in reqs or "uvicorn" in reqs:
        run = [f"Start the server: uvicorn {Path(entry).stem}:app --reload",
               "Open http://127.0.0.1:8000 in your browser."]
        notes.append("If it says it cannot find 'app', change the name after the colon.")
    elif "flask" in reqs:
        run = [f"Start the server: python3 {entry}",
               "Open the address it prints (often http://127.0.0.1:5000)."]
    else:
        run = [f"Run it: python3 {entry}"]
    return part(title, ["Python 3 - get it at python.org"], setup, run, notes, folder)


def node_part(folder, title):
    pkg = folder / "package.json"
    if pkg.exists():
        try:
            data = json.loads(read(pkg))
        except ValueError:
            data = {}
        scripts = data.get("scripts") or {}
        if "start" in scripts:
            run = ["Start it: npm start"]
        elif "dev" in scripts:
            run = ["Start it: npm run dev"]
        elif data.get("main"):
            run = [f"Start it: node {data['main']}"]
        else:
            run = ["No start command found. Look at 'scripts' in package.json."]
        notes = []
        if "test" in scripts:
            notes.append("Run the tests: npm test")
        if "build" in scripts:
            notes.append("Make a final version: npm run build")
        return part(title, ["Node.js (a recent version) - get it at nodejs.org"],
                    ["Install the packages: npm install"], run, notes, folder)
    js = [n for n in JS_ENTRY if (folder / n).exists()] or [f.name for f in sorted(folder.glob("*.js"))[:1]]
    if js:
        return part(title, ["Node.js (a recent version) - get it at nodejs.org"], [],
                    [f"Run it: node {js[0]}"], [], folder)
    return None


def other_parts(folder, title):
    found = []
    if (folder / "Cargo.toml").exists():
        found.append(part(title, ["Rust - get it at rustup.rs"], [], ["Run it: cargo run"], [], folder))
    if (folder / "go.mod").exists():
        found.append(part(title, ["Go - get it at go.dev"], [], ["Run it: go run ."], [], folder))
    if (folder / "pom.xml").exists():
        found.append(part(title, ["Java (JDK) and Maven"], ["Build it: mvn package"],
                          ["Run the .jar file made in the target folder: java -jar target/NAME.jar"],
                          ["Replace NAME with the real file name in the target folder."], folder))
    if (folder / "build.gradle").exists() or (folder / "build.gradle.kts").exists():
        found.append(part(title, ["Java (JDK)"], [], ["Run it: ./gradlew run"], [], folder))
    if (folder / "Makefile").exists():
        found.append(part(title, ["make (comes with most Mac and Linux computers)"], [],
                          ["Build and run it: make"], ["See the Makefile for other commands."], folder))
    if (folder / "index.html").exists():
        found.append(part(title, ["A web browser"], [],
                          ["Double-click index.html, or drag it into your browser."], [], folder))
    sh = sorted(folder.glob("*.sh"))
    if sh and not found:
        found.append(part(title, ["A terminal (bash)"], [], [f"Run it: bash {sh[0].name}"], [], folder))
    return found


def detect_folder(folder, title):
    parts = []
    for p in (node_part(folder, title), python_part(folder, title)):
        if p:
            parts.append(p)
    parts.extend(other_parts(folder, title))
    return parts


def detect_file(path):
    ext = path.suffix.lower()
    runners = {".py": ("Python 3 - get it at python.org", f"python3 {path.name}"),
               ".js": ("Node.js - get it at nodejs.org", f"node {path.name}"),
               ".sh": ("A terminal (bash)", f"bash {path.name}"),
               ".rb": ("Ruby - get it at ruby-lang.org", f"ruby {path.name}"),
               ".php": ("PHP - get it at php.net", f"php {path.name}")}
    if ext in runners:
        needs, cmd = runners[ext]
        return [part(path.name, [needs], [], [f"Run it: {cmd}"])]
    if ext == ".html":
        return [part(path.name, ["A web browser"], [], [f"Double-click {path.name} to open it."])]
    return []


def render(name, parts):
    out = [f"HOW TO RUN: {name}",
           "(Written by make_run_guide.py. Please read it once to check it.)", ""]
    for i, p in enumerate(parts, 1):
        if len(parts) > 1:
            out += [f"=== PART {i}: {p['title']} ===", ""]
        out.append("WHAT YOU NEED")
        out += [f"  - {n}" for n in p["needs"]]
        out += ["", "STEPS", "  1. Open a terminal in the project folder."]
        out += [f"  {n}. {s}" for n, s in enumerate(p["steps"], 2)]
        if p["notes"]:
            out += ["", "NOTES"] + [f"  - {n}" for n in p["notes"]]
        out.append("")
    out += ["IF SOMETHING GOES WRONG",
            "  - 'command not found' means a tool is not installed. Install it from the link above.",
            "  - Make sure the terminal is inside the project folder (type: pwd).",
            "  - Read the last 5 lines of the error. They usually name the problem.",
            ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Write a plain-text how-to-run guide.")
    ap.add_argument("path", help="project folder or a single code file")
    ap.add_argument("--out", help="output file (default: HOW_TO_RUN.txt in the project folder)")
    args = ap.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"Path not found: {args.path}")
        return 2

    if target.is_file():
        base, parts = target.parent, detect_file(target)
    else:
        base = target
        parts = detect_folder(base, base.name)
        for sub in sorted(p for p in base.iterdir() if p.is_dir() and p.name not in SKIP and not p.name.startswith(".")):
            for p in detect_folder(sub, f"{sub.name}/"):
                p["steps"].insert(0, f"Go into the folder: cd {sub.name}")
                parts.append(p)

    if not parts:
        print("No project found. Write HOW_TO_RUN.txt by hand.")
        return 1

    text = render(target.name, parts)
    out = Path(args.out) if args.out else base / "HOW_TO_RUN.txt"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"Saved to: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

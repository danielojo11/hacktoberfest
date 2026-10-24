# Explanation Templates

Read this when you explain code. Contents: PLAIN mode (for non-developers), DEV mode (for developers), word swaps, quality check.

## 1. PLAIN mode (non-developers)

Rules: short sentences, no jargon, one everyday comparison. If you must use a technical word, explain it in the same sentence.

Template:
1. **In one sentence:** "This program [does what] so that [why it matters]."
2. **The picture:** one everyday comparison. Example: "Think of it like a cashier who adds up a receipt."
3. **Step by step:** numbered, 3 to 7 steps, in the order the program runs. Each step is one plain sentence.
4. **What goes in, what comes out:** "You give it ___. You get back ___."
5. **Words you may see:** only the 2 or 3 technical words they will meet when running it, each with a short meaning.

Example (for a script that totals paid orders):
> This program adds up the money from all paid orders, including tax.
> Think of it like a cashier who adds up a receipt, but skips unpaid items.
> 1. It opens the list of orders. 2. It skips orders that are not paid. 3. It adds 20% tax to each paid order. 4. It adds everything together and shows the total.
> You give it a list of orders. You get back one number: the total.

## 2. DEV mode (developers)

Rules: be exact and short. Use the real names from the code.

Template:
1. **Purpose:** one sentence.
2. **Flow:** the path from entry point to output, with file and function names (`main.py: run() -> load_orders() -> total_paid_with_tax()`).
3. **Key parts:** the 3 to 5 functions or classes that matter, one line each.
4. **Data:** main inputs, outputs, and where state or files are touched.
5. **Gotchas:** edge cases, hidden assumptions, missing error handling, bugs you saw.

## 3. Word swaps for PLAIN mode

| Technical | Plain |
|-----------|-------|
| function | a small named job |
| variable | a labeled box that holds a value |
| loop | doing the same thing for each item |
| API | a way for programs to talk to each other |
| dependency / package | extra code written by someone else that this project uses |
| terminal / command line | a window where you type commands |
| environment variable | a setting stored outside the code |

## 4. Quality check

- A friend with no coding background could follow PLAIN mode.
- DEV mode names real files and functions.
- Nothing is claimed that you did not see in the code. If unsure, say "it looks like".

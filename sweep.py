"""
Parameter sweep generator
==========================

Runs generate.py once per value of a swept parameter, each into its
own params / STL / preview file, so several variants can be printed
and test-fitted side by side.

Edit GROUP / PARAM / START / STOP / STEP below to sweep a different
parameter or range.

Run:
    python sweep.py [base_params.json]

Output (in this directory):
    params_<tag>.json
    replacement_insert_<tag>.stl
    replacement_insert_<tag>_preview.png

The sweep stops early if a value fails to generate (the error is
printed) - smaller/larger values usually fail the same way, so later
values are skipped rather than run.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
GENERATE = HERE / "generate.py"

BASE_PARAMS_FILE = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else HERE / "params.json"
)

# ------------------------------------------------------------
# Sweep definition
# ------------------------------------------------------------

GROUP = "measured"
PARAM = "INSERT_DEPTH"

START = 4.0
STOP = 0.2      # inclusive; the sweep may stop earlier on failure
STEP = 0.2


def tag_for(value):
    return f"depth_{value:.1f}"


def main():

    with open(BASE_PARAMS_FILE, encoding="utf-8") as file:
        base = json.load(file)

    if GROUP not in base or PARAM not in base[GROUP]:
        sys.exit(f"{BASE_PARAMS_FILE}: {GROUP}.{PARAM} not found")

    results = []
    value = START

    while value >= STOP - 1e-9:

        params = copy.deepcopy(base)
        params[GROUP][PARAM] = round(value, 4)

        tag = tag_for(value)
        stl_name = f"replacement_insert_{tag}.stl"
        preview_name = f"replacement_insert_{tag}_preview.png"
        params_path = HERE / f"params_{tag}.json"

        params["output"]["OUTPUT_FILE"] = stl_name
        params["output"]["PREVIEW_FILE"] = preview_name

        with open(params_path, "w", encoding="utf-8") as file:
            json.dump(params, file, indent=2)
            file.write("\n")

        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(GENERATE), str(params_path)],
            cwd=HERE,
            capture_output=True,
            text=True,
        )

        ok = proc.returncode == 0
        results.append((value, ok, stl_name, params_path.name))

        print(f"{PARAM} = {value:.1f} mm -> {'OK' if ok else 'FAILED'}")

        if not ok:

            print()
            print(f"--- generate.py output for {params_path.name} ---")
            print(proc.stdout[-2000:])
            print(proc.stderr[-2000:])
            print("---")
            print()
            print(
                f"Stopping sweep: {PARAM} = {value:.1f} mm failed. "
                "Smaller values are expected to fail the same way, "
                "so they were not attempted."
            )
            break

        value -= STEP

    print()
    print("=" * 60)
    print("SWEEP SUMMARY")
    print("=" * 60)

    for value, ok, stl_name, params_name in results:

        status = "OK  " if ok else "FAIL"

        print(f"  {value:>5.1f} mm  {status}  {stl_name}  ({params_name})")

    print("=" * 60)


if __name__ == "__main__":
    main()

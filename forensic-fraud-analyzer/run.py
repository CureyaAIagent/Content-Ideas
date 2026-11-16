"""Usage: python run.py inputs.xlsx prices_dir report.xlsx"""
import sys

from ffri.pipeline import run, write_report

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    res = run(sys.argv[1], sys.argv[2])
    write_report(res, sys.argv[3])
    print(res["latest"][["company", "year", "FFRI", "band", "coverage"]].to_string(index=False))

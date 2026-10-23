"""Build and run the slice cocotb test on Icarus for one lane count.

Usage: python runner.py <lanes> <build_dir> [--negative-control]
Seed comes from the SEED environment variable (set by run.sh).
"""
import os
import sys
from pathlib import Path

from cocotb_tools.runner import get_runner

HERE = Path(__file__).resolve().parent


def main():
    lanes = int(sys.argv[1])
    build = Path(sys.argv[2]).resolve()
    neg = "--negative-control" in sys.argv[3:]
    os.environ["LANES"] = str(lanes)
    os.environ["NEG_CONTROL"] = "1" if neg else "0"
    os.environ["SUMMARY_PATH"] = str(build / "summary.json")

    runner = get_runner("icarus")
    runner.build(
        sources=sorted((HERE.parent / "rtl").glob("*.v")),
        hdl_toplevel="slice",
        parameters={"N": lanes},
        build_dir=build / "sim_build",
        always=True,
        timescale=("1ns", "1ps"),
    )
    xml = runner.test(
        hdl_toplevel="slice",
        test_module="test_slice",
        test_dir=HERE,
        build_dir=build / "sim_build",
        results_xml=build / "results.xml",
        seed=int(os.environ["SEED"]),
    )
    print(f"results: {xml}")


if __name__ == "__main__":
    main()

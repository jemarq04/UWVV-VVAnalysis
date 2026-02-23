#!/usr/bin/env python3

import argparse
import glob
import json
import multiprocessing
import os
import subprocess

import tqdm
from UWVV.VVAnalysis import helpers, mergetools


def main():
    """Process merge.py jobs in parallel using multiple cores."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=helpers.CustomHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-q", "--quiet", action="store_true", help="disable all print statements")
    parser.add_argument("-j", "--num-cores", type=int, required=True, help="number of cores to use")
    parser.add_argument(
        "-o", "--outfile", default=argparse.SUPPRESS, help="output file (default: Hists-<ANALYSIS><YEAR>.root)"
    )
    parser.add_argument(
        "--skimmed",
        default=argparse.SUPPRESS,
        help="skimmed ntuple JSON (default: json/<ANALYSIS>/<YEAR>/skimmed.json)",
    )
    args = parser.parse_args()

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if args.num_cores <= 0:
        parser.error(f"invalid number of cores: {args.num_cores}")
    if "skimmed" in args and not os.path.isfile(args.skimmed):
        parser.error(f"invalid skimmed JSON: {args.skimmed}")

    # Handle defaults
    if "skimmed" not in args:
        args.skimmed = None
    if "outfile" not in args:
        args.outfile = f"Hists-{args.analysis}{args.year}.root"

    # Load JSON information
    if args.skimmed is not None:
        with open(args.skimmed) as infile:
            args.skimmed = json.load(infile)
    else:
        args.skimmed = helpers.load_json(args.analysis, args.year, "skimmed.json")

    # Use multiple cores to call merge.py for each dataset
    with multiprocessing.Pool(processes=args.num_cores) as pool:
        if not args.quiet:
            list(
                tqdm.tqdm(
                    pool.imap_unordered(call_merge, [(args, sample) for sample in args.skimmed]),
                    total=len(args.skimmed),
                )
            )
        else:
            pool.map(call_merge, [(args, sample) for sample in args.skimmed])

    # Combine temporary files
    tempfiles = [f"Hists-{args.analysis}{args.year}_{sample}.root" for sample in args.skimmed]
    outlog = subprocess.DEVNULL if args.quiet else None
    status = subprocess.call(["hadd", "-f", args.outfile] + tempfiles, stdout=outlog, stderr=outlog)
    if status == 0:
        for tempfile in tempfiles:
            os.remove(tempfile)


def call_merge(args: tuple):
    """Unpack tuple of arguments and call merge()."""
    merge(*args)


def merge(args: argparse.Namespace, sample: str):
    """Merge files one dataset at a time with the given inputs."""
    # Determine input files
    infiles = [infile for path in args.skimmed[sample] for infile in glob.iglob(path)]

    # Initialize arguments to pass to merging function
    merge_args = argparse.Namespace(
        analysis=args.analysis,
        year=args.year,
        verbose=False,
        skimmed=None,
        infiles=infiles,
        sample=sample,
        outfile=f"Hists-{args.analysis}{args.year}_{sample}.root",
    )

    # Merge files
    mergetools.merge(merge_args)


if __name__ == "__main__":
    main()

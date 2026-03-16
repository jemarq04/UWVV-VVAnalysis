#!/usr/bin/env python3

import argparse
import os
import subprocess

from UWVV.VVAnalysis import helpers


def main():
    """Resubmit skim.py jobs in HTCondor."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=helpers.CustomHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-g", "--save-gen", action="store_true", help="save gen trees")
    parser.add_argument("--only-data", action="store_true", help="only retry failed data skimming jobs")
    parser.add_argument("-v", "--verbose", action="store_true", help="print more updates during skimming")
    parser.add_argument("-q", "--quiet", action="store_true", help="disable all print statements")
    parser.add_argument("submission_dir", help="job directory in /nfs_scratch/...")
    args = parser.parse_args()

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if not os.path.isdir(args.submission_dir):
        parser.error(f"invalid job directory: {args.submission_dir}")

    # Handle defaults
    if args.quiet:
        args.verbose = False

    # Resubmit skimming for each sample
    samples = [sample for sample in os.listdir(args.submission_dir) if not args.only_data or sample.startswith("data")]
    for sample in samples:
        if args.verbose:
            print(f"Resubmitting jobs for {sample}")
        farmout_path = os.path.join(args.submission_dir, sample, "farmout.sh")
        log_path = os.path.join(args.submission_dir, sample, "log_reskim.txt")
        with open(log_path, "w") as outfile:
            status = subprocess.call(["bash", farmout_path, "resubmit"], stdout=outfile, stderr=outfile)
            if status != 0:
                print(f"ERROR: Jobs for {sample} could not be resubmitted. Check log file: {log_path}")
            elif not args.quiet:
                print(f"Jobs resubmitted to condor for {sample}")


if __name__ == "__main__":
    main()

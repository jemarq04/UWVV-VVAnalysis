#!/usr/bin/env python3

import argparse
import json
import os

from UWVV.VVAnalysis import helpers, mergetools


def main():
    """Merge input files from a certain dataset and fill histograms to one output file."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=helpers.CustomHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument(
        "-o", "--outfile", default=argparse.SUPPRESS, help="output file (default: Hists-<ANALYSIS><YEAR>_<SAMPLE>.root)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print during merging")
    parser.add_argument(
        "--skimmed",
        default=argparse.SUPPRESS,
        help="skimmed ntuple JSON (default: json/<ANALYSIS>/<YEAR>/skimmed.json)",
    )
    parser.add_argument("-i", "--infiles", nargs="+", help="input file(s)")
    parser.add_argument(
        "-s",
        "--sample",
        default=argparse.SUPPRESS,
        required=True,
        help="name of sample to be processed (e.g. qqZZ or data_MuonEG_Run2022C). "
        "if no input files are provided, all filepaths for this sample are used as input",
    )
    args = parser.parse_args()

    # Handle defaults
    if "outfile" not in args:
        args.outfile = f"Hists-{args.analysis}{args.year}_{args.sample}.root"
    if "skimmed" not in args:
        args.skimmed = None

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if args.skimmed is not None and not os.path.isfile(args.skimmed):
        parser.error(f"invalid skimmed JSON: {args.skimmed}")

    # Loading infiles, if needed
    if args.infiles is None:
        # Load JSON information
        if args.skimmed is not None:
            with open(args.skimmed_dir) as infile:
                skimmed = json.load(infile)
        else:
            skimmed = helpers.load_json(args.analysis, args.year, "skimmed.json")

        # Error checking
        if args.sample not in skimmed:
            parser.error(f"invalid sample: {args.sample}")

        # Read input files from JSON
        args.infiles = skimmed[args.sample]

    # Merge
    mergetools.merge(args)


if __name__ == "__main__":
    main()

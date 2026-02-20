#!/usr/bin/env python3

import argparse
import os
import subprocess

import UWVV.VVAnalysis.helpers as helpers
import UWVV.VVAnalysis.skimtools as skimtools


def main():
    """Applies cuts/triggers and additional selections to an input file."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=helpers.CustomHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-t", "--trigger", default="MonteCarlo", help="trigger set to apply")
    parser.add_argument("-o", "--outfile", default=argparse.SUPPRESS, help="output file (default: output<YEAR>.root)")
    parser.add_argument("-g", "--save-gen", action="store_true", help="save gen trees")
    parser.add_argument("-v", "--verbose", action="store_true", help="print during skimming")
    parser.add_argument("--json-dir", default=helpers.JSON_DIR, help="directory for JSON files")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--infiles", nargs="+", help="input file")
    group.add_argument("-I", "--input-file-list", help="file that lists input files, one per line")
    args = parser.parse_args()

    # Handle defaults
    if "outfile" not in args:
        args.outfile = f"output{args.year}.root"

    # Read input file list, if given
    if args.input_file_list is not None:
        if not os.path.isfile(args.input_file_list):
            parser.error(f"invalid file: {args.input_file_list}")
        with open(args.input_file_list) as infile:
            args.infiles = [line.strip() for line in infile if not line.isspace() and not line.startswith("#")]

    # Error checking
    for infile in args.infiles:
        if infile.startswith("root:"):
            status = subprocess.call(
                f"hdfs dfs -ls {infile[infile.find('/store'):]}".split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if status != 0:
                parser.error(f"invalid file: {infile}")
        elif not os.path.isfile(infile.replace("file:", "")):
            parser.error(f"invalid file: {infile}")
    if not os.path.isdir(os.path.join(args.json_dir, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(args.json_dir, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")

    # Load JSON information
    cutinfo = helpers.load_json(args.analysis, args.year, "cuts.json", json_dir=args.json_dir)
    aliases = helpers.load_json(args.analysis, args.year, "aliases.json", json_dir=args.json_dir)
    triggers = helpers.load_json(args.analysis, args.year, "triggers.json", json_dir=args.json_dir)

    # Error check provided trigger
    if args.trigger not in triggers:
        parser.error(f"invalid trigger: {args.trigger}")

    # Call skimming function
    skimtools.skim(args, cutinfo, aliases, triggers)


if __name__ == "__main__":
    main()

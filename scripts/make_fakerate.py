#!/usr/bin/env python3

import argparse
import json
import os

import correctionlib.convert
import correctionlib.schemav2
from UWVV.VVAnalysis import helpers, mergetools


def main():
    """Create fake rate JSON correction file."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=helpers.CustomHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZplusL", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument(
        "-o", "--outfile", default=argparse.SUPPRESS, help="output file (default: FakeRates-<ANALYSIS><YEAR>.json)"
    )
    parser.add_argument("infile", help="input histogram file")
    args = parser.parse_args()

    # Handle defaults
    if "outfile" not in args:
        args.outfile = f"FakeRates-{args.analysis}{args.year}.json"

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if not os.path.isfile(args.infile):
        parser.error(f"invalid input file: {args.infile}")

    # Set configurations based on analysis
    config = mergetools.configure_fakerate(args.analysis)

    # Create correction items for each object
    corr_items = {
        obj: correctionlib.convert.from_uproot_THx(
            f"{args.infile}:{config.group_name}/inclusive/{info['hist_name']}", list(config.inputs), "clamp"
        )
        for obj, info in config.objects.items()
    }

    # Fill in configurations for each correction
    corrections = []
    for obj, corr in corr_items.items():
        corr.name = obj
        corr.description = config.objects[obj]["desc"].format(obj=obj)
        for i, val in enumerate(config.inputs.values()):
            corr.inputs[i].description = val.format(obj=obj)
        corr.output.name = "fake rate"
        corr.output.description = config.out_desc.format(obj=obj)
        corrections.append(corr)

    # Create final correction JSON
    cset = correctionlib.schemav2.CorrectionSet(schema_version=2, corrections=corrections, description=config.desc)

    # Write final output file
    with open(args.outfile, "w") as outfile:
        json.dump(json.loads(cset.json(exclude_unset=True)), outfile, indent=2)


if __name__ == "__main__":
    main()

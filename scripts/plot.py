#!/usr/bin/env python3

import argparse
import os

from UWVV.VVAnalysis import helpers, plotfuncs


def main():
    """Plot histograms from an input histogram file and write plots to a given output directory."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=helpers.CustomHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-o", "--output", default="output", help="name of output directory with plots")
    parser.add_argument("-f", "--force", action="store_true", help="use output dir even if it already exists")
    # parser.add_argument("-v", "--verbose", action="store_true", help="print during plotting")
    parser.add_argument("infile", help="input scaled histogram file with histograms to plot")
    args = parser.parse_args()

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if not os.path.isfile(args.infile):
        parser.error(f"invalid input file: {args.infile}")
    if not args.force and os.path.isdir(args.output):
        parser.error(f"output directory already exists: {args.output}")

    # Make required directories
    paths = [
        args.output,
        os.path.join(args.output, "plots"),
        os.path.join(args.output, "logs"),
        os.path.join(args.output, "channels"),
    ]
    for channel in plotfuncs.get_channels(args.analysis):
        paths.append(os.path.join(args.output, "channels", channel))
        paths.append(os.path.join(args.output, "channels", channel, "plots"))
        paths.append(os.path.join(args.output, "channels", channel, "logs"))
    for path in paths:
        if not os.path.isdir(path):
            os.mkdir(path)

    # Load JSON information
    data = helpers.load_json(args.analysis, args.year, "data.json")
    hist_order = helpers.load_json(args.analysis, args.year, "hist_order.json")

    # Save information
    if data["years"][args.year]["eras"]:
        lumi = sum(erainfo["lumi"] for erainfo in data["years"][args.year]["eras"].values())
    else:
        lumi = data["years"][args.year]["lumi"]
    args.lumi_text = f"{lumi:.2f} fb^{{-1}}"
    args.hist_order = hist_order["order"] if "order" in hist_order else []

    # Plot histograms
    try:
        plotfuncs.plot(args)
    except NotImplementedError as err:
        parser.error(err)


if __name__ == "__main__":
    main()

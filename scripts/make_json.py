#!/usr/bin/env python3

import os
import glob
import json
import argparse
import UWVV.VVAnalysis.helpers as helpers


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-v", "--verbose", action="store_true", help="more print statements")
    parser.add_argument(
        "-o", "--outfile", default=argparse.SUPPRESS, help="output file (default: json/<ANALYSIS>/<YEAR>/<MODE>.json)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-n", "--ntuples", help="directory path that contains the base ntuples (by default, will create ntuples.json)"
    )
    group.add_argument(
        "-s",
        "--skimmed",
        help="directory path that contains the skimmed ntuples (by default, will create skimmed.json)",
    )
    args = parser.parse_args()

    # Handle defaults
    if "outfile" not in args:
        args.outfile = os.path.join(
            helpers.JSON_DIR, args.analysis, args.year, "ntuples.json" if args.ntuples is not None else "skimmed.json"
        )

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")

    # Load JSON information
    streams = [key for key in helpers.load_json(args.analysis, args.year, "triggers.json") if key != "MonteCarlo"]
    montecarlo = helpers.load_json(args.analysis, args.year, "montecarlo.json")
    data = helpers.load_json(args.analysis, args.year, "data.json")

    # Error checking
    if args.year not in data["years"]:
        parser.error(f"information for era {args.year} not in data.json file(s) for analysis {args.analysis}")

    # Find files matching montecarlo information
    result = {}
    for mc_sample, mc_info in montecarlo.items():
        if args.ntuples is not None:
            check_path = os.path.join(args.ntuples, mc_info["dataset"])
            if data["years"][args.year]["eras"]:
                for era, era_info in data["years"][args.year]["eras"].items():
                    check_era_path = os.path.join(check_path, era_info["campaign"])
                    if len(glob.glob(check_era_path)) > 0:
                        result[f"{mc_sample}_{era}"] = [f"{check_era_path}/*/*/*.root"]
                    elif args.verbose:
                        print(f"Skipped {mc_sample}_{era}")
            else:
                if len(glob.glob(check_path)) > 0:
                    result[mc_sample] = [f"{check_path}/*/*/*.root"]
                elif args.verbose:
                    print(f"Skipped {mc_sample}")
        elif data["years"][args.year]["eras"]:
            for era in data["years"][args.year]["eras"]:
                check_path = os.path.join(args.skimmed, f"{mc_sample}_{era}")
                if os.path.isdir(check_path):
                    result[f"{mc_sample}_{era}"] = [f"{check_path}/*.root"]
                elif args.verbose:
                    print(f"Skipped {mc_sample}_{era}")
        else:
            check_path = os.path.join(args.skimmed, mc_sample)
            if os.path.isdir(check_path):
                result[mc_sample] = [f"{check_path}/*.root"]
            elif args.verbose:
                print(f"Skipped {mc_sample}")

    # Find files matching data information
    if args.ntuples is not None:
        for stream in streams:
            check_path = os.path.join(args.ntuples, stream)
            for era in os.listdir(check_path):
                result[f"data_{stream}_{era}"] = [f"{check_path}/{era}/*/*/*.root"]
    else:
        for stream in streams:
            check_path = os.path.join(args.skimmed, f"data_{stream}_Run{args.year}*")
            for data_sample in glob.iglob(check_path):
                result[os.path.basename(data_sample)] = [f"{data_sample}/*.root"]

    # Write out desired output file
    with open(args.outfile, "w") as outfile:
        json.dump(result, outfile, indent=2)
        outfile.write("\n")


if __name__ == "__main__":
    main()

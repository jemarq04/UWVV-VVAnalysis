#!/usr/bin/env python3

import ROOT
import argparse
import os
import UWVV.VVAnalysis.helpers as helpers
import UWVV.VVAnalysis.skimtools as skimtools

# NOTE: Get it working hard-coded and then make it better later!


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-t", "--trigger", default="MonteCarlo", help="trigger set to apply")
    parser.add_argument("-o", "--outfile", default="output.root", help="output file")
    parser.add_argument("infile", help="input file")
    args = parser.parse_args()

    if not os.path.isfile(args.infile):
        parser.error(f"invalid file: {args.infile}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")

    cutinfo = helpers.load_json(args.analysis, args.year, "cuts.json")
    aliases = helpers.load_json(args.analysis, args.year, "aliases.json")
    triggers = helpers.load_json(args.analysis, args.year, "triggers.json")

    if args.trigger not in triggers:
        parser.error(f"invalid trigger: {args.trigger}")

    with ROOT.TFile.Open(args.infile) as infile:
        with ROOT.TFile.Open(args.outfile, "RECREATE") as outfile:
            outfile.cd()
            for channel in ["eeee", "eemm", "mmmm"]:
                cutstring = skimtools.build_cutstring(cutinfo, channel)
                cutstring += f" && ({triggers[args.trigger]})"
                print("cutstring:", cutstring)

                tree = infile.Get(f"{channel}/ntuple")
                for key, val in (aliases["Event"] | aliases["Channel"][channel]).items():
                    if val:
                        tree.SetAlias(key, val)
                skimmed_tree = tree.CopyTree(cutstring)
                skimmed_tree.Process(ROOT.BestZZCandSelector())
                skimmed_tree.Write(f"{channel}/ntuple")


if __name__ == "__main__":
    main()

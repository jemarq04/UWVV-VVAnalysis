#!/usr/bin/env python3

# import ROOT
# import argparse
import os
import UWVV.VVAnalysis.helpers as helpers
import UWVV.VVAnalysis.skimtools as skimtools

# NOTE: Get it working hard-coded and then make it better later!
# maybe get some sort of recipe/makefile that writes down the current directory for easy lookup in these scripts.


def main():
    if "CMSSW_BASE" not in os.environ:
        print("error: CMSSW_BASE not set")
        exit(1)

    dataset = "MonteCarlo"  # or Muon, EGamma, MuonEG, etc.
    analysis = "ZZ4l"
    year = "2022"

    cutinfo = helpers.load_json(analysis, year, "cuts.json")
    aliases = helpers.load_json(analysis, year, "aliases.json")
    triggers = helpers.load_json(analysis, year, "triggers.json")

    for channel in ["eeee", "eemm", "mmmm"]:
        cutstring = skimtools.build_cutstring(cutinfo, channel)
        cutstring += f" && ({triggers[dataset]})"
        print(cutstring)


if __name__ == "__main__":
    main()

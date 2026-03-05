#!/usr/bin/env python3

import argparse
import os

import ROOT
from UWVV.VVAnalysis import helpers, mergetools

# TODO: needs some sort of post-processing before plotting.
#   for ZZ4l,
#       scale MC,
#       combine plot groups together (skip sumweights),
#       ...
#   for ZplusL,
#       scale MC,
#       combine plot groups together (skip sumweights),
#       get combined ele/mu plots,
#       get loose-tight ratios


def main():
    """Combine plot groups, scale MC histograms, and other tasks before plotting."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=helpers.CustomHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-v", "--verbose", action="store_true", help="print debug messages")
    parser.add_argument(
        "-o", "--outfile", default=argparse.SUPPRESS, help="output file (default: ScaledHists-<ANALYSIS><YEAR>.root)"
    )
    parser.add_argument("--no-scale", action="store_true", help="disable MC scaling")
    parser.add_argument("infile", help="input histogram file")
    args = parser.parse_args()

    # Handle defaults
    if "outfile" not in args:
        args.outfile = f"ScaledHists-{args.analysis}{args.year}.root"

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if not os.path.isfile(args.infile):
        parser.error(f"invalid input file: {args.infile}")

    # Load JSON information
    montecarlo = helpers.load_json(args.analysis, args.year, "montecarlo.json")
    data = helpers.load_json(args.analysis, args.year, "data.json")
    groups = helpers.load_json(args.analysis, args.year, "groups.json")

    with ROOT.TFile.Open(args.infile) as infile:
        with ROOT.TFile.Open(args.outfile, "recreate") as outfile:
            channels = mergetools.get_channels(args.analysis)

            # Iterate over each sample
            for in_sample in mergetools.get_children(infile, ROOT.TDirectory):
                mergetools.copy_tdirectory(outfile, in_sample)

                sample_name = in_sample.GetName()
                sample = outfile.Get(sample_name)
                print(f"Processing sample {sample_name}")

                # Scale MC histograms with cross-sections and SFs
                if not args.no_scale and not sample_name.startswith("data_"):
                    if args.verbose:
                        print("  Scaling to data")

                    # Get base cross-section
                    xsec = montecarlo[sample_name]["cross_section"]

                    # Determine k-factor
                    kfactor = montecarlo[sample_name]["k_factor"]

                    # Determine luminosity
                    if data["years"][args.year]["eras"]:
                        lumi = sum(erainfo["lumi"] for erainfo in data["years"][args.year]["eras"].values())

                        # Scale k-factor by the fractional luminosity from the era
                        # (e.g. 2022preEE/2022)
                        for era, erainfo in data["years"][args.year]["eras"].items():
                            if sample_name.endswith(f"_{era}"):
                                kfactor *= erainfo["lumi"] / lumi
                                break
                    else:
                        lumi = data["years"][args.year]["lumi"]

                    # Determine sumweights
                    sumweights_hist = sample.Get("sumweights")
                    sumweights = sumweights_hist.Integral(1, sumweights_hist.GetNbinsX() + 2)

                    # Scale each MC histogram to data by (xsec * lumi)/sumweights
                    for subdir in mergetools.get_children(sample, ROOT.TDirectory):
                        for hist in mergetools.get_children(subdir, ROOT.TH1):
                            hist.Scale(xsec * kfactor * 1000 * lumi / sumweights)

                # TODO: Rebin histograms

                # Combine channels
                if args.verbose:
                    print("  Combining channels")
                total_dir = sample.mkdir("inclusive")
                total_dir.cd()
                for hist in mergetools.get_children(sample.Get(channels[0]), ROOT.TH1):
                    total_hist = hist.Clone()
                    for channel in channels[1:]:
                        total_hist.Add(sample.Get(f"{channel}/{hist.GetName()}"))
                    total_hist.Write()
                sample.cd()

                # Update histograms
                sample.Write("", ROOT.TObject.kOverwrite)

            # Combine MC samples into groups, skipping sumweights
            # (e.g. ggZZ4e, ggZZ4mu, ... into ggZZ, etc.)
            if args.verbose:
                print("==========")
            for group_name, group_info in groups["groups"].items():
                # Initialize dict of combined histograms
                summed_hists = {}

                # Determine list of plot group members
                members = [member for member in group_info["members"] if outfile.Get(member)]

                # Check for sub-era samples (e.g. preEE, postEE, etc.)
                if data["years"][args.year]["eras"]:
                    members = [f"{name}_{subera}" for name in members for subera in data["years"][args.year]["eras"]]

                if members:
                    if args.verbose:
                        print(f"Combining samples into {group_name}")

                    # Iterate over each sample to add to summed_hists
                    for sample_name in members:
                        sample = outfile.Get(sample_name)

                        if args.verbose:
                            print(f"  -> {sample_name}")

                        for subdir in mergetools.get_children(sample, ROOT.TDirectory):
                            subdir_name = subdir.GetName()
                            summed_hists[subdir_name] = ROOT.TList()
                            for hist in mergetools.get_children(subdir, ROOT.TH1):
                                hist_name = hist.GetName()
                                summed_hist = summed_hists[subdir_name].FindObject(hist_name)
                                if summed_hist:
                                    summed_hist.Add(hist)
                                else:
                                    summed_hists[subdir_name].Add(hist.Clone())

                # Write combined histograms to file, if we have any
                if summed_hists:
                    combined_dir = outfile.mkdir(group_name)
                    for key, hists in summed_hists.items():
                        subdir = combined_dir.mkdir(key)
                        subdir.cd()
                        for hist in hists:
                            hist.Write()
            outfile.cd()

            # Combine groups, skipping sumweights
            # (e.g. AllData, AllEWK, AllDY, etc.)
            for combined_group, plot_groups in groups["combined"].items():
                # Initialize dict of combined histograms
                summed_hists = {}

                # Determine list of plot group members
                if combined_group == "AllData":
                    # Check infile to be marginally faster, less keys present in
                    # it compared to outfile
                    members = [key.GetName() for key in infile.GetListOfKeys() if key.GetName().startswith("data_")]
                else:
                    members = [group_name for group_name in plot_groups if outfile.Get(group_name)]

                if members:
                    if args.verbose:
                        print(f"Combining samples into {combined_group}")

                    # Iterate over each sample to add to summed_hists
                    for sample_name in members:
                        sample = outfile.Get(sample_name)

                        if args.verbose:
                            print(f"  -> {sample_name}")

                        for subdir in mergetools.get_children(sample, ROOT.TDirectory):
                            subdir_name = subdir.GetName()
                            summed_hists[subdir_name] = ROOT.TList()
                            for hist in mergetools.get_children(subdir, ROOT.TH1):
                                hist_name = hist.GetName()
                                summed_hist = summed_hists[subdir_name].FindObject(hist_name)
                                if summed_hist:
                                    summed_hist.Add(hist)
                                else:
                                    summed_hists[subdir_name].Add(hist.Clone())

                # Write combined histograms to file, if we have any
                if summed_hists:
                    combined_dir = outfile.mkdir(combined_group)
                    for key, hists in summed_hists.items():
                        subdir = combined_dir.mkdir(key)
                        subdir.cd()
                        for hist in hists:
                            hist.Write()
            outfile.cd()

            # Get DataEWKCorrected (AllData-AllEWK)
            if all(outfile.FindObject(name) for name in ["AllData", "AllEWK"]):
                if args.verbose:
                    print("Correcting data with EWK MC...")
                differences = {}
                for subdir in mergetools.get_children(outfile.Get("AllData"), ROOT.TDirectory):
                    subdir_name = subdir.GetName()
                    differences[subdir_name] = ROOT.TList()
                    for hist in mergetools.get_children(subdir, ROOT.TH1):
                        differences[subdir_name].Add(hist.Clone())
                for subdir in mergetools.get_children(outfile.Get("AllEWK"), ROOT.TDirectory):
                    subdir_name = subdir.GetName()
                    for hist in mergetools.get_children(subdir, ROOT.TH1):
                        differences[subdir_name].FindObject(hist.GetName()).Add(hist, -1)

                differences_dir = outfile.mkdir("DataEWKCorrected")
                for key, hists in differences.items():
                    subdir = differences_dir.mkdir(key)
                    subdir.cd()
                    for hist in hists:
                        hist.Write()

                # Additional step for ZplusL analysis
                if args.analysis == "ZplusL":
                    # For ZplusL (fake rates), create the ratio plots from
                    #  tight vs. loose histograms and write to the 'inclusive' directory.
                    total_dir = outfile.Get("DataEWKCorrected/inclusive")
                    total_dir.cd()
                    for hist in mergetools.get_children(total_dir, ROOT.TH1):
                        if "tight" not in hist.GetName():
                            continue
                        ratio_hist = hist.Clone(hist.GetName().replace("tight", "ratio"))
                        if not ratio_hist.GetSumw2():
                            ratio_hist.Sumw2()
                        ratio_hist.Divide(total_dir.Get(hist.GetName().replace("tight", "loose")))
                        ratio_hist.Write()
                    outfile.cd()

    print("Done.")


if __name__ == "__main__":
    main()

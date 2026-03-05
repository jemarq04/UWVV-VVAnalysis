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
                if args.verbose:
                    print(f"Processing sample {sample_name}")

                # Scale MC histograms with cross-sections and SFs
                if not args.no_scale and not sample_name.startswith("data_"):
                    if args.verbose:
                        print("  Scaling to data")

                    if data["years"][args.year]["eras"]:
                        for key in data["years"][args.year]["eras"]:
                            if sample_name.endswith(f"_{key}"):
                                era = key
                                break
                        else:
                            parser.error(f"could not find era for sample: {sample_name}")
                        base_sample_name = sample_name.replace(f"_{era}", "")

                        # Get base cross-section
                        xsec = montecarlo[base_sample_name]["cross_section"]

                        # Determine k-factor
                        kfactor = montecarlo[base_sample_name]["k_factor"]

                        # Determine luminosity
                        lumi = sum(erainfo["lumi"] for erainfo in data["years"][args.year]["eras"].values())

                        # Scale k-factor by the fractional luminosity from the era
                        # (e.g. 2022preEE/2022)
                        kfactor *= data["years"][args.year]["eras"][era]["lumi"] / lumi
                    else:
                        # Get base cross-section
                        xsec = montecarlo[sample_name]["cross_section"]

                        # Determine k-factor
                        kfactor = montecarlo[sample_name]["k_factor"]

                        # Determine luminosity
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
                # Determine list of plot group members
                members = group_info["members"]

                # Check for sub-era samples (e.g. preEE, postEE, etc.)
                if data["years"][args.year]["eras"]:
                    members = [
                        f"{member}_{subera}" for member in members for subera in data["years"][args.year]["eras"]
                    ]

                # Check that the samples exist in the file
                members = [member for member in members if outfile.Get(member)]

                if members:
                    if args.verbose:
                        print(f"Combining samples into {group_name}")
                        for sample_name in members:
                            print(f"  -> {sample_name}")

                    # Create and write summed histograms
                    mergetools.write_summed_hists(outfile, group_name, members)

            # Combine groups, skipping sumweights
            # (e.g. AllData, AllEWK, AllDY, etc.)
            for combined_group, plot_groups in groups["combined"].items():
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
                        for sample_name in members:
                            print(f"  -> {sample_name}")

                    # Create and write summed histograms
                    mergetools.write_summed_hists(outfile, combined_group, members)

            # Get DataEWKCorrected (AllData-AllEWK)
            if all(outfile.FindObject(name) for name in ["AllData", "AllEWK"]):
                if args.verbose:
                    print("Correcting data with EWK MC")
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

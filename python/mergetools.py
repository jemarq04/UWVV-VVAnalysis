import argparse
import os
import subprocess

import ROOT


def merge(args: argparse.Namespace):
    """Merge input files and fill histograms to one output file.

    Parameters
    ----------
    args : argparse.Namespace
        A dict-like object parsed from the command-line containing information about
        the job. Contains analysis, year, outfile, etc. Check merge.py to see
        full list.

    """
    # Merging input files and saving histograms for each channel
    tempfiles = []
    for channel in get_channels(args.analysis):
        if args.verbose:
            print(f"{channel}:")
            print("  Adding files...")

        # Initialize tree
        tree = ROOT.TChain(f"{channel}/ntuple")
        for infile in args.infiles:
            tree.Add(infile)

        # Get selector to process events
        outfile = args.outfile.replace(".root", f"_{channel}.root")
        selector = get_selector(args.analysis, channel, args.sample, outfile)

        # Apply selector
        if args.verbose:
            print("  Applying selector...")
        tree.Process(selector)

        # Track temporary output file
        if args.verbose:
            print(f"  Written to temporary file: {outfile}")
        tempfiles.append(outfile)

    # Combine each of the channel files to one file for the sample.
    if args.verbose:
        print(f"\nCombining temporary files to {args.outfile}")
    outlog = None if args.verbose else subprocess.DEVNULL
    status = subprocess.call(["hadd", "-f", args.outfile] + tempfiles, stdout=outlog, stderr=outlog)
    if status == 0:
        for tempfile in tempfiles:
            os.remove(tempfile)

    # Add sumweights
    tree = ROOT.TChain("metaInfo/metaInfo")
    for infile in args.infiles:
        tree.Add(infile)
    oldBatch = ROOT.gROOT.IsBatch()
    ROOT.gROOT.SetBatch(True)
    canvas = ROOT.TCanvas("c", "Canvas")
    with ROOT.TFile.Open(args.outfile, "update") as tempfile:
        tempfile.Get(args.sample).cd()
        sumweights = ROOT.TH1D("sumweights", "sumweights", 1, 0, 2000)
        tree.Draw("summedWeights>>sumweights")
        sumweights.Write()
    canvas.Close()
    ROOT.gROOT.SetBatch(oldBatch)


def get_channels(analysis: str) -> list:
    """Determine list of channels to process/merge for a given analysis.

    Note that this is not the same function used for skimming. This is split
    because the channels may differ between skimming and merging. For example,
    ZZ4l skims [eeee, eemm, mmmm], but when it is processed eemm is split into
    eemm and mmee, depending on which lepton pair is the primary Z candidate.

    Parameters
    ----------
    analysis : str
        The analysis with the desired channels.

    Returns
    -------
    list of str
        The list of channels for a given analysis.

    """
    channels = []
    if analysis == "ZZ4l":
        channels = ["eeee", "eemm", "mmee", "mmmm"]
    elif analysis == "ZplusL":
        channels = ["eee", "eem", "emm", "mmm"]
    else:
        # NOTE: If needed, add more analyses here!
        raise NotImplementedError(f"no channels found for analysis {analysis}")
    return channels


def get_selector(analysis: str, channel: str, sample: str, outfile: str) -> ROOT.TSelector:
    """Get selector appropriate for the given analysis to fill histograms.

    Parameters
    ----------
    analysis : str
        The analysis to check for a selector (e.g. ZZ4l).
    channel : str
        The channel to be processed (e.g. eeee or eemm).
    sample : str
        The sample name to be processed (e.g. qqZZ or ggHZZ_preBPix)
    outfile : str
        The name of the output file path to pass to the selector

    Returns
    -------
    ROOT.TSelector
        A TSelector object loaded with the appropriate inputs depending on
        the given analysis and channel.

    """
    # Build counts of objects and the list of object names
    # i.e. {"e": 2, "m": 2} -> ["e1", "e2", "m1", "m2"]
    # (These are built slightly differently than in build_cutstring())
    object_counts = {}
    for obj in channel:
        if obj in object_counts:
            object_counts[obj] += 1
        else:
            object_counts[obj] = 1

    object_names = []
    for obj, count in object_counts.items():
        object_names += [f"{obj}{i}" if count != 1 else obj for i in range(1, count + 1)]

    # Build selector depending on analysis
    if analysis == "ZplusL":
        selector = ROOT.ZplusLFakeRateSelector()
        inputs = ROOT.TList()
        inputs.Add(ROOT.TNamed("name", sample))
        inputs.Add(ROOT.TNamed("channel", channel))
        inputs.Add(ROOT.TNamed("output", outfile))
        inputs.Add(ROOT.TNamed("l1Tight", f"{object_names[0]}ZZTightID"))
        inputs.Add(ROOT.TNamed("l2Tight", f"{object_names[1]}ZZTightID"))
        inputs.Add(ROOT.TNamed("l3Tight", f"{object_names[2]}ZZTightID"))
        inputs.Add(ROOT.TNamed("l1Iso", f"{object_names[0]}ZZIsoPass"))
        inputs.Add(ROOT.TNamed("l2Iso", f"{object_names[1]}ZZIsoPass"))
        inputs.Add(ROOT.TNamed("l3Iso", f"{object_names[2]}ZZIsoPass"))
        inputs.Add(ROOT.TNamed("l3Pt", f"{object_names[2]}Pt"))
        inputs.Add(ROOT.TNamed("l3Eta", f"{object_names[2]}Eta"))
        inputs.Add(ROOT.TNamed("l3MtToMET", f"{object_names[2]}MtToMET"))
        for obj, count in object_counts.items():
            if count >= 2:
                inputs.Add(ROOT.TNamed("Z1Mass", f"{obj}1_{obj}2_Mass"))
        selector.SetInputList(inputs)
    else:
        # NOTE: If needed, add more analyses here!
        raise NotImplementedError(f"no selector available for analysis: {analysis}")

    return selector

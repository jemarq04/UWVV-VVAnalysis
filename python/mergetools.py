import argparse
import os
import subprocess
from typing import Iterator, Optional, Type

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

    # Final additions
    with ROOT.TFile.Open(args.outfile, "update") as tempfile:
        # Get meta tree
        tree = ROOT.TChain("metaInfo/metaInfo")
        for infile in args.infiles:
            tree.Add(infile)

        # Create canvas
        oldBatch = ROOT.gROOT.IsBatch()
        ROOT.gROOT.SetBatch(True)
        canvas = ROOT.TCanvas("c", "Canvas")

        # Create sumweights histogram
        tempfile.Get(args.sample).cd()
        sumweights = ROOT.TH1D("sumweights", "sumweights", 1, 0, 2000)
        tree.Draw("1>>sumweights", "summedWeights")
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
        inputs.Add(ROOT.TNamed("l3Tight", f"{object_names[2]}ZZTightID"))
        inputs.Add(ROOT.TNamed("l3Iso", f"{object_names[2]}ZZIsoPass"))
        inputs.Add(ROOT.TNamed("l3Pt", f"{object_names[2]}Pt"))
        inputs.Add(ROOT.TNamed("l3Eta", f"{object_names[2]}Eta"))
        selector.SetInputList(inputs)
    else:
        # NOTE: If needed, add more analyses here!
        raise NotImplementedError(f"no selector available for analysis: {analysis}")

    return selector


def get_children(tdir: ROOT.TDirectory, type_: Optional[Type[ROOT.TObject]] = None) -> Iterator[ROOT.TObject]:
    """Return generator for TObjects within a TDirectory.

    Parameters
    ----------
    tdir : ROOT.TDirectory
        The TDirectory to loop through and whose children are returned.
    type_ : Type[ROOT.TObject] or None
        A class object to check against the children in the TDirectory. If the object
        inherits from the class object provided, it is returned. If set to None, all objects
        are returned regardless of type. (default is None)

    Returns
    -------
    Iterator[ROOT.TObject]
        A generator that returns the children of the provided TDirectory.

    """
    for key in tdir.GetListOfKeys():
        item = tdir.Get(key.GetName())
        if type_ is None or isinstance(item, type_):
            yield item


def copy_tdirectory(dest: ROOT.TDirectory, src: ROOT.TDirectory):
    """Recursively copy TDirectory to a new destination.

    Parameters
    ----------
    dest : ROOT.TDirectory
        The TDirectory that 'src' will be copied into.
    src : ROOT.TDirectory
        The TDirectory that will be copied recursively.

    """
    src_name = src.GetName()
    if not dest.FindObject(src_name):
        dest.mkdir(src_name)
    dest_dir = dest.Get(src_name)

    for item in get_children(src):
        if isinstance(item, ROOT.TDirectory):
            copy_tdirectory(dest_dir, item)
        else:
            dest_dir.WriteObject(item, item.GetName())


def write_summed_hists(infile: ROOT.TDirectory, name: str, members: list):
    """Create and write summed histograms from input directory and list of directories.

    This function expects the input directory (usually a file) with the following structure.
    It must contain directories with the names provided in the 'members' variable, and those
    must contain subdirectories of histograms to be combined. All these histograms will be
    combined, retaining the subdirectory hierarchy, and will be written out to a new directory
    with the name provided.

    Parameters
    ----------
    infile : ROOT.TDirectory
        The input directory (or file) to with histograms to read/write.
    name: str
        The name of the output directory to be written to the input directory.
    members: list of str
        The list of directories within the input directory to find histograms.

    """
    summed_hists = {}

    # Skip process if there is only one member, and it shares
    # the same name as the combined group
    if len(members) == 1 and name == members[0]:
        return

    # Iterate over each sample to add to summed_hists
    for sample_name in members:
        sample = infile.Get(sample_name)

        for subdir in get_children(sample, ROOT.TDirectory):
            subdir_name = subdir.GetName()
            if subdir_name not in summed_hists:
                summed_hists[subdir_name] = ROOT.TList()
            for hist in get_children(subdir, ROOT.TH1):
                hist_name = hist.GetName()
                summed_hist = summed_hists[subdir_name].FindObject(hist_name)
                if summed_hist:
                    summed_hist.Add(hist)
                else:
                    summed_hists[subdir_name].Add(hist.Clone())

    # Write combined histograms to file, if we have any
    if summed_hists:
        combined_dir = infile.mkdir(name)
        for key, hists in summed_hists.items():
            subdir = combined_dir.mkdir(key)
            subdir.cd()
            for hist in hists:
                hist.Write()
    infile.cd()


def preplot_analysis(analysis: str, outfile: ROOT.TFile):
    """Process any final tasks to output file to prepare for plotting.

    Parameters
    ----------
    analysis : str
        The analysis to use for pre-plotting (e.g. ZZ4l).
    outfile : ROOT.TFile
        The output file (with write permissions) to prepare for plotting.

    """
    if analysis == "ZplusL":
        # For ZplusL (fake rates), create the ratio plots from
        #  tight vs. loose histograms and write to the 'inclusive' directory.
        total_dir = outfile.Get("DataEWKCorrected/inclusive")
        total_dir.cd()
        for hist in get_children(total_dir, ROOT.TH1):
            if "tight" not in hist.GetName():
                continue
            ratio_hist = hist.Clone(hist.GetName().replace("tight", "ratio"))
            if not ratio_hist.GetSumw2():
                ratio_hist.Sumw2()
            ratio_hist.Divide(total_dir.Get(hist.GetName().replace("tight", "loose")))
            ratio_hist.Write()
        outfile.cd()
    else:
        # NOTE: If needed, add more analyses here!
        pass


def configure_fakerate(analysis: str) -> argparse.Namespace:
    """Provide configuration settings for fake rate JSON correction file.

    Parameters
    ----------
    analysis : str
        The analysis to use for determining the appropriate settings (e.g. ZZ4l).

    Returns
    -------
    argparse.Namespace
        The settings for the fake rate JSON correction file. Returned in an
        argparse.Namespace object as it is just a fancy wrapper for a dict object.

    """
    result = argparse.Namespace()

    if analysis == "ZplusL":
        result.group_name = "DataEWKCorrected"
        result.inputs = {
            "pt": "{obj} pT [GeV]",
            "eta": "{obj} eta",
        }
        result.desc = "ZplusL fake rates for electrons and muons, made for ZZ4l analysis"
        result.out_desc = "ZplusL fake rate"
        result.objects = {
            "electron": {"hist_name": "ratioElePtEta", "desc": "ZplusL {obj} fake rate"},
            "muon": {"hist_name": "ratioMuPtEta", "desc": "ZplusL {obj} fake rate"},
        }
    else:
        # NOTE: If needed, add more analyses here!
        raise NotImplementedError(f"no fake rate configuration found for {analysis}")

    return result

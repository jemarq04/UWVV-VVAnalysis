import argparse
import itertools
from typing import Optional

import ROOT
import UWVV.VVAnalysis.helpers as helpers


def skim(args: argparse.Namespace, cutinfo: dict, aliases: dict, triggers: dict):
    """Apply cuts and optional selector to input file.

    Parameters
    ----------
    args : argparse.Namespace
        A dict-like object parsed from the command-line containing information about
        the job. Contains analysis, year, trigger, outfile, etc. Check skim.py to see
        full list.
    cutinfo : dict
        A dict containing all the relevant cuts to be applied.
    aliases : dict
        A dict containing all the aliases to be set for the input trees.
    triggers : dict
        A dict containing the trigger selections for MonteCarlo and each data stream.
    """
    # Create output ROOT file
    with ROOT.TFile.Open(args.outfile, "RECREATE") as outfile:
        if args.verbose:
            print(f"Writing to {args.outfile}")
        outfile.cd()

        # Skim tree for each channel
        for channel in helpers.get_channels(args.analysis):
            cutstring = build_cutstring(cutinfo, channel)
            cutstring += f" && ({triggers[args.trigger]})"

            # Initialize tree
            tree = ROOT.TChain(f"{channel}/ntuple")
            for infile in args.infiles:
                tree.Add(infile)

            # Set aliases
            for key, val in (aliases["Event"] | aliases["Channel"][channel]).items():
                tree.SetAlias(key, val)

            # Apply cuts
            skimmed_tree = tree.CopyTree(cutstring) if tree.GetEntries() > 0 else tree

            # Apply additional selector, if needed for analysis
            selector = get_selector(args.analysis, channel)
            if selector is not None:
                skimmed_tree.Process(selector)
                entry_list = selector.GetOutputList().FindObject("bestCandidates")
                skimmed_tree.SetEntryList(entry_list)
                # To create a tree with only the entries in the list above, copy
                skimmed_tree = skimmed_tree.CopyTree("")

            # Print out information regarding skim
            if args.verbose:
                print(f"{channel}:")
                print(f"  {cutstring}")
                for key, val in (aliases["Event"] | aliases["Channel"][channel]).items():
                    print(f"  Set alias: {key} -> {val}")
                print(f"  Entries pre-skim: {tree.GetEntries()}")
                print(f"  Entries post-skim: {skimmed_tree.GetEntries()}")
                if selector is None:
                    print(f"  No selector available for {args.analysis}")
                else:
                    print("  Selector status:", selector.GetStatus())

            # Save skimmed tree
            subdir = outfile.mkdir(channel)
            subdir.cd()
            skimmed_tree.Write()

            # Save gen tree, if specified
            if args.save_gen:
                tree = ROOT.TChain(f"{channel}Gen/ntuple")
                for infile in args.infiles:
                    tree.Add(infile)
                subdir = outfile.mkdir(f"{channel}Gen")
                subdir.cd()
                tree_copy = tree.CopyTree("")
                tree_copy.Write()

        # Save metaInfo tree
        tree = ROOT.TChain("metaInfo/metaInfo")
        for infile in args.infiles:
            tree.Add(infile)
        subdir = outfile.mkdir("metaInfo")
        subdir.cd()
        tree_copy = tree.CopyTree("")
        tree_copy.Write()

    if args.verbose:
        print(f"Written to {args.outfile}")


def build_cutstring(cutinfo: dict, channel: str) -> str:
    """Build a cutstring to apply to a tree to skim unwanted events.

    Parameters
    ----------
    cutinfo : dict
        A dict containing all the relevant cuts to be applied.
    channel : str
        The channel where the skimming is applied (e.g. eeee or eemm).

    Returns
    -------
    str
        The cutstring built from the given cut information depending on
        the channel provided.
    """
    # Begin cutstring with event cuts and channel-dependent cuts
    cuts = cutinfo["Event"] + cutinfo["Channel"][channel]

    # Build counts of objects and object names
    # i.e. eemm: {"e": 2, "m": 2} -> {"e": ["e1", "e2"], "m": ["m1", "m2"]}
    object_counts = {}
    for obj in channel:
        if obj in object_counts:
            object_counts[obj] += 1
        else:
            object_counts[obj] = 1

    object_names = {}
    for obj, count in object_counts.items():
        object_names[obj] = [f"{obj}{i}" if count != 1 else obj for i in range(1, count + 1)]

    # Add cuts on each object in the event (e.g. on e1, e2, m1, m2)
    for obj, obj_cuts in cutinfo["Object"].items():
        if obj in object_names:
            cuts += [cut.format(name) for cut in obj_cuts for name in object_names[obj]]

    # Add cuts on each object pair in the event (e.g. e1_e2, e1_m1, e1_m2, ...)
    all_object_names = [name for names in object_names.values() for name in names]
    for cut in cutinfo["ObjectPair"]:
        for obj1, obj2 in itertools.combinations(all_object_names, 2):
            cuts.append(cut.format(obj1, obj2))

    # Add cuts on leading (+ subleading) pt leptons
    if cutinfo["LeadingPt"] > 0:
        if cutinfo["SubleadingPt"] > 0:
            ptcuts = []
            for obj1 in all_object_names:
                ptcuts.append(
                    f"{obj1}Pt >= {cutinfo['LeadingPt']} && ("
                    + " || ".join(f"{obj2}Pt >= {cutinfo['SubleadingPt']}" for obj2 in all_object_names if obj2 != obj1)
                    + ")"
                )
            cuts.append(" || ".join(f"({cut})" for cut in ptcuts))
        else:
            cuts.append(" || ".join(f"{obj1}Pt >= {cutinfo['LeadingPt']}"))

    return " && ".join(f"({cut})" for cut in cuts)


def get_selector(analysis: str, channel: str) -> Optional[ROOT.TSelector]:
    """Get selector appropriate for the given analysis.

    Parameters
    ----------
    analysis : str
        The analysis to check for a selector (e.g. ZZ4l).
    channel : str
        The channel where the skimming is applied (e.g. eeee or eemm).

    Returns
    -------
    ROOT.TSelector or None
        A TSelector object loaded with the appropriate inputs depending on
        the given analysis and channel. If no selector is specified for
        an analysis, returns None.
    """
    selector = None

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
    if analysis == "ZZ4l":
        # For a given event, choose the best ZZ candidate
        selector = ROOT.BestZZCandSelector()
        inputs = ROOT.TList()
        inputs.Add(ROOT.TNamed("run", "run"))
        inputs.Add(ROOT.TNamed("evt", "evt"))
        inputs.Add(ROOT.TNamed("Z1Mass", f"{object_names[0]}_{object_names[1]}_Mass"))
        inputs.Add(ROOT.TNamed("Z2Mass", f"{object_names[2]}_{object_names[3]}_Mass"))
        inputs.Add(ROOT.TNamed("l1Pt", f"{object_names[0]}Pt"))
        inputs.Add(ROOT.TNamed("l2Pt", f"{object_names[1]}Pt"))
        inputs.Add(ROOT.TNamed("l3Pt", f"{object_names[2]}Pt"))
        inputs.Add(ROOT.TNamed("l4Pt", f"{object_names[3]}Pt"))
        inputs.Add(ROOT.TNamed("l1Tight", f"{object_names[0]}ZZTightID"))
        inputs.Add(ROOT.TNamed("l2Tight", f"{object_names[1]}ZZTightID"))
        inputs.Add(ROOT.TNamed("l3Tight", f"{object_names[2]}ZZTightID"))
        inputs.Add(ROOT.TNamed("l4Tight", f"{object_names[3]}ZZTightID"))
        inputs.Add(ROOT.TNamed("l1Iso", f"{object_names[0]}ZZIsoPass"))
        inputs.Add(ROOT.TNamed("l2Iso", f"{object_names[1]}ZZIsoPass"))
        inputs.Add(ROOT.TNamed("l3Iso", f"{object_names[2]}ZZIsoPass"))
        inputs.Add(ROOT.TNamed("l4Iso", f"{object_names[3]}ZZIsoPass"))
        selector.SetInputList(inputs)
    elif analysis == "ZplusL":
        # For a given event, choose the best Z candidate
        selector = ROOT.BestZplusLCandSelector()
        inputs = ROOT.TList()
        inputs.Add(ROOT.TNamed("run", "run"))
        inputs.Add(ROOT.TNamed("evt", "evt"))
        for obj, count in object_counts.items():
            if count >= 2:
                inputs.Add(ROOT.TNamed("Z1Mass", f"{obj}1_{obj}2_Mass"))
        selector.SetInputList(inputs)
    else:
        pass  # No selector is built, will return None

    return selector


def get_trigger(triggers: list, sample: str) -> str:
    """Returns appropriate trigger to use for given sample.

    This function searches the sample name for '_TRIGGER_' for
    each trigger in the provided list. Data samples follow this
    convention so that the triggers can be determined on-the-fly.
    If no match is found, 'MonteCarlo' is chosen.

    Parameters
    ----------
    triggers : list of str
        A list of trigger names to check.
    sample: str
        The name of a sample to check.

    Returns
    -------
    str
        The trigger name to apply.
    """
    # Determine trigger (i.e. Primary Dataset for data) for given sample
    for trigger in triggers:
        if f"_{trigger}_" in sample:
            return trigger
    return "MonteCarlo"


def build_farmout_command(paths: list) -> str:
    """Build script to execute skimming jobs through HTCondor.

    Parameters
    ----------
    paths: list of str
        List of file paths (may be globbable) to make the input
        file list.

    Returns
    -------
    str
        The full contents of the farmout.sh file to be created.
    """
    # Set script to exit on error
    command = "# Set script to exit on error\n"
    command += "set -e\n"

    # Create input file list
    command += "# Create input file list\n"
    command += "if [ ! -f ${{job_dir}}/inputs.txt ]; then\n"
    command += "  touch ${{job_dir}}/inputs.txt\n"
    for path in paths:
        command += f"  hdfs dfs -ls {path.replace('/hdfs', '')}"
        command += " | awk '{{print $8}}' >> ${{job_dir}}/inputs.txt\n"
    command += "fi\n\n"

    # Farmout command
    command += "# Farmout command\n"
    farmout_command = []
    farmout_command.append("farmoutAnalysisJobs --fwklite --input-basenames-not-unique --assume-input-files-exist")
    farmout_command.append("--opsys {opsys}")
    farmout_command.append("--submit-dir=${{job_dir}}/submit")
    farmout_command.append("--output-dir={output_dir}/{job_name}")
    farmout_command.append("--input-file-list=${{job_dir}}/inputs.txt")
    farmout_command.append("--input-files-per-job=1")
    farmout_command.append("--input-dir=root://cmsxrootd.hep.wisc.edu/")
    farmout_command.append("{job_name} $CMSSW_BASE ${{job_dir}}/skim.sh")

    return command + " \\\n\t\t".join(farmout_command) + "\n"

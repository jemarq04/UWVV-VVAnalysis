#!/usr/bin/env python3

import ROOT
import os
import argparse
import subprocess
import UWVV.VVAnalysis.helpers as helpers
import UWVV.VVAnalysis.skimtools as skimtools


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-t", "--trigger", default="MonteCarlo", help="trigger set to apply")
    parser.add_argument("-o", "--outfile", default=argparse.SUPPRESS, help="output file (default: output<YEAR>.root)")
    parser.add_argument("-g", "--save-gen", action="store_true", help="save gen trees")
    parser.add_argument("-v", "--verbose", action="store_true", help="print during skimming")
    parser.add_argument("--json-dir", default=helpers.JSON_DIR, help="directory for JSON files")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--infiles", nargs="+", help="input file")
    group.add_argument("-I", "--input-file-list", help="file that lists input files, one per line")
    args = parser.parse_args()

    if "outfile" not in args:
        args.outfile = f"output{args.year}.root"

    if args.input_file_list is not None:
        if not os.path.isfile(args.input_file_list):
            parser.error(f"invalid file: {args.input_file_list}")
        with open(args.input_file_list) as infile:
            args.infiles = [line.strip() for line in infile if not line.isspace() and not line.startswith("#")]

    for infile in args.infiles:
        if infile.startswith("root:"):
            if subprocess.call(f"hdfs dfs -ls {infile[infile.find('/store'):]}".split()) != 0:
                parser.error(f"invalid file: {infile}")
        elif not os.path.isfile(infile.replace("file:", "")):
            parser.error(f"invalid file: {infile}")
    if not os.path.isdir(os.path.join(args.json_dir, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(args.json_dir, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")

    cutinfo = helpers.load_json(args.analysis, args.year, "cuts.json", json_dir=args.json_dir)
    aliases = helpers.load_json(args.analysis, args.year, "aliases.json", json_dir=args.json_dir)
    triggers = helpers.load_json(args.analysis, args.year, "triggers.json", json_dir=args.json_dir)

    if args.trigger not in triggers:
        parser.error(f"invalid trigger: {args.trigger}")

    if args.verbose:
        print(f"Writing to {args.outfile}")

    with ROOT.TFile.Open(args.outfile, "RECREATE") as outfile:
        outfile.cd()
        for channel in helpers.get_channels(args.analysis):
            cutstring = skimtools.build_cutstring(cutinfo, channel)
            cutstring += f" && ({triggers[args.trigger]})"

            tree = ROOT.TChain(f"{channel}/ntuple")
            for infile in args.infiles:
                tree.Add(infile)
            for key, val in (aliases["Event"] | aliases["Channel"][channel]).items():
                tree.SetAlias(key, val)
            skimmed_tree = tree.CopyTree(cutstring)
            selector = skimtools.get_selector(args.analysis, channel)
            if selector is not None:
                skimmed_tree.Process(selector)
                entry_list = selector.GetOutputList().FindObject("bestCandidates")
                skimmed_tree.SetEntryList(entry_list)
            if args.verbose:
                print(f"{channel}:")
                print(f"  {cutstring}")
                for key, val in (aliases["Event"] | aliases["Channel"][channel]).items():
                    print(f"  Set alias: {key} -> {val}")
                print(f"  Entries pre-skim: {tree.GetEntries()}")
                print(f"  Entries post-skim: {skimmed_tree.GetEntries()}")
                if selector is not None:
                    print(f"  Entries saved to entry_list: {entry_list.GetN()}")
                    print("  Selector status:", selector.GetStatus())
            subdir = outfile.mkdir(channel)
            subdir.cd()
            skimmed_tree.Write()

            if args.save_gen:
                tree = ROOT.TChain(f"{channel}Gen/ntuple")
                for infile in args.infiles:
                    tree.Add(infile)
                subdir = outfile.mkdir(f"{channel}Gen")
                subdir.cd()
                tree_copy = tree.CopyTree("")
                tree_copy.Write()

        tree = ROOT.TChain("metaInfo/metaInfo")
        for infile in args.infiles:
            tree.Add(infile)
        subdir = outfile.mkdir("metaInfo")
        subdir.cd()
        tree_copy = tree.CopyTree("")
        tree_copy.Write()

    if args.verbose:
        print(f"Written to {args.outfile}")


if __name__ == "__main__":
    main()

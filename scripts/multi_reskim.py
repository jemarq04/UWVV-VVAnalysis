#!/usr/bin/env python3

import argparse
import glob
import multiprocessing
import os
import shutil

import tqdm
from UWVV.VVAnalysis import helpers, skimtools


def main():
    """Process failed skim.py jobs in parallel using multiple cores.

    This script searches through the job directory to determine which samples were submitted to HTCondor
    and look for their corresponding outputs in the provided out directory. If it's missing, the skim is
    re-attempted.
    """
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=helpers.CustomHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-g", "--save-gen", action="store_true", help="save gen trees")
    parser.add_argument("--only-data", action="store_true", help="only retry failed data skimming jobs")
    parser.add_argument("-q", "--quiet", action="store_true", help="disable all print statements")
    parser.add_argument("-j", "--num-cores", type=int, required=True, help="number of cores to use")
    parser.add_argument("submission_dir", help="job directory in /nfs_scratch/...")
    parser.add_argument("output_dir", help="output directory (e.g. /hdfs/store/user/.../)")
    args = parser.parse_args()

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if args.num_cores <= 0:
        parser.error(f"invalid number of cores: {args.num_cores}")
    if not os.path.isdir(args.submission_dir):
        parser.error(f"invalid job directory: {args.submission_dir}")
    if not os.path.isdir(args.output_dir):
        parser.error(f"invalid output directory: {args.output_dir}")

    # Load JSON information
    args.cutinfo = helpers.load_json(args.analysis, args.year, "cuts.json")
    args.aliases = helpers.load_json(args.analysis, args.year, "aliases.json")
    args.triggers = helpers.load_json(args.analysis, args.year, "triggers.json")

    # Iterate over job directories
    # TODO: maybe use multiprocessing to determine missing files
    failed_jobs = []
    samples = [sample for sample in os.listdir(args.submission_dir) if not args.only_data or sample.startswith("data")]
    if not args.quiet:
        print("Searching output directory for missing output files")
    for sample in tqdm.tqdm(samples) if not args.quiet else samples:
        sample_dir = os.path.join(args.submission_dir, sample)
        sample_output_dir = os.path.join(args.output_dir, sample)
        if not os.path.isdir(sample_output_dir):
            continue
        trigger = skimtools.get_trigger(list(args.triggers.keys()), sample)
        for skim_path in glob.iglob(os.path.join(sample_dir, "submit", "skim-*")):
            skim_name = os.path.basename(skim_path)
            outfile = os.path.join(sample_output_dir, f"{skim_name}.root")
            if not os.path.isfile(outfile):
                with open(os.path.join(skim_path, f"{skim_name}.inputs")) as infile:
                    inputs = [line.strip() for line in infile]
                failed_jobs.append((inputs, outfile, trigger))

    if failed_jobs:
        with multiprocessing.Pool(processes=args.num_cores) as pool:
            if not args.quiet:
                print("Re-skimming failed files")
                list(
                    tqdm.tqdm(
                        pool.imap_unordered(call_skim, [(args, failed_job) for failed_job in failed_jobs]),
                        total=len(failed_jobs),
                    )
                )
            else:
                pool.map(call_skim, [(args, failed_job) for failed_job in failed_jobs])
    elif not args.quiet:
        print("No missing output files!")


def call_skim(args: tuple):
    """Unpack tuple of arguments and call skim()."""
    skim(*args)


def skim(args: argparse.Namespace, jobinfo: tuple):
    """Skim file one at a time with the given inputs."""
    (inputs, outfile, trigger) = jobinfo
    temp_file = os.path.basename(outfile)

    # Initialize arguments to pass to skimmer
    skim_args = argparse.Namespace(
        analysis=args.analysis,
        year=args.year,
        trigger=trigger,
        save_gen=args.save_gen,
        verbose=False,
        infiles=inputs,
        outfile=temp_file,
    )

    # Skim file and move to target directory
    skimtools.skim(skim_args, args.cutinfo, args.aliases, args.triggers)
    shutil.move(temp_file, outfile)


if __name__ == "__main__":
    main()

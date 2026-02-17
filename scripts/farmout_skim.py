#!/usr/bin/env python3

import os
import json
import argparse
import datetime
import subprocess
import configparser
import UWVV.VVAnalysis.helpers as helpers
import UWVV.VVAnalysis.skimtools as skimtools


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-g", "--save-gen", action="store_true", help="save gen trees")
    parser.add_argument("-v", "--verbose", action="store_true", help="print during skimming")
    parser.add_argument("-q", "--quiet", action="store_true", help="disable all print statements")
    parser.add_argument(
        "--ntuples", default=argparse.SUPPRESS, help="ntuple JSON (default: json/<ANALYSIS>/<YEAR>/ntuples.json)"
    )
    parser.add_argument(
        "-s",
        "--submission-dir",
        default=argparse.SUPPRESS,
        help="submission directory (default: /nfs_scratch/<USERNAME>/<DATE>_<ANALYSIS><YEAR>AnalysisJobs/)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=argparse.SUPPRESS,
        help="output directory (default: /hdfs/store/user/<CERN_USERNAME>/<ANALYSIS><YEAR>AnalysisJobs_<DATE>/)",
    )
    parser.add_argument("--opsys", default="AlmaLinux9", help="operating system for jobs to run")
    parser.add_argument("--test", action="store_true", help="create submission directory but do not execute")
    args = parser.parse_args()

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if "ntuples" in args and not os.path.isfile(args.ntuples):
        parser.error(f"invalid ntuples JSON: {args.ntuples}")

    config_path = os.path.join(helpers.BASE_DIR, "config", f"{os.getlogin()}.cfg")
    if not os.path.isfile(config_path):
        parser.error(f"cannot find config file: {config_path}")

    # Read user configuration file
    settings = configparser.ConfigParser()
    settings.read(config_path)

    # Handle defaults
    date = f"{datetime.date.today():%Y-%m-%d}"
    if "submission_dir" not in args:
        args.submission_dir = f"/nfs_scratch/{os.getlogin()}/{date}_{args.analysis}{args.year}AnalysisJobs"
    if "output_dir" not in args:
        args.output_dir = (
            f"/hdfs/store/user/{settings['farmout']['cern_username']}/{args.analysis}{args.year}AnalysisJobs_{date}"
        )
    if "ntuples" not in args:
        args.ntuples = None
    if args.quiet:
        args.verbose = False

    # Load JSON information
    triggers = list(helpers.load_json(args.analysis, args.year, "triggers.json").keys())
    if args.ntuples is not None:
        with open(args.ntuples) as infile:
            ntuples = json.load(infile)
    else:
        ntuples = helpers.load_json(args.analysis, args.year, "ntuples.json")

    # Determine unique directory names (to avoid overwriting)
    args.submission_dir = helpers.get_unique_dirname(args.submission_dir)
    args.output_dir = helpers.get_unique_dirname(args.output_dir)

    # Submit skimming jobs for each sample
    if args.verbose:
        print(f"Setting up jobs for {list(ntuples.keys())}\n")
    os.mkdir(args.submission_dir)
    for sample in ntuples:
        job_dir = os.path.join(args.submission_dir, sample)
        os.mkdir(job_dir)
        if args.verbose:
            print(f"Created directory {job_dir}")

        # Create farmout.sh file
        farmout_path = os.path.join(job_dir, "farmout.sh")
        with open(farmout_path, "w") as outfile:
            outfile.write(f"job_dir={job_dir}\n\n")
            outfile.write(skimtools.build_farmout_command(ntuples[sample]).format(job_name=sample, **vars(args)))

        # Create skim.sh file
        with open(os.path.join(job_dir, "skim.sh"), "w") as outfile:
            outfile.write(f"skim.py -v -a {args.analysis} -y {args.year} -I $INPUT -o $OUTPUT ")
            if args.save_gen:
                outfile.write("--save-gen ")
            outfile.write(f"-t {skimtools.get_trigger(triggers, sample)} --json-dir {helpers.JSON_DIR}\n")

        # Call farmout.sh file and pipe output to file
        if not args.test:
            if args.verbose:
                print("Calling farmout.sh...")
            log_path = os.path.join(job_dir, "log.txt")
            with open(log_path, "w") as outfile:
                status = subprocess.call(["bash", farmout_path], stdout=outfile, stderr=outfile)
                if status != 0:
                    print(f"ERROR: Jobs for {sample} unsubmitted. Check log file: {log_path}")
                elif not args.quiet:
                    print(f"Jobs submitted to condor for {sample}")
        elif not args.quiet:
            print(f"Submission directory created for {sample}")

    if args.verbose:
        print("\nDone.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import os
import json
import argparse
import datetime
import subprocess
import configparser
import UWVV.VVAnalysis.helpers as helpers
import UWVV.VVAnalysis.skimtools as skimtools

# TODO: add more verbose statements to use with args.verbose (maybe even a quiet flag)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-g", "--save-gen", action="store_true", help="save gen trees")
    parser.add_argument("-v", "--verbose", action="store_true", help="print during skimming")
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

    # Load JSON information
    triggers = list(helpers.load_json(args.analysis, args.year, "triggers.json").keys())
    if args.ntuples is not None:
        with open(args.ntuples) as infile:
            ntuples = json.load(infile)
    else:
        ntuples = helpers.load_json(args.analysis, args.year, "ntuples.json")

    # Determine submission directory name (avoids overwriting) and create it
    count = 1
    base_submission_dir = args.submission_dir
    while os.path.isdir(args.submission_dir):
        count += 1
        args.submission_dir = f"{base_submission_dir}_{count}"
    os.mkdir(args.submission_dir)

    # Submit skimming jobs for each sample
    for sample in ntuples:
        job_dir = os.path.join(args.submission_dir, sample)
        os.mkdir(job_dir)

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
        log_path = os.path.join(job_dir, "log.txt")
        with open(log_path, "w") as outfile:
            if not args.test:
                status = subprocess.call(["bash", farmout_path], stdout=outfile, stderr=outfile)
                if status != 0:
                    print(f"ERROR: Jobs for {sample} unsubmitted. Check log file: {log_path}")
                else:
                    print(f"Jobs submitted to condor for {sample}")
            else:
                print(f"Submission directory created for {sample}")


if __name__ == "__main__":
    main()

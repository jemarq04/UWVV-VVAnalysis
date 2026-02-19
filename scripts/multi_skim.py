#!/usr/bin/env python3

import os
import glob
import tqdm
import shutil
import argparse
import datetime
import configparser
import multiprocessing
import UWVV.VVAnalysis.helpers as helpers
import UWVV.VVAnalysis.skimtools as skimtools


def call_skim(args: tuple):
    skim(*args)


def skim(
    args: argparse.Namespace,
    sample: str,
    infile: str,
    output_dir: str,
    cutinfo: dict,
    aliases: dict,
    triggers: dict,
    trigger: str,
):
    # Determine output file path
    # (Temporary file needed for saving in /hdfs/store/...)
    basename = os.path.basename(infile)
    temp_file = f"temp_{sample}_{basename}"
    outfile = os.path.join(output_dir, basename)

    # Initialize arguments to pass to skimmer
    skim_args = argparse.Namespace(
        analysis=args.analysis,
        year=args.year,
        trigger=trigger,
        save_gen=args.save_gen,
        verbose=False,
        infiles=[infile],
        outfile=temp_file,
    )

    # Skim file and move to target directory
    skimtools.skim(skim_args, cutinfo, aliases, triggers)
    shutil.move(temp_file, outfile)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--analysis", default="ZZ4l", help="name of analysis")
    parser.add_argument("-y", "--year", default="2022", help="year for analysis")
    parser.add_argument("-g", "--save-gen", action="store_true", help="save gen trees")
    parser.add_argument("-q", "--quiet", action="store_true", help="disable all print statements")
    parser.add_argument("-j", "--num-cores", type=int, required=True, help="number of cores to use")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=argparse.SUPPRESS,
        help="output directory (default: /hdfs/store/user/<CERN_USERNAME>/<ANALYSIS><YEAR>AnalysisJobs_<DATE>/)",
    )
    args = parser.parse_args()

    # Error checking
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis)):
        parser.error(f"invalid analysis: {args.analysis}")
    if not os.path.isdir(os.path.join(helpers.JSON_DIR, args.analysis, args.year)):
        parser.error(f"invalid year for analysis {args.analysis}: {args.year}")
    if args.num_cores <= 0:
        parser.error(f"invalid number of cores: {args.num_cores}")

    config_path = os.path.join(helpers.BASE_DIR, "config", f"{os.getlogin()}.cfg")
    if not os.path.isfile(config_path):
        parser.error(f"cannot find config file: {config_path}")

    # Read user configuration file
    settings = configparser.ConfigParser()
    settings.read(config_path)

    # Handle defaults
    date = f"{datetime.date.today():%Y-%m-%d}"
    if "output_dir" not in args:
        args.output_dir = (
            f"/hdfs/store/user/{settings['farmout']['cern_username']}/{args.analysis}{args.year}AnalysisJobs_{date}"
        )

    # Load JSON information
    cutinfo = helpers.load_json(args.analysis, args.year, "cuts.json")
    aliases = helpers.load_json(args.analysis, args.year, "aliases.json")
    triggers = helpers.load_json(args.analysis, args.year, "triggers.json")
    ntuples = helpers.load_json(args.analysis, args.year, "ntuples.json")

    # Determine unique directory names (to avoid overwriting)
    args.output_dir = helpers.get_unique_dirname(args.output_dir)

    # Process each dataset
    num_samples = len(ntuples)
    for i, sample in enumerate(ntuples):
        # Get list of files to process and determine the trigger
        infiles = [infile for path in ntuples[sample] for infile in glob.iglob(path)]
        trigger = skimtools.get_trigger(list(triggers.keys()), sample)

        if not args.quiet:
            print(f"\n{i+1}/{num_samples} Processing {sample} ({trigger})")

        # Skip any skim calls if there are no input files
        if not infiles:
            continue

        # Create output directory as needed
        output_dir = os.path.join(args.output_dir, sample)
        os.makedirs(output_dir, exist_ok=True)

        # Use multiple cores to call skim.py for each dataset
        with multiprocessing.Pool(processes=args.num_cores) as pool:
            if not args.quiet:
                list(
                    tqdm.tqdm(
                        pool.imap(
                            call_skim,
                            [
                                (args, sample, infile, output_dir, cutinfo, aliases, triggers, trigger)
                                for infile in infiles
                            ],
                        ),
                        total=len(infiles),
                    )
                )
            else:
                pool.map(
                    call_skim,
                    [(args, sample, infile, output_dir, cutinfo, aliases, triggers, trigger) for infile in infiles],
                )


if __name__ == "__main__":
    main()

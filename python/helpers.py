import argparse
import json
import os

BASE_DIR = os.environ["CMSSW_BASE"] + "/src/UWVV/VVAnalysis"
JSON_DIR = os.path.join(BASE_DIR, "json")


def get_channels(analysis: str) -> list:
    """Determine list of channels for a given analysis.

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
        channels = ["eeee", "eemm", "mmmm"]
    elif analysis == "ZplusL":
        channels = ["eee", "eem", "emm", "mmm"]
    else:
        raise NotImplementedError(f"no channels found for analysis {analysis}")
    return channels


class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    """Inherits properties from two formatter classes for desired help strings."""

    pass


def load_json(analysis: str, year: str, basename: str, json_dir: str = JSON_DIR) -> dict:
    """Load JSON files into a dict for a given analysis and year.

    This function will load dictionaries from JSON files (if they exist)
    in a specific order:
    1. <json_dir>/<basename>
    2. <json_dir>/<analysis>/<basename>
    3. <json_dir>/<analysis>/<year>/<basename>

    The loading is done in a 'modified extended' way - the highest-level dict
    is merged into by extending lists and overwriting other types. Any
    sub-dictionaries are merged in the same way.

    Parameters
    ----------
    analysis : str
        Name of analysis with the given JSON information.
    year : str
        The year for the given JSON information.
    basename : str
        The base name of the JSON file to look for in the given analysis and year.
    json_dir : str, optional
        The base JSON directory that stores the relevant files (default is JSON_DIR).

    Returns
    -------
    dict
        The merged JSON dictionary.
    """
    filenames = [
        os.path.join(json_dir, basename),
        os.path.join(json_dir, analysis, basename),
        os.path.join(json_dir, analysis, year, basename),
    ]
    result = {}
    for filename in filenames:
        if os.path.exists(filename):
            with open(filename) as infile:
                merge_dicts(result, json.load(infile))
    return result


def get_unique_dirname(dirname: str) -> str:
    """Determine a unique directory name to avoid overwriting.

    Parameters
    ----------
    dirname : str
        Name of directory to check. If it exists, '<dirname>_2' will
        be checked, and so on.

    Returns
    -------
    str
        A unique directory name derived from the one provided.
    """
    count = 1
    basedir = dirname
    while os.path.exists(dirname):
        count += 1
        dirname = f"{basedir}_{count}"
    return dirname


def merge_dicts(dict1: dict, dict2: dict):
    """Merge dictionary using a modified extended method.

    The first dict is merged into by extending lists and
    overwriting values of other types. Any sub-dictionaries
    are merged in the same way, recursively.

    Parameters
    ----------
    dict1 : dict
        The dictionary to merge into. This will be overwritten.
    dict2 : dict
        The dictionary to merge from.
    """
    for key, val in dict1.items():
        if key in dict2:
            if type(val) is dict:
                merge_dicts(val, dict2[key])
            elif type(val) is list:
                val.extend(dict2[key])
            else:
                dict1[key] = dict2[key]
    for key, val in dict2.items():
        if key not in dict1:
            dict1[key] = val

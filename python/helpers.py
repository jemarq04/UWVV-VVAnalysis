import os
import json

# NOTE: maybe get some sort of recipe/makefile that writes down the current directory for easy lookup in these scripts.
BASE_DIR = os.environ["CMSSW_BASE"] + "/src/UWVV/VVAnalysis"
JSON_DIR = os.path.join(BASE_DIR, "json")


def get_channels(analysis: str) -> list:
    channels = []
    if analysis == "ZZ4l":
        channels = ["eeee", "eemm", "mmmm"]
    elif analysis == "ZplusL":
        channels = ["eee", "eem", "emm", "mmm"]
    else:
        raise ValueError(f"no channels found for analysis {analysis}")
    return channels


def load_json(analysis: str, year: str, basename: str) -> dict:
    filenames = [
        os.path.join(JSON_DIR, basename),
        os.path.join(JSON_DIR, analysis, basename),
        os.path.join(JSON_DIR, analysis, year, basename),
    ]
    result = {}
    for filename in filenames:
        if os.path.exists(filename):
            with open(filename) as infile:
                merge_dicts(result, json.load(infile))
    return result


def merge_dicts(dict1: dict, dict2: dict):
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

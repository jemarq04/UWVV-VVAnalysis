# import ROOT
# import argparse
import json
import os
import itertools

# NOTE: Get it working hard-coded and then make it better later!
# maybe get some sort of recipe/makefile that writes down the current directory for easy lookup in these scripts.

JSON_DIR = os.environ["CMSSW_BASE"] + "/src/UWVV/VVAnalysis/json"


def main():
    if "CMSSW_BASE" not in os.environ:
        print("error: CMSSW_BASE not set")
        exit(1)

    dataset = "MonteCarlo"  # or Muon, EGamma, MuonEG, etc.
    analysis = "ZZ4l"
    year = "2022"

    cutinfo = load_json(analysis, year, "cuts.json")
    aliases = load_json(analysis, year, "aliases.json")
    triggers = load_json(analysis, year, "triggers.json")

    for channel in ["eeee", "eemm", "mmmm"]:
        cutstring = build_cutstring(cutinfo, channel)
        cutstring += f" && ({triggers[dataset]})"
        print(cutstring)


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


def build_cutstring(cutinfo: dict, channel: str) -> str:
    cuts = cutinfo["Event"] + cutinfo["Channel"][channel]

    object_counts = {}
    for obj in channel:
        if obj in object_counts:
            object_counts[obj] += 1
        else:
            object_counts[obj] = 1

    object_names = {}
    for obj, count in object_counts.items():
        object_names[obj] = [f"{obj}{i}" if count != 1 else obj for i in range(1, count + 1)]

    for obj, obj_cuts in cutinfo["Object"].items():
        if obj in object_names:
            cuts += [cut.format(name) for cut in obj_cuts for name in object_names[obj]]

    all_object_names = [name for names in object_names.values() for name in names]
    for cut in cutinfo["ObjectPair"]:
        for obj1, obj2 in itertools.combinations(all_object_names, 2):
            cuts.append(cut.format(obj1, obj2))

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


if __name__ == "__main__":
    main()

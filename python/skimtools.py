import ROOT
import itertools
from typing import Optional


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


def get_selector(analysis: str, channel: str) -> Optional[ROOT.TSelector]:
    # if "ROOT" not in sys.modules:
    #        import ROOT
    selector = None

    object_counts = {}
    object_names = []
    for obj in channel:
        if obj in object_counts:
            object_counts[obj] += 1
        else:
            object_counts[obj] = 1
    for obj, count in object_counts.items():
        object_names += [f"{obj}{i}" if count != 1 else obj for i in range(1, count + 1)]

    if analysis == "ZZ4l":
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
        selector = ROOT.BestZplusLCandSelector()
        inputs = ROOT.TList()
        inputs.Add(ROOT.TNamed("run", "run"))
        inputs.Add(ROOT.TNamed("evt", "evt"))
        for obj, count in object_counts.items():
            if count >= 2:
                inputs.Add(ROOT.TNamed("Z1Mass", f"{obj}1_{obj}2_Mass"))
        selector.SetInputList(inputs)

    return selector

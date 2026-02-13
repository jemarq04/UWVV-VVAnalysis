import itertools


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

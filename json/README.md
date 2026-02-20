# UWVV/VVAnalysis JSON files
----------------------------

This directory stores all the relevant information for skimming, merging, and plotting UWVV ntuples. An example directory structure is the following:

```
json
|-- <ANALYSIS>
|   |-- <YEAR>
|   |   `-- some-files.json
|   |-- aliases.json
|   |-- cuts.json
|   `-- montecarlo.json
`-- data.json
```

This is a work in progress.

## Table of Contents

- [Setup](#setup)
- [JSON File Formats](#json-file-formats)
   * [`data.json`](#datajson)
      + [Example](#example)
   * [`montecarlo.json`](#montecarlojson)
      + [Example](#example-1)
   * [`ntuples.json`](#ntuplesjson)
      + [Example](#example-2)
   * [`skimmed.json`](#skimmedjson)
      + [Example](#example-3)
   * [`aliases.json`](#aliasesjson)
      + [Example](#example-4)
   * [`cuts.json`](#cutsjson)
      + [Example](#example-5)
   * [`triggers.json`](#triggersjson)
      + [Example](#example-6)

## Setup

When JSON files are loaded for jobs, they are loaded by searching each directory in order. For example, let's say we want to load `montecarlo.json`
for a ZZ4l analysis in 2024. The JSON file will be loaded by checking in the following order:

1. `json/montecarlo.json`: This file will likely not exist, as it shouldn't be common for multiple VV analyses to share the exact same MC samples!
2. `json/ZZ4l/montecarlo.json`: This file exists, and so all the relevant information for this file will be loaded.
3. `json/ZZ4l/2024/montecarlo.json`: This file also exists, so the JSON file is merged into by using a modified extended method. What this means is
   that any lists within the dict will be extended and all other values will be overwritten. In this example, this file has a "ggHZZ" dictionary that
   only specifies the "dataset" key. That means that the original cross-section and k-factor will remain untouched from their original values set from
   `json/ZZ4l/montecarlo.json`, and only the "dataset" key will change. (This was because MC naming conventions changed in 2024.) Additional Drell-Yan
   samples are also specified here.

This hierarchical nature of the JSON files is important to set defaults and update things as the analysis progresses, but keep as much information
shared as needed for readability and maintaining the information in the long-term. Next we can look into each type of JSON file.

## JSON File Formats

### `data.json`

The `data.json` file stores information about each year and era, such as luminosities and MC campaigns. This will likely be shared by all analyses,
but can be moved around following the loading order described in [the previous section](#setup). This file is used by
[`farmout_skim.py`](../scripts/farmout_skim.py) and [`multi_skim.py`](../scripts/multi_skim.py) to determine the MC campaigns needed.

Each year is added to the "years" dictionary and should contain the following keys:

- eras: A dictionary of dictionaries. The sub-dictionaries will list the luminosity ("lumi") and campaign ("campaign") for that era. This is
  necessary for years like 2022 and 2023 that were split into 2022/2022EE and 2023/2023BPix, respectively. For other years, this should be empty.
- campaign: A string containing the MC campaign for this year. This can be the exact name or simply the prefix followed by the glob `*` operator. If
  the year is split into sub-eras (e.g. 2022 and 2023), this should be `null`.
- lumi: The luminosity for the full year. If the year is split into sub-eras (e.g. 2022 and 2023), this should be `null`.
- lumi\_unc: The uncertainty on the luminosity measurements for this year. This is used as an input for Combine cards, so if there is a 1.4% error
  then it should be listed as `1.014`.

To merging/plotting combined years (e.g. plotting 2022-2023 for an early Run 3 analysis), you need to define a 'combined' key. This is done by adding
an entry to the "combined" dictionary. This entry will simply be a list of strings, where each string is the year desired in this combined analysis.

#### Example

For examples of each of the cases described above, look at the snippet of [`json/data.json`](json/data.json) below.

```json
{
  "years": {
    "2022": {
      "eras": {
        "preEE": {
          "lumi": 7.980315199,
          "campaign": "Run3Summer22MiniAOD*"
        },
        "postEE": {
          "lumi": 26.671326001,
          "campaign": "Run3Summer22EEMiniAOD*"
        }
      },
      "campaign": null,
      "lumi": null,
      "lumi_unc": 1.014
    },
    "2024": {
      "eras": {},
      "campaign": "RunIII2024Summer24MiniAOD*",
      "lumi": 108.95,
      "lumi_unc": 0.0
    }
  },
  "combined": {
    "Run3Combined": ["2022", "2023", "2024"]
  }
}
```

### `montecarlo.json`

The `montecarlo.json` file stores information for each MC sample in the analysis. This file is used by [`make_json.py`](../scripts/make_json.py) to
determine the MC samples needed. Each MC sample is added to the root dictionary and should contain the following keys:

- cross\_section: The cross-section of the MC sample. This will often be retrieved from [XSDB](https://xsecdb-xsdb-official.app.cern.ch/).
- k\_factor: The k-factor for the MC sample. These are often determined by theorists and used to help make the cross-section measurement more precise
  (e.g. LO -> NLO accuracy).
- dataset: The MC primary dataset name. This can be the full dataset name or just the prefix with the glob `*` operator. This will be needed to submit
  CRAB jobs to make the UWVV ntuples, but can also be retrieved from [DAS](https://cmsweb.cern.ch/das/).

Note that even if your analysis contains years that are split (i.e. 2022/2022EE), you do not need to create one entry for each era! The separate
entries that are needed for the analysis will be created as needed by [`make_json.py`](../scripts/make_json.py). For example, an entry for "qqZZ"
would be used by [`make_json.py`](../scripts/make_json.py) to create a "qqZZ\_preEE" and "qqZZ\_postEE" entry for ntuples or skimmed listings
automatically.

#### Example

```json
{
  "qqZZ": {
    "cross_section": 1.39,
    "k_factor": 1.08,
    "dataset": "ZZto4L_*"
  }
}
```

### `ntuples.json`

The `ntuples.json` file stores lists of paths to UWVV ntuples per MC sample for a given analysis and year. This file is used by
[`farmout_skim.py`](../scripts/farmout_skim.py) and [`multi_skim.py`](../scripts/multi_skim.py) as input to determine the files needed to be skimmed.
This file can be created automatically using [`make_json.py`](../scripts/make_json.py).

Each MC sample is added to the root dictionary and should contain a list of file paths. (The glob `*` operator is suppported.)

#### Example

```json
{
  "qqZZ_preEE": [
    "/hdfs/store/user/marquez/ZZ4l2022-ntuples/ZZto4L_*/Run3Summer22MiniAOD*/*/*/*.root"
  ],
  "qqZZ_postEE": [
    "/hdfs/store/user/marquez/ZZ4l2022-ntuples/ZZto4L_*/Run3Summer22EEMiniAOD*/*/*/*.root"
  ]
}
```

### `skimmed.json`

The `skimmed.json` file stores lists of paths to skimmed UWVV ntuples per MC sample for a given analysis and year. This file can be created
automatically using [`make_json.py`](../scripts/make_json.py).

Each MC sample is added to the root dictionary and should contain a list of file paths. (The glob `*` operator is suppported.)

#### Example

```json
{
  "zz4l-powheg_preEE": [
    "/hdfs/store/user/marquez/ZZ4l2022-skimmed/qqZZ_preEE/*.root"
  ],
  "zz4l-powheg_postEE": [
    "/hdfs/store/user/marquez/ZZ4l2022-skimmed/qqZZ_postEE/*.root"
  ]
}
```

### `aliases.json`

The `aliases.json` file stores information needed to set aliases in a `TTree` before applying any cuts. This file is used by
[`skim.py`](../scripts/skim.py) (and other scripts that skim) to determine the appropriate aliases to set.

The file contains two dictionaries: "Channel" and "Event". The "Event" dictionary contains string to string mappings that define the alias. The key is
the new name and the value is the formula that the new name points to. The "Channel" dictionary contains one dictionary for each channel, and those
channel dictionaries are formatted like in "Event".

The trigger-flow is described within the "Event" dictionary.

#### Example

```json
{
  "Channel" : {
    "eeee" : {
      "Z1Mass": "e1_e2_Mass",
      "Z2Mass": "e3_e4_Mass"
    },
    "eemm" : {
      "Z1Mass": "e1_e2_Mass",
      "Z2Mass": "m1_m2_Mass"
    },
    "mmmm" : {
      "Z1Mass": "m1_m2_Mass",
      "Z2Mass": "m3_m4_Mass"
    }
  },
  "Event" : {
    "singleElectronPass": "HLT_Ele32_WPTight_GsfPass || HLT_Ele30_WPTight_GsfPass"
  }
}
```

### `cuts.json`

The `cuts.json` file stores information needed to build a "custring" (i.e. a formula string that is parsed by a `TTree` to skim events). This file is
used by [`skim.py`](../scripts/skim.py) (and other scripts that skim) to apply cuts on input `TTree` objects. Note that [aliases](#aliasesjson) are
set before these are applied.

The root directory contains six keys:

- Object: This is a dictionary containing string to list mappings. Each key is an object in the event and the value is a list of cuts to be applied to
  each of the specified objects (e.g. the key "e" lists the cuts to apply to each electron).
    - **Note**: All objects must be specified, even if it is an empty list.
- ObjectPair: This is a list of cuts to be applied to every pair of leptons (regardless of charge or flavor).
- Channel: This is a dictionary containing string to list mappings. Each key is a channel and the value is a list of cuts to be applied to events in
  this channel.
    - **Note**: All channels must be specified, even if it is an empty list.
- Event: This is a list of cuts to be applied to every event, regardless of channel.
- LeadingPt: A float which sets the pt cut on the leading lepton pt. To disable, set to `null`, but note that doing so will disable the subleading
  lepton pt cut below.
- SubleadingPt: A float which sets the pt cut on the subleading lepton pt. To disable, set to `null`.

#### Example

```json
{
  "Object": {
    "e": [
      "{}ZZLooseID > 0.5"
    ],
    "m": [
      "{}ZZLooseID > 0.5"
    ]
  },
  "ObjectPair": [
    "{0}_{1}_DR >= 0.02"
  ],
  "Channel": {
    "eeee": [
      "!(abs(ZaMass-91.1876) < abs(Z1Mass-91.1876) && ZbMass < 12)"
    ],
    "eemm": [
    ],
    "mmmm": [
      "!(abs(ZaMass-91.1876) < abs(Z1Mass-91.1876) && ZbMass < 12)"
    ]
  },
  "Event": [
    "Mass > 70"
  ],
  "LeadingPt": 20,
  "SubleadingPt": 10
}
```

### `triggers.json`

The `triggers.json` file stores information on the trigger selections for MC and data samples. This file is used by [`skim.py`](../scripts/skim.py)
(and other scripts that skim) to apply trigger selections on input `TTree` objects. Note that [aliases](#aliasesjson) are set before these are
applied.

The root dictionary contains a list of string to string mappings. The key is the primary dataset name (e.g. EGamma0 or MuonEG) or "MonteCarlo" and the
value is the formula to be applied for the trigger selection.

To avoid duplicate data events, it is important that there is a proper ordering (or "trigger flow") to how the cuts are applied. For example, if the
EGamma dataset applies `singleElectronPass || doubleElectronPass`, then all other data triggers should check that those fail as well. The files in the
repository currently follow these rules.

#### Example

```json
{
    "MonteCarlo" : "singleElectronPass || doubleElectronPass || singleMuonPass || doubleMuonPass || tripleMuonPass || crossEMuPass",
    "EGamma" : "singleElectronPass || doubleElectronPass",
    "DoubleMuon" : "(doubleMuonPass || tripleMuonPass) && !(singleElectronPass || doubleElectronPass)",
    "SingleMuon" : "(singleMuonPass) && !(doubleMuonPass || tripleMuonPass) && !(singleElectronPass || doubleElectronPass)",
    "Muon" : "(singleMuonPass || doubleMuonPass || tripleMuonPass) && !(singleElectronPass || doubleElectronPass)",
    "MuonEG" : "crossEMuPass && !(singleMuonPass || doubleMuonPass || tripleMuonPass) && !(singleElectronPass || doubleElectronPass)"
}
```

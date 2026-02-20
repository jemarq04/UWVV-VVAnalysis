# UWVV/VVAnalysis JSON files
----------------------------

This directory stores all the relevant information for skimming, merging, and plotting UWVV ntuples. The general structure is the following:

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
but can be moved around following the loading order described in [the previous section](#setup). This file is used by `farmout_skim.py` and
`multi_skim.py` to determine the MC campaigns needed.

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

The `montecarlo.json` file stores information for each MC sample in the analysis. This file is used by `make_json.py`
to determine the MC samples needed. Each MC sample is added to the root dictionary and should contain the following keys:

- cross\_section: The cross-section of the MC sample. This will often be retrieved from [XSDB](https://xsecdb-xsdb-official.app.cern.ch/).
- k\_factor: The k-factor for the MC sample. These are often determined by theorists and used to help make the cross-section measurement more precise
  (e.g. LO -> NLO accuracy).
- dataset: The MC primary dataset name. This can be the full dataset name or just the prefix with the glob `*` operator. This will be needed to submit
  CRAB jobs to make the UWVV ntuples, but can also be retrieved from [DAS](https://cmsweb.cern.ch/das/).

Note that even if your analysis contains years that are split (i.e. 2022/2022EE), you do not need to create one entry for each era! The separate
entries that are needed for the analysis will be created as needed by `make_json.py`. For example, an entry for "qqZZ" would be used by `make_json.py`
to create a "qqZZ\_preEE" and "qqZZ\_postEE" entry for ntuples or skimmed listings automatically.

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

Work in progress.

### `skimmed.json`

Work in progress.

### `aliases.json`

Work in progress.

### `cuts.json`

Work in progress.

### `triggers.json`

Work in progress.

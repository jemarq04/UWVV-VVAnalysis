# UWVV/VVAnalysis
-----------------

This project is meant to take in ntuples produced from [UWVV](https://github.com/jemarq04/UWVV) and process them for analysis. There are scripts
available to skim ntuples, merge files, and plot distributions.

Note that this repository is still in-progress.

## Setup

Eventually, this will be set up automatically by UWVV. Until then, run the following commands.

This project has been tested within `CMSSW_15_0_14`. To create a fresh environment, run the following:
```bash
cmsrel CMSSW_15_0_14
cd CMSSW_15_0_14/src
cmsenv
```

If you already have an environment prepared, make sure it's activated (with `cmsenv`) and run the following:
```bash
cd $CMSSW_BASE/src
git clone git@github.com:jemarq04/UWVV-VVAnalysis UWVV/VVAnalysis
cd UWVV/VVAnalysis
make build
```

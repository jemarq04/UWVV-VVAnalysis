#!/bin/bash

basedir=$CMSSW_BASE/src/UWVV/VVAnalysis

# Error checking
if [[ $# -lt 1 ]]; then
  echo "usage: $0 ANALYSIS [YEAR]"
  echo
  echo "ANALYSIS: name of analysis to make fake rate"
  echo "[YEAR]: year of analysis (default: all)"
  exit 1
elif [[ -z $CMSSW_BASE ]]; then
  echo "CMSSW not set!"
  exit 1
elif [[ ! -d $basedir/json/$1 ]]; then
  echo "invalid analysis: $1"
  exit 1
fi

# Set variables
analysis=$1
years=$2

# Handle defaults
if [[ -z $years || $years = all ]]; then
  years=($basedir/json/$analysis/*/)
fi

for yearpath in ${years[@]}; do
  year=$(basename $yearpath)
  # Check for valid year
  [[ ! -d $basedir/json/$analysis/$year ]] && continue

  # Set input/outputs
  infile=$basedir/histout/ScaledHists-${analysis}${year}.root
  outfile=$basedir/data/FakeRates-${analysis}${year}.json

  # Skip if there is no valid input file
  if [[ ! -f $infile ]]; then
    echo "error: File $(basename $infile) not found. Skipping..."
    continue
  fi

  echo Running $analysis$year...
  make_fakerate.py -a $analysis -y $year -o $outfile $infile
  echo $year done.
done

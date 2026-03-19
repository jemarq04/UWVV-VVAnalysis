#!/bin/bash

basedir=$CMSSW_BASE/src/UWVV/VVAnalysis

# Error checking
if [[ $# -lt 1 ]]; then
  echo "usage: $0 ANALYSIS [YEAR]"
  echo
  echo "ANALYSIS: name of analysis to merge"
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
  outdir=$basedir/histout
  histfile=$outdir/Hists-${analysis}${year}.root
  scaledfile=$outdir/ScaledHists-${analysis}${year}.root

  echo Running $analysis$year...
  multi_merge.py -a $analysis -y $year -j 12 -o $histfile
  [[ -f $histfile ]] && preplot.py -a $analysis -y $year -o $scaledfile $histfile || echo No output file $histfile
  echo $year done.
done

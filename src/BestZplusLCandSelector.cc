#include "UWVV/VVAnalysis/interface/BestZplusLCandSelector.h"
#include <iostream>

void BestZplusLCandSelector::SlaveBegin(TTree *tree) {
  fEntryList = new TEntryList("bestCandidates",
                              "Entry list of disambiguated combinatoric "
                              "candidates after leptons pass tight ID");
  fOutput->Add(fEntryList);
}

void BestZplusLCandSelector::Init(TTree *tree) {
  if (!tree)
    return;
  fChain = tree;
  nEntries = fChain->GetEntries();

  if (!GetInputList())
    throw std::invalid_argument("input list is empty");

  for (std::string branchname : {"run", "evt", "Z1Mass"}) {
    if (GetInputList()->FindObject(branchname.c_str()) == nullptr)
      throw std::invalid_argument("missing input " + branchname);
  }

  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("run"))->GetTitle(), &run, &b_run);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("evt"))->GetTitle(), &evt, &b_evt);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("Z1Mass"))->GetTitle(), &Z1Mass,
      &b_Z1Mass);
}

Bool_t BestZplusLCandSelector::Process(Long64_t entry) {
  b_evt->GetEntry(entry);
  b_run->GetEntry(entry);
  if (run != fCurrentRun || evt != fCurrentEvt)
    findBestEntry();
  fCurrentRun = run;
  fCurrentEvt = evt;

  b_Z1Mass->GetEntry(entry);

  fEntries.push_back(entry);
  fDiscriminants.push_back(fabs(Z1Mass - 91.1876));

  if (entry == nEntries - 1)
    findBestEntry();

  return true;
}

void BestZplusLCandSelector::SlaveTerminate() {
  fEntryList->OptimizeStorage();
  fEntryList = nullptr;
}

void BestZplusLCandSelector::findBestEntry() {
  Long64_t bestEntry = -1;
  float bestDiscriminant = 1e10;

  for (size_t i = 0; i < fEntries.size(); i++) {
    if (fDiscriminants[i] < bestDiscriminant) {
      bestEntry = fEntries[i];
      bestDiscriminant = fDiscriminants[i];
    }
  }

  if (bestEntry >= 0)
    fEntryList->Enter(bestEntry);

  fEntries.clear();
  fDiscriminants.clear();
}

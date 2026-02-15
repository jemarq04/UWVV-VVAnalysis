#include "UWVV/VVAnalysis/interface/BestZZCandSelector.h"
#include <iostream>

void BestZZCandSelector::SlaveBegin(TTree *tree) {
  fEntryList = new TEntryList("bestCandidates",
                              "Entry list of disambiguated combinatoric "
                              "candidates after leptons pass tight ID");
  fOutput->Add(fEntryList);
}

void BestZZCandSelector::Init(TTree *tree) {
  if (!tree)
    return;
  fChain = tree;
  nEntries = fChain->GetEntries();

  if (!GetInputList())
    throw std::invalid_argument("input list is empty");

  for (std::string branchname :
       {"run", "evt", "Z1Mass", "Z2Mass", "l1Pt", "l2Pt", "l3Pt", "l4Pt",
        "l1Tight", "l2Tight", "l3Tight", "l4Tight", "l1Iso", "l2Iso", "l3Iso",
        "l4Iso"}) {
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
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("Z2Mass"))->GetTitle(), &Z2Mass,
      &b_Z2Mass);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l1Pt"))->GetTitle(), &l1Pt,
      &b_l1Pt);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l2Pt"))->GetTitle(), &l2Pt,
      &b_l2Pt);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l3Pt"))->GetTitle(), &l3Pt,
      &b_l3Pt);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l4Pt"))->GetTitle(), &l4Pt,
      &b_l4Pt);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l1Tight"))->GetTitle(), &l1Tight,
      &b_l1Tight);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l2Tight"))->GetTitle(), &l2Tight,
      &b_l2Tight);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l3Tight"))->GetTitle(), &l3Tight,
      &b_l3Tight);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l4Tight"))->GetTitle(), &l4Tight,
      &b_l4Tight);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l1Iso"))->GetTitle(), &l1Iso,
      &b_l1Iso);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l2Iso"))->GetTitle(), &l2Iso,
      &b_l2Iso);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l3Iso"))->GetTitle(), &l3Iso,
      &b_l3Iso);
  fChain->SetBranchAddress(
      ((TNamed *)GetInputList()->FindObject("l4Iso"))->GetTitle(), &l4Iso,
      &b_l4Iso);
}

Bool_t BestZZCandSelector::Process(Long64_t entry) {
  b_evt->GetEntry(entry);
  b_run->GetEntry(entry);
  if (run != fCurrentRun || evt != fCurrentEvt)
    findBestEntry();
  fCurrentRun = run;
  fCurrentEvt = evt;

  b_Z1Mass->GetEntry(entry);
  b_Z2Mass->GetEntry(entry);
  b_l1Pt->GetEntry(entry);
  b_l2Pt->GetEntry(entry);
  b_l3Pt->GetEntry(entry);
  b_l4Pt->GetEntry(entry);
  b_l1Tight->GetEntry(entry);
  b_l2Tight->GetEntry(entry);
  b_l3Tight->GetEntry(entry);
  b_l4Tight->GetEntry(entry);
  b_l1Iso->GetEntry(entry);
  b_l2Iso->GetEntry(entry);
  b_l3Iso->GetEntry(entry);
  b_l4Iso->GetEntry(entry);

  float discriminant, z2PtSum;
  float discriminant_Z1 = fabs(Z1Mass - 91.1876);
  float discriminant_Z2 = fabs(Z2Mass - 91.1876);
  if (discriminant_Z1 < discriminant_Z2) {
    discriminant = discriminant_Z1;
    z2PtSum = l3Pt + l4Pt;
  } else {
    discriminant = discriminant_Z2;
    z2PtSum = l1Pt + l2Pt;
  }

  if (tightZZ()) {
    fTightEntries.push_back(entry);
    fTightDiscriminants.push_back(discriminant);
    fTightZ2PtSums.push_back(z2PtSum);
  } else {
    fLooseEntries.push_back(entry);
    fLooseDiscriminants.push_back(discriminant);
    fLooseZ2PtSums.push_back(z2PtSum);
  }

  if (entry == nEntries - 1)
    findBestEntry();

  return true;
}

void BestZZCandSelector::SlaveTerminate() {
  fEntryList->OptimizeStorage();
  fEntryList = nullptr;
}

bool BestZZCandSelector::tightZZ() {
  return l1Tight && l2Tight && l3Tight && l4Tight && l1Iso && l2Iso && l3Iso &&
         l4Iso;
}

void BestZZCandSelector::findBestEntry() {
  Long64_t bestTightEntry = -1;
  float bestTightDiscriminant = 1e10;
  float bestTightZ2PtSum = 0.0;

  Long64_t bestLooseEntry = -1;
  float bestLooseDiscriminant = 1e10;
  float bestLooseZ2PtSum = 0.0;

  for (size_t i = 0; i < fTightEntries.size(); i++) {
    if (fTightDiscriminants[i] < bestTightDiscriminant ||
        (fTightDiscriminants[i] == bestTightDiscriminant &&
         fTightZ2PtSums[i] > bestTightZ2PtSum)) {
      bestTightEntry = fTightEntries[i];
      bestTightDiscriminant = fTightDiscriminants[i];
      bestTightZ2PtSum = fTightZ2PtSums[i];
    }
  }
  for (size_t i = 0; i < fLooseEntries.size(); i++) {
    if (fLooseDiscriminants[i] < bestLooseDiscriminant ||
        (fLooseDiscriminants[i] == bestLooseDiscriminant &&
         fLooseZ2PtSums[i] > bestLooseZ2PtSum)) {
      bestLooseEntry = fLooseEntries[i];
      bestLooseDiscriminant = fLooseDiscriminants[i];
      bestLooseZ2PtSum = fLooseZ2PtSums[i];
    }
  }

  if (bestTightEntry >= 0)
    fEntryList->Enter(bestTightEntry);
  else if (bestLooseEntry >= 0)
    fEntryList->Enter(bestLooseEntry);

  fTightEntries.clear();
  fTightDiscriminants.clear();
  fTightZ2PtSums.clear();

  fLooseEntries.clear();
  fLooseDiscriminants.clear();
  fLooseZ2PtSums.clear();
}

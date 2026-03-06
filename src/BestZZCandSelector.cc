#include "UWVV/VVAnalysis/interface/BestZZCandSelector.h"

void BestZZCandSelector::SlaveBegin(TTree *tree) {
  // Ensure input list is not empty
  if (GetInputList() == nullptr)
    throw std::logic_error("input list is empty");

  // Define entry list for output list
  fEntryList = new TEntryList("bestCandidates",
                              "Entry list of disambiguated combinatoric "
                              "candidates after leptons pass tight ID");
  fOutput->Add(fEntryList);
}

void BestZZCandSelector::Init(TTree *tree) {
  // Assign tree
  if (!tree)
    return;
  fChain = tree;
  nEntries = fChain->GetEntries();

  // Set all branch addresses
  fChain->SetBranchAddress(GetInput<TNamed>("run")->GetTitle(), &run, &b_run);
  fChain->SetBranchAddress(GetInput<TNamed>("evt")->GetTitle(), &evt, &b_evt);
  fChain->SetBranchAddress(GetInput<TNamed>("Z1Mass")->GetTitle(), &Z1Mass, &b_Z1Mass);
  fChain->SetBranchAddress(GetInput<TNamed>("Z2Mass")->GetTitle(), &Z2Mass, &b_Z2Mass);
  fChain->SetBranchAddress(GetInput<TNamed>("l1Pt")->GetTitle(), &l1Pt, &b_l1Pt);
  fChain->SetBranchAddress(GetInput<TNamed>("l2Pt")->GetTitle(), &l2Pt, &b_l2Pt);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Pt")->GetTitle(), &l3Pt, &b_l3Pt);
  fChain->SetBranchAddress(GetInput<TNamed>("l4Pt")->GetTitle(), &l4Pt, &b_l4Pt);
  fChain->SetBranchAddress(GetInput<TNamed>("l1Tight")->GetTitle(), &l1Tight, &b_l1Tight);
  fChain->SetBranchAddress(GetInput<TNamed>("l2Tight")->GetTitle(), &l2Tight, &b_l2Tight);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Tight")->GetTitle(), &l3Tight, &b_l3Tight);
  fChain->SetBranchAddress(GetInput<TNamed>("l4Tight")->GetTitle(), &l4Tight, &b_l4Tight);
  fChain->SetBranchAddress(GetInput<TNamed>("l1Iso")->GetTitle(), &l1Iso, &b_l1Iso);
  fChain->SetBranchAddress(GetInput<TNamed>("l2Iso")->GetTitle(), &l2Iso, &b_l2Iso);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Iso")->GetTitle(), &l3Iso, &b_l3Iso);
  fChain->SetBranchAddress(GetInput<TNamed>("l4Iso")->GetTitle(), &l4Iso, &b_l4Iso);
}

Bool_t BestZZCandSelector::Process(Long64_t entry) {
  // Check current run/event.
  //  If it is new, check vectors for best entry
  b_evt->GetEntry(entry);
  b_run->GetEntry(entry);
  if (run != fCurrentRun || evt != fCurrentEvt)
    findBestEntry();
  fCurrentRun = run;
  fCurrentEvt = evt;

  // Load variables from branches
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

  // Determine discriminant and Z2 pt sum
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

  // Save discriminant and Z2 pt sum to vector
  if (tightZZ()) {
    fTightEntries.push_back(entry);
    fTightDiscriminants.push_back(discriminant);
    fTightZ2PtSums.push_back(z2PtSum);
  } else {
    fLooseEntries.push_back(entry);
    fLooseDiscriminants.push_back(discriminant);
    fLooseZ2PtSums.push_back(z2PtSum);
  }

  // If this is the last entry, find best one in vectors
  if (entry == nEntries - 1)
    findBestEntry();

  return true;
}

void BestZZCandSelector::SlaveTerminate() {
  // Clean up
  fEntryList->OptimizeStorage();
  fEntryList = nullptr;
}

bool BestZZCandSelector::tightZZ() {
  // Check that all leptons have tight ID and pass isolation
  return l1Tight && l2Tight && l3Tight && l4Tight && l1Iso && l2Iso && l3Iso && l4Iso;
}

void BestZZCandSelector::findBestEntry() {
  // Initialize variables
  Long64_t bestTightEntry = -1;
  float bestTightDiscriminant = 1e10;
  float bestTightZ2PtSum = 0.0;

  Long64_t bestLooseEntry = -1;
  float bestLooseDiscriminant = 1e10;
  float bestLooseZ2PtSum = 0.0;

  // Iterate through tight entries for best one
  for (size_t i = 0; i < fTightEntries.size(); i++) {
    if (fTightDiscriminants[i] < bestTightDiscriminant ||
        (fTightDiscriminants[i] == bestTightDiscriminant && fTightZ2PtSums[i] > bestTightZ2PtSum)) {
      bestTightEntry = fTightEntries[i];
      bestTightDiscriminant = fTightDiscriminants[i];
      bestTightZ2PtSum = fTightZ2PtSums[i];
    }
  }
  // Iterate through loose entries for best one
  for (size_t i = 0; i < fLooseEntries.size(); i++) {
    if (fLooseDiscriminants[i] < bestLooseDiscriminant ||
        (fLooseDiscriminants[i] == bestLooseDiscriminant && fLooseZ2PtSums[i] > bestLooseZ2PtSum)) {
      bestLooseEntry = fLooseEntries[i];
      bestLooseDiscriminant = fLooseDiscriminants[i];
      bestLooseZ2PtSum = fLooseZ2PtSums[i];
    }
  }

  // Save best entry to output entry list
  //  Prioritize one passing tight cuts
  if (bestTightEntry >= 0)
    fEntryList->Enter(bestTightEntry);
  else if (bestLooseEntry >= 0)
    fEntryList->Enter(bestLooseEntry);

  // Clear vectors for next event
  fTightEntries.clear();
  fTightDiscriminants.clear();
  fTightZ2PtSums.clear();

  fLooseEntries.clear();
  fLooseDiscriminants.clear();
  fLooseZ2PtSums.clear();
}

#include "UWVV/VVAnalysis/interface/BestZplusLCandSelector.h"

void BestZplusLCandSelector::SlaveBegin(TTree *tree) {
  // Ensure input list is not empty
  if (GetInputList() == nullptr)
    throw std::logic_error("input list is empty");

  // Define entry list for output list
  fEntryList = new TEntryList("bestCandidates",
                              "Entry list of disambiguated combinatoric "
                              "candidates after leptons pass tight ID");
  fOutput->Add(fEntryList);
}

void BestZplusLCandSelector::Init(TTree *tree) {
  // Assign tree
  if (!tree)
    return;
  fChain = tree;
  nEntries = fChain->GetEntries();

  // Set all branch addresses
  fChain->SetBranchAddress(GetInput<TNamed>("run")->GetTitle(), &run, &b_run);
  fChain->SetBranchAddress(GetInput<TNamed>("evt")->GetTitle(), &evt, &b_evt);
  fChain->SetBranchAddress(GetInput<TNamed>("Z1Mass")->GetTitle(), &Z1Mass, &b_Z1Mass);
}

Bool_t BestZplusLCandSelector::Process(Long64_t entry) {
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

  // Save discriminant to vector
  fEntries.push_back(entry);
  fDiscriminants.push_back(fabs(Z1Mass - 91.1876));

  // If this is the last entry, find best one in vectors
  if (entry == nEntries - 1)
    findBestEntry();

  return true;
}

void BestZplusLCandSelector::SlaveTerminate() {
  // Clean up
  fEntryList->OptimizeStorage();
  fEntryList = nullptr;
}

void BestZplusLCandSelector::findBestEntry() {
  // Initialize variables
  Long64_t bestEntry = -1;
  float bestDiscriminant = 1e10;

  // Iterate through entries for best one
  for (size_t i = 0; i < fEntries.size(); i++) {
    if (fDiscriminants[i] < bestDiscriminant) {
      bestEntry = fEntries[i];
      bestDiscriminant = fDiscriminants[i];
    }
  }

  // Save best entry to output entry list
  if (bestEntry >= 0)
    fEntryList->Enter(bestEntry);

  // Clear vectors for next event
  fEntries.clear();
  fDiscriminants.clear();
}

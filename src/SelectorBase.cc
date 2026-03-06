#include "UWVV/VVAnalysis/interface/SelectorBase.h"

void SelectorBase::SlaveBegin(TTree *tree) {
  // Ensure input list is not empty
  if (GetInputList() == nullptr)
    throw std::logic_error("input list is empty");

  name_ = GetInput<TNamed>("name")->GetTitle();
  isMC_ = name_.find("data") == std::string::npos;
  channel_ = GetInput<TNamed>("channel")->GetTitle();
}

void SelectorBase::Init(TTree *tree) {}

Bool_t SelectorBase::Process(Long64_t entry) { return false; }

void SelectorBase::SlaveTerminate() {}

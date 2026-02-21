#include "UWVV/VVAnalysis/interface/ZplusLFakeRateSelector.h"

void ZplusLFakeRateSelector::SlaveBegin(TTree *tree) {
  SelectorBase::SlaveBegin(tree);
  if (channel_ != "eee" && channel_ != "eem" && channel_ != "emm" && channel_ != "mmm")
    throw std::invalid_argument("invalid channel provided for ZplusL fake rate: " + channel_);
}

void ZplusLFakeRateSelector::Init(TTree *tree) {
  if (!tree)
    return;
  fChain = tree;

  fChain->SetBranchAddress(GetInput<TNamed>("Z1Mass")->GetTitle(), &Z1Mass_, &b_Z1Mass_);

  fChain->SetBranchAddress(GetInput<TNamed>("l1Tight")->GetTitle(), &l1Tight_, &b_l1Tight_);
  fChain->SetBranchAddress(GetInput<TNamed>("l2Tight")->GetTitle(), &l2Tight_, &b_l2Tight_);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Tight")->GetTitle(), &l3Tight_, &b_l3Tight_);
  fChain->SetBranchAddress(GetInput<TNamed>("l1Iso")->GetTitle(), &l1Iso_, &b_l1Iso_);
  fChain->SetBranchAddress(GetInput<TNamed>("l2Iso")->GetTitle(), &l2Iso_, &b_l2Iso_);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Iso")->GetTitle(), &l3Iso_, &b_l3Iso_);

  fChain->SetBranchAddress(GetInput<TNamed>("l3Pt")->GetTitle(), &l3Pt_, &b_l3Pt_);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Eta")->GetTitle(), &l3Eta_, &b_l3Eta_);
  fChain->SetBranchAddress(GetInput<TNamed>("l3MtToMET_")->GetTitle(), &l3MtToMET_, &b_l3MtToMET_);

  fChain->SetBranchAddress("type1_pfMETEt", &type1_pfMETEt_, &b_type1_pfMETEt_);
  if (isMC_)
    fChain->SetBranchAddress("genWeight", &genWeight_, &b_genWeight_);
}

Bool_t ZplusLFakeRateSelector::Process(Long64_t entry) {
  // Load branches
  weight_ = 1;
  b_Z1Mass_->GetEntry(entry);

  b_l1Tight_->GetEntry(entry);
  b_l1Iso_->GetEntry(entry);
  b_l2Tight_->GetEntry(entry);
  b_l2Iso_->GetEntry(entry);

  b_l3Pt_->GetEntry(entry);
  b_l3Eta_->GetEntry(entry);
  b_l3MtToMET_->GetEntry(entry);

  b_type1_pfMETEt_->GetEntry(entry);
  if (isMC_) {
    b_genWeight_->GetEntry(entry);
    weight_ = genWeight_;
  }

  // Apply cuts
  if (Z1Mass_ > 98.1876 || Z1Mass_ < 84.1876)
    return true;
  if (type1_pfMETEt_ > 25)
    return true;
  if (l3MtToMET_ > 30)
    return true;
  if (!l1Tight_ || !l1Iso_ || !l2Tight_ || !l2Iso_)
    return true;

  // Set variables
  float l3AbsEta = std::abs(l3Eta_);

  // Fill loose histograms
  if (channel_ == "eee" || channel_ == "emm") {
    //Electron barrel up to |eta| = 1.479
    if (l3AbsEta < 1.479) {
      // fill 1D electron pt barrel
    } else {
      // fill 1D electron pt endcap
    }
    // fill electron 2D and 1D eta
  } else {
    //Muon barrel up to |eta| = 1.2
    if (l3AbsEta < 1.2) {
      // fill 1D muon pt barrel
    } else {
      // fill 1D muon pt endcap
    }
    // fill muon 2D and 1D eta
  }

  // Fill tight histograms
  if (l3Tight_ && l3Iso_) {
    if (channel_ == "eee" || channel_ == "emm") {
      //Electron barrel up to |eta| = 1.479
      if (l3AbsEta < 1.479) {
        // fill 1D electron pt barrel
      } else {
        // fill 1D electron pt endcap
      }
      // fill electron 2D and 1D eta
    } else {
      //Muon barrel up to |eta| = 1.2
      if (l3AbsEta < 1.2) {
        // fill 1D muon pt barrel
      } else {
        // fill 1D muon pt endcap
      }
      // fill muon 2D and 1D eta
    }
  }

  return true;
}

void ZplusLFakeRateSelector::SlaveTerminate() {}

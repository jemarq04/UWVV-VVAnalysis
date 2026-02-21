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

  fChain->SetBranchAddress(GetInput<TNamed>("Z1Mass")->GetTitle(), &Z1Mass, &b_Z1Mass);

  fChain->SetBranchAddress(GetInput<TNamed>("l1Tight")->GetTitle(), &l1Tight, &b_l1Tight);
  fChain->SetBranchAddress(GetInput<TNamed>("l2Tight")->GetTitle(), &l2Tight, &b_l2Tight);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Tight")->GetTitle(), &l3Tight, &b_l3Tight);
  fChain->SetBranchAddress(GetInput<TNamed>("l1Iso")->GetTitle(), &l1Iso, &b_l1Iso);
  fChain->SetBranchAddress(GetInput<TNamed>("l2Iso")->GetTitle(), &l2Iso, &b_l2Iso);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Iso")->GetTitle(), &l3Iso, &b_l3Iso);

  fChain->SetBranchAddress(GetInput<TNamed>("l3Pt")->GetTitle(), &l3Pt, &b_l3Pt);
  fChain->SetBranchAddress(GetInput<TNamed>("l3Eta")->GetTitle(), &l3Eta, &b_l3Eta);
  fChain->SetBranchAddress(GetInput<TNamed>("l3MtToMET")->GetTitle(), &l3MtToMET, &b_l3MtToMET);

  fChain->SetBranchAddress("type1_pfMETEt", &type1_pfMETEt, &b_type1_pfMETEt);
  if (isMC_)
    fChain->SetBranchAddress("genWeight", &genWeight, &b_genWeight);
}

Bool_t ZplusLFakeRateSelector::Process(Long64_t entry) {
  // Load branches
  weight_ = 1;
  b_Z1Mass->GetEntry(entry);

  b_l1Tight->GetEntry(entry);
  b_l1Iso->GetEntry(entry);
  b_l2Tight->GetEntry(entry);
  b_l2Iso->GetEntry(entry);

  b_l3Pt->GetEntry(entry);
  b_l3Eta->GetEntry(entry);
  b_l3MtToMET->GetEntry(entry);

  b_type1_pfMETEt->GetEntry(entry);
  if (isMC_) {
    b_genWeight->GetEntry(entry);
    weight_ = genWeight;
  }

  // Apply cuts
  if (Z1Mass > 98.1876 || Z1Mass < 84.1876)
    return true;
  if (type1_pfMETEt > 25)
    return true;
  if (l3MtToMET > 30)
    return true;
  if (!l1Tight || !l1Iso || !l2Tight || !l2Iso)
    return true;

  // Set variables
  float l3AbsEta = std::abs(l3Eta);

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
  if (l3Tight && l3Iso) {
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

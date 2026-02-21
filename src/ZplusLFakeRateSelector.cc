#include "UWVV/VVAnalysis/interface/ZplusLFakeRateSelector.h"

void ZplusLFakeRateSelector::SlaveBegin(TTree *tree) {
  SelectorBase::SlaveBegin(tree);
  if (channel_ != "eee" && channel_ != "eem" && channel_ != "emm" && channel_ != "mmm")
    throw std::invalid_argument("invalid channel provided for ZplusL fake rate: " + channel_);

  std::string outpath = GetInput<TNamed>("output")->GetTitle();
  outfile_ = new TFile(outpath.c_str(), "recreate");
  if (outfile_ == nullptr)
    throw std::invalid_argument("error creating file: " + outpath);

  const int numPtBins = 6;
  double ptBins[numPtBins + 1] = {5, 10, 20, 30, 40, 50, 80};

  const int numEleEtaBins = 4;
  double eleEtaBins[numEleEtaBins + 1] = {0.0, 0.7395, 1.479, 2.0, 2.5};

  const int numMuEtaBins = 2;
  double muEtaBins[numMuEtaBins + 1] = {0.0, 1.2, 2.4};

  looseElePt_barrel_ = new TH1D(("looseElePt_barrel_" + channel_).c_str(), "Electron Pt (Barrel)", numPtBins, ptBins);
  looseElePt_endcap_ = new TH1D(("looseElePt_endcap_" + channel_).c_str(), "Electron Pt (Endcap)", numPtBins, ptBins);
  looseMuPt_barrel_ = new TH1D(("looseMuPt_barrel_" + channel_).c_str(), "Muon Pt (Barrel)", numPtBins, ptBins);
  looseMuPt_endcap_ = new TH1D(("looseMuPt_endcap_" + channel_).c_str(), "Muon Pt (Endcap)", numPtBins, ptBins);

  looseEleEta_ = new TH1D(("looseEleEta_" + channel_).c_str(), "Electron Eta", numEleEtaBins, eleEtaBins);
  looseMuEta_ = new TH1D(("looseMuEta_" + channel_).c_str(), "Muon Eta", numMuEtaBins, muEtaBins);

  looseElePtEta_ = new TH2D(
      ("looseElePtEta_" + channel_).c_str(), "Electron Pt vs. Eta", numPtBins, ptBins, numEleEtaBins, eleEtaBins);
  looseMuPtEta_ =
      new TH2D(("looseMuPtEta_" + channel_).c_str(), "Muon Pt vs. Eta", numPtBins, ptBins, numMuEtaBins, muEtaBins);

  tightElePt_barrel_ = new TH1D(("tightElePt_barrel_" + channel_).c_str(), "Electron Pt (Barrel)", numPtBins, ptBins);
  tightElePt_endcap_ = new TH1D(("tightElePt_endcap_" + channel_).c_str(), "Electron Pt (Endcap)", numPtBins, ptBins);
  tightMuPt_barrel_ = new TH1D(("tightMuPt_barrel_" + channel_).c_str(), "Muon Pt (Barrel)", numPtBins, ptBins);
  tightMuPt_endcap_ = new TH1D(("tightMuPt_endcap_" + channel_).c_str(), "Muon Pt (Endcap)", numPtBins, ptBins);

  tightEleEta_ = new TH1D(("tightEleEta_" + channel_).c_str(), "Electron Eta", numEleEtaBins, eleEtaBins);
  tightMuEta_ = new TH1D(("tightMuEta_" + channel_).c_str(), "Muon Eta", numMuEtaBins, muEtaBins);

  tightElePtEta_ = new TH2D(
      ("tightElePtEta_" + channel_).c_str(), "Electron Pt vs. Eta", numPtBins, ptBins, numEleEtaBins, eleEtaBins);
  tightMuPtEta_ =
      new TH2D(("tightMuPtEta_" + channel_).c_str(), "Muon Pt vs. Eta", numPtBins, ptBins, numMuEtaBins, muEtaBins);
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
      looseElePt_barrel_->Fill(l3Pt, weight_);
    } else {
      looseElePt_endcap_->Fill(l3Pt, weight_);
    }
    looseEleEta_->Fill(l3AbsEta, weight_);
    looseElePtEta_->Fill(l3Pt, l3AbsEta, weight_);
  } else {
    //Muon barrel up to |eta| = 1.2
    if (l3AbsEta < 1.2) {
      looseMuPt_barrel_->Fill(l3Pt, weight_);
    } else {
      looseMuPt_endcap_->Fill(l3Pt, weight_);
    }
    looseMuEta_->Fill(l3AbsEta, weight_);
    looseMuPtEta_->Fill(l3Pt, l3AbsEta, weight_);
  }

  // Fill tight histograms
  if (l3Tight && l3Iso) {
    if (channel_ == "eee" || channel_ == "emm") {
      //Electron barrel up to |eta| = 1.479
      if (l3AbsEta < 1.479) {
        tightElePt_barrel_->Fill(l3Pt, weight_);
      } else {
        tightElePt_endcap_->Fill(l3Pt, weight_);
      }
      tightEleEta_->Fill(l3AbsEta, weight_);
      tightElePtEta_->Fill(l3Pt, l3AbsEta, weight_);
    } else {
      //Muon barrel up to |eta| = 1.2
      if (l3AbsEta < 1.2) {
        tightMuPt_barrel_->Fill(l3Pt, weight_);
      } else {
        tightMuPt_endcap_->Fill(l3Pt, weight_);
      }
      tightMuEta_->Fill(l3AbsEta, weight_);
      tightMuPtEta_->Fill(l3Pt, l3AbsEta, weight_);
    }
  }

  return true;
}

void ZplusLFakeRateSelector::SlaveTerminate() {
  outfile_->Write();
  outfile_->Close();
}

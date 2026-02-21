#ifndef ZplusLFakeRateSelector_h
#define ZplusLFakeRateSelector_h

#include "TChain.h"
#include "TFile.h"
#include "TH1.h"
#include "TH2.h"

#include "UWVV/VVAnalysis/interface/SelectorBase.h"

class ZplusLFakeRateSelector : public SelectorBase {
public:
  float Z1Mass;
  bool l1Tight, l2Tight, l3Tight;
  bool l1Iso, l2Iso, l3Iso;
  float l3Pt, l3Eta, l3MtToMET;
  float type1_pfMETEt, genWeight;

  TBranch *b_Z1Mass;
  TBranch *b_l1Tight, *b_l2Tight, *b_l3Tight;
  TBranch *b_l1Iso, *b_l2Iso, *b_l3Iso;
  TBranch *b_l3Pt, *b_l3Eta, *b_l3MtToMET;
  TBranch *b_type1_pfMETEt, *b_genWeight;

  ZplusLFakeRateSelector(TTree *tree = 0) {}
  ~ZplusLFakeRateSelector() override {}
  void SlaveBegin(TTree *tree) override;
  void Init(TTree *tree) override;
  Bool_t Process(Long64_t entry) override;
  void SlaveTerminate() override;

  ClassDefOverride(ZplusLFakeRateSelector, 0);

private:
  TFile *outfile_;
  TH1D *looseElePt_barrel_, *looseElePt_endcap_, *looseEleEta_;
  TH1D *looseMuPt_barrel_, *looseMuPt_endcap_, *looseMuEta_;
  TH2D *looseElePtEta_, *looseMuPtEta_;
  TH1D *tightElePt_barrel_, *tightElePt_endcap_, *tightEleEta_;
  TH1D *tightMuPt_barrel_, *tightMuPt_endcap_, *tightMuEta_;
  TH2D *tightElePtEta_, *tightMuPtEta_;
};

#endif

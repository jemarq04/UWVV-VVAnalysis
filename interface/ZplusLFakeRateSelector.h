#ifndef ZplusLFakeRateSelector_h
#define ZplusLFakeRateSelector_h

#include "TChain.h"

#include "UWVV/VVAnalysis/interface/SelectorBase.h"

class ZplusLFakeRateSelector : public SelectorBase {
public:
  float Z1Mass_;
  bool l1Tight_, l2Tight_, l3Tight_;
  bool l1Iso_, l2Iso_, l3Iso_;
  float l3Pt_, l3Eta_, l3MtToMET_;
  float type1_pfMETEt_, genWeight_;

  TBranch *b_Z1Mass_;
  TBranch *b_l1Tight_, *b_l2Tight_, *b_l3Tight_;
  TBranch *b_l1Iso_, *b_l2Iso_, *b_l3Iso_;
  TBranch *b_l3Pt_, *b_l3Eta_, *b_l3MtToMET_;
  TBranch *b_type1_pfMETEt_, *b_genWeight_;

  ZplusLFakeRateSelector(TTree *tree = 0) {}
  ~ZplusLFakeRateSelector() override {}
  void SlaveBegin(TTree *tree) override;
  void Init(TTree *tree) override;
  Bool_t Process(Long64_t entry) override;
  void SlaveTerminate() override;

  ClassDefOverride(ZplusLFakeRateSelector, 0);

private:
};

#endif

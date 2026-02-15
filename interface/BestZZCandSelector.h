#ifndef BestZZCandSelector_h
#define BestZZCandSelector_h

#include "TChain.h"
#include "TEntryList.h"
#include "TSelector.h"

class BestZZCandSelector : public TSelector {
public:
  TTree *fChain = 0;
  ULong64_t fCurrentEvt;
  UInt_t fCurrentRun;

  ULong64_t evt;
  UInt_t run;
  float Z1Mass, Z2Mass;
  float l1Pt, l2Pt, l3Pt, l4Pt;
  bool l1Tight, l2Tight, l3Tight, l4Tight;
  bool l1Iso, l2Iso, l3Iso, l4Iso;

  TBranch *b_evt, *b_run;
  TBranch *b_Z1Mass, *b_Z2Mass;
  TBranch *b_l1Pt, *b_l2Pt, *b_l3Pt, *b_l4Pt;
  TBranch *b_l1Tight, *b_l2Tight, *b_l3Tight, *b_l4Tight;
  TBranch *b_l1Iso, *b_l2Iso, *b_l3Iso, *b_l4Iso;

  TEntryList *fEntryList = 0;

  BestZZCandSelector(TTree *tree = 0) {}
  ~BestZZCandSelector() override {}
  void SlaveBegin(TTree *tree) override;
  void Init(TTree *tree) override;
  Bool_t Process(Long64_t entry) override;
  void SlaveTerminate() override;

  Int_t Version() const override { return 2; }
  void Begin(TTree *tree) override {};
  Bool_t Notify() override { return true; }
  Int_t GetEntry(Long64_t entry, Int_t getall = 0) override {
    return fChain ? fChain->GetTree()->GetEntry(entry, getall) : 0;
  }
  void SetOption(const char *option) override { fOption = option; }
  void SetObject(TObject *obj) override { fObject = obj; }
  void SetInputList(TList *input) override { fInput = input; }
  TList *GetOutputList() const override { return fOutput; }
  void Terminate() override {}

  ClassDefOverride(BestZZCandSelector, 0);

private:
  bool tightZZ();
  void findBestEntry();
  Long64_t nEntries;
  std::vector<Long64_t> fTightEntries, fLooseEntries;
  std::vector<float> fTightDiscriminants, fLooseDiscriminants;
  std::vector<float> fTightZ2PtSums, fLooseZ2PtSums;
};

#endif

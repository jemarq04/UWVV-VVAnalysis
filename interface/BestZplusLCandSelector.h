#ifndef BestZplusLCandSelector_h
#define BestZplusLCandSelector_h

#include "TChain.h"
#include "TEntryList.h"
#include "TSelector.h"

class BestZplusLCandSelector : public TSelector {
public:
  TTree *fChain = 0;
  ULong64_t fCurrentEvt;
  UInt_t fCurrentRun;

  ULong64_t evt;
  UInt_t run;
  float Z1Mass;

  TBranch *b_evt, *b_run;
  TBranch *b_Z1Mass;

  TEntryList *fEntryList = 0;

  BestZplusLCandSelector(TTree *tree = 0) {}
  ~BestZplusLCandSelector() override {}
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

  ClassDefOverride(BestZplusLCandSelector, 0);

private:
  void findBestEntry();
  Long64_t nEntries;
  std::vector<Long64_t> fEntries;
  std::vector<float> fDiscriminants;
};

#endif

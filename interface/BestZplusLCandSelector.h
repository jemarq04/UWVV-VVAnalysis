#ifndef BestZplusLCandSelector_h
#define BestZplusLCandSelector_h

#include "TChain.h"
#include "TEntryList.h"
#include "TSelector.h"

class BestZplusLCandSelector : public TSelector {
public:
  // See comment on TSelectors in BestZZCandSelector.h

  // Tree variable
  TTree *fChain = 0;

  // Tree values
  ULong64_t evt;
  UInt_t run;
  float Z1Mass;

  // Tree branches
  TBranch *b_evt, *b_run;
  TBranch *b_Z1Mass;

  // Main TSelector methods
  //  These need to be defined for the selector to
  //  run properly.
  BestZplusLCandSelector(TTree *tree = 0) {}
  ~BestZplusLCandSelector() override {}
  void SlaveBegin(TTree *tree) override;
  void Init(TTree *tree) override;
  Bool_t Process(Long64_t entry) override;
  void SlaveTerminate() override;

  // Other TSelector methods
  //  These are defined here, and are not needed in any
  //  children classes. They are required for ROOT to
  //  recognize this class properly.
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

  // Define the selector within ROOT
  ClassDefOverride(BestZplusLCandSelector, 0);

private:
  // === Helper functions ===
  void findBestEntry();

  // Helps retrieve a TObject from the input list with
  //  appropriate checks to make sure not to access
  //  nullptrs
  template <typename T>
  T *GetInput(const char *name) const {
    TObject *input = GetInputList()->FindObject(name);
    if (input == nullptr)
      throw std::invalid_argument("missing input " + (std::string)name);
    else
      return (T *)input;
  }

  // === Member variables ===

  // Entry list of best ZZ candidates
  TEntryList *fEntryList = 0;

  // Current run/event
  ULong64_t fCurrentEvt;
  UInt_t fCurrentRun;

  // Number of entries in tree (to avoid calling function multiple times)
  Long64_t nEntries;

  // Vectors corresponding to quantities per entry. These are used to
  // determine the best ZZ candidate for a given event.
  std::vector<Long64_t> fEntries;
  std::vector<float> fDiscriminants;
};

#endif

#ifndef SelectorBase_h
#define SelectorBase_h

#include "TChain.h"
#include "TSelector.h"

class SelectorBase : public TSelector {
public:
  // See comment on TSelectors in BestZZCandSelector.h

  // Tree variable
  TTree *fChain = 0;

  // Main TSelector methods
  //  These need to be defined for the selector to
  //  run properly.
  SelectorBase(TTree *tree = 0) {}
  ~SelectorBase() override {}
  virtual void SlaveBegin(TTree *tree) override;
  virtual void Init(TTree *tree) override;
  virtual Bool_t Process(Long64_t entry) override;
  virtual void SlaveTerminate() override;

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
  ClassDefOverride(SelectorBase, 0);

protected:
  // === Helper functions ===

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
  std::string name_, channel_;
  bool isMC_;
  float weight_;
};

#endif

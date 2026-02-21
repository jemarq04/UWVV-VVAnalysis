#ifndef SelectorBase_h
#define SelectorBase_h

#include "TChain.h"
#include "TSelector.h"

class SelectorBase : public TSelector {
public:
  TTree *fChain = 0;

  SelectorBase(TTree *tree = 0) {}
  ~SelectorBase() override {}
  virtual void SlaveBegin(TTree *tree) override;
  virtual void Init(TTree *tree) override;
  virtual Bool_t Process(Long64_t entry) override;
  virtual void SlaveTerminate() override;

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

  ClassDefOverride(SelectorBase, 0);

protected:
  std::string name_, channel_;
  bool isMC_;
  float weight_;

  template <typename T>
  T *GetInput(const char *name) const {
    if (GetInputList() == nullptr)
      throw std::logic_error("input list is empty");

    TObject *input = GetInputList()->FindObject(name);
    if (input == nullptr)
      throw std::invalid_argument("missing input " + (std::string)name);
    else
      return (T *)input;
  }
};

#endif

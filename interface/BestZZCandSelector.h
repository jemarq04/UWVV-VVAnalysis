#ifndef BestZZCandSelector_h
#define BestZZCandSelector_h

#include "TChain.h"
#include "TEntryList.h"
#include "TSelector.h"

class BestZZCandSelector : public TSelector {
public:
  // TSelector instances process trees with a given input list and
  // return an output list. The TTree::Process() method attaches the tree
  // to this selector and begins processing code found here. The important
  // methods are the "Main TSelector methods" found below, and they are
  // called in the following order:
  //  1. SlaveBegin() -> Called once per tree, before processing any entries.
  //      This is the best place to define new histograms or other outputs.
  //  2. Init() -> Called once per tree. This is where the tree is assigned, and
  //      where branch addresses should be set so that variables can be accessed.
  //  3. Process() -> Called once per entry in the tree. This is where values should
  //      be loaded from the branches. Make any selections, and fill histograms/outputs
  //      per entry.
  //  4. SlaveTerminate() -> Called once per tree, after processing all entries. This is
  //      the best place to write out any histograms/outputs and clean up any data.

  // Tree variable
  TTree *fChain = 0;

  // Tree values
  ULong64_t evt;
  UInt_t run;
  float Z1Mass, Z2Mass;
  float l1Pt, l2Pt, l3Pt, l4Pt;
  bool l1Tight, l2Tight, l3Tight, l4Tight;
  bool l1Iso, l2Iso, l3Iso, l4Iso;

  // Tree branches
  TBranch *b_evt, *b_run;
  TBranch *b_Z1Mass, *b_Z2Mass;
  TBranch *b_l1Pt, *b_l2Pt, *b_l3Pt, *b_l4Pt;
  TBranch *b_l1Tight, *b_l2Tight, *b_l3Tight, *b_l4Tight;
  TBranch *b_l1Iso, *b_l2Iso, *b_l3Iso, *b_l4Iso;

  // Main TSelector methods
  //  These need to be defined for the selector to
  //  run properly.
  BestZZCandSelector(TTree *tree = 0) {}
  ~BestZZCandSelector() override {}
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
  ClassDefOverride(BestZZCandSelector, 0);

private:
  // === Helper functions ===
  bool tightZZ();
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
  std::vector<Long64_t> fTightEntries, fLooseEntries;
  std::vector<float> fTightDiscriminants, fLooseDiscriminants;
  std::vector<float> fTightZ2PtSums, fLooseZ2PtSums;
};

#endif

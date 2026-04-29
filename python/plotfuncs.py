import argparse

import ROOT


def plot(args: argparse.Namespace):
    """Plot histograms for a given analysis.

    The method to print the histograms is found in this file using globals(). If
    it is not yet defined, an error will be thrown.

    Parameters
    ----------
    args : argparse.Namespace
        A dict-like object parsed from the command-line containing information
        about the plotting job. Contains analysis, year, outfile, etc. Check
        plot.py to see full list.

    """
    method_name = f"plot_{args.analysis}"
    if method_name in globals():
        globals()[method_name](args)
    else:
        raise NotImplementedError(f"plotting function not implemented for analysis: {args.analysis}")


def plot_ZplusL(args: argparse.Namespace):
    """Plot histograms for ZplusL analysis.

    Parameters
    ----------
    args : argparse.Namespace
        A dict-like object parsed from the command-line containing information
        about the plotting job. Contains analysis, year, outfile, etc. Check
        plot.py to see full list.

    """
    from UWVV.VVAnalysis.plottools import ZplusL

    # Create canvas
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    canvas = ROOT.TCanvas("c", "Canvas")

    with ROOT.TFile.Open(args.infile) as infile:
        dymc_dir = infile.Get("AllDY/inclusive")
        data_uncorr_dir = infile.Get("AllData/inclusive")
        data_dir = infile.Get("DataEWKCorrected/inclusive")

        limits = {
            "Ele": {
                "pt": [0.01, 0.08],
                "eta": [0.01, 0.08],
            },
            "Mu": {
                "pt": [0.01, 0.2],
                "eta": [0.01, 0.2],
            },
        }

        for obj in ["Ele", "Mu"]:
            # Plot 1D pt ratios
            # - Get ratios
            ratioPt_barrel, ratioPt_endcap = ZplusL.get_pt_ratios(data_dir, obj, limits[obj]["pt"])
            ratioPt_barrel_uncorr, ratioPt_endcap_uncorr = ZplusL.get_pt_ratios(data_uncorr_dir, obj, limits[obj]["pt"])
            ratioPt_barrel_dymc, ratioPt_endcap_dymc = ZplusL.get_pt_ratios(dymc_dir, obj, limits[obj]["pt"])
            # - Set dashed lines
            ratioPt_barrel.SetLineStyle(2)
            ratioPt_endcap.SetLineStyle(2)
            # - Draw
            ZplusL.draw_pt_ratios(
                obj,
                {"uncorrected": ratioPt_barrel_uncorr, "corrected": ratioPt_barrel},
                {"uncorrected": ratioPt_endcap_uncorr, "corrected": ratioPt_endcap},
                args.lumi_text,
                f"{args.output}/ratio{obj}Pt_Data",
            )
            ZplusL.draw_pt_ratios(
                obj,
                {"Data-EWK": ratioPt_barrel, "DYJets MC": ratioPt_barrel_dymc},
                {"Data-EWK": ratioPt_endcap, "DYJets MC": ratioPt_endcap_dymc},
                args.lumi_text,
                f"{args.output}/ratio{obj}Pt_DataMC",
            )

            # Plot 1D eta ratios
            # - Get ratios
            ratioEta = ZplusL.get_eta_ratio(data_dir, obj, limits[obj]["eta"])
            ratioEta_uncorr = ZplusL.get_eta_ratio(data_uncorr_dir, obj, limits[obj]["eta"])
            ratioEta_dymc = ZplusL.get_eta_ratio(dymc_dir, obj, limits[obj]["eta"])
            # - Set line color
            ratioEta.SetLineColor(ROOT.kRed)
            # - Draw
            ZplusL.draw_eta_ratio(
                obj,
                {"Data": ratioEta_uncorr, "Data-EWK": ratioEta},
                args.lumi_text,
                f"{args.output}/ratio{obj}Eta_Data",
            )
            ZplusL.draw_eta_ratio(
                obj,
                {"Data-EWK": ratioEta, "DYJets MC": ratioEta_dymc},
                args.lumi_text,
                f"{args.output}/ratio{obj}Eta_DataMC",
            )

            # Plot 2D pt vs. eta ratio
            # TODO: 2D (need to invert??)
            ratioPtEta = ZplusL.get_pt_eta_ratio(data_dir, obj)
            ZplusL.draw_pt_eta_ratio(
                obj,
                ratioPtEta,
                args.lumi_text,
                f"{args.output}/ratio{obj}PtEta",
            )

    canvas.Close()


# NOTE: If needed, add more analyses here!
#  To plot new analyses, add a new method with the following signature:
#    def plot_NAME(args: argparse.Namespace):
#  where NAME is the name of the new analysis.

import argparse
import glob
import os
from typing import Optional

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


def get_channels(analysis: str) -> list:
    """Determine list of channels to plot for a given analysis.

    Parameters
    ----------
    analysis : str
        The analysis with the desired channels.

    Returns
    -------
    list of str
        The list of channels for a given analysis.

    """
    channels = []
    if analysis == "ZZ4l":
        channels = ["eeee", "eemm", "mmee", "mmmm", "2e2m"]
    elif analysis == "ZplusL":
        channels = []
    else:
        # NOTE: If needed, add more analyses here!
        raise NotImplementedError(f"no channels found for analysis {analysis}")
    return channels


def write_html(
    path: str, order: list[str], title: str = "Plots", inclusive: bool = True, channels: Optional[list] = None
):
    """Write out index.html file for easy web navigation of created plots.

    Parameters
    ----------
    path : str
        The directory in which to create the index.html file.
    order : list of str
        The ordering of the histograms in the page.
    title : str, optional
        The title of the HTML page (default is 'Plots').
    inclusive : bool, optional
        Whether the plots are inclusive of all channels (default is True).
    channels : list of str or None, optional
        The list of channels to provide hyperlinks to (default is None).

    """
    if channels is None:
        channels = []

    def order_hist(filepath: str):
        name = os.path.basename(filepath).split(".")[0]
        return order.index(name) if name in order else 99

    image_files = glob.glob(os.path.join(path, "plots", "*.png"))
    image_files.sort(key=order_hist)

    style = (
        '  <style type="text/css">\n'
        "    .autoResizeImage {\n"
        "      max-width: 100%;\n"
        "      height: auto;\n"
        "      width: auto;\n"
        "    }\n"
        "  </style>\n"
    )

    with open(f"{path}/index.html", "w") as outfile:
        prefix = "." if inclusive else "../.."

        outfile.write(f"<html>\n<head>\n  <title>{title}</title>\n{style}</head>\n")

        outfile.write("<body>\n")
        outfile.write(f'  <div style="text-align: center;"><b>{title}</b></div>\n')

        outfile.write("  <table>\n")
        outfile.write('  <div style="text-align: center;">Plots by channel:\n')
        outfile.write(f'    <a href="{prefix}">[all]</a>')
        for channel in channels:
            outfile.write(f' - <a href="{prefix}/channels/{channel}">[{channel}]</a>')
        outfile.write("\n  </div>\n  </table>\n  <table>\n")

        for i, image in enumerate(image_files):
            name = os.path.basename(image).split(".")[0]
            if i % 3 == 0:
                outfile.write('  <tr style="text-align: center;">\n')

            outfile.write('    <td style="text-align: center;">\n')
            outfile.write(f'      <img src="plots/{os.path.basename(image)}" class="autoResizeImage"/><br/>\n')
            outfile.write(f'      <a href="logs/{name}.log">[log]</a> -\n')
            outfile.write(f'      <a href="logs/{name}-verbose.log">[verbose log]</a> -\n')
            outfile.write(f'      <a href="plots/{name}.png">[png]</a> -\n')
            outfile.write(f'      <a href="plots/{name}.pdf">[pdf]</a>\n')
            outfile.write("    </td>\n")

            if (i + 1) % 3 == 0:
                outfile.write("  </tr>\n")

        outfile.write("</body>\n</html>\n")


def plot_ZplusL(args: argparse.Namespace):
    """Plot histograms for ZplusL analysis.

    Parameters
    ----------
    args : argparse.Namespace
        A dict-like object parsed from the command-line containing information
        about the plotting job. Contains analysis, year, outfile, etc. Check
        plot.py to see full list.

    """
    from UWVV.VVAnalysis.plotfuncs import ZplusL

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
                f"{args.output}/plots/ratio{obj}Pt_Data",
            )
            ZplusL.draw_pt_ratios(
                obj,
                {"Data-EWK": ratioPt_barrel, "DYJets MC": ratioPt_barrel_dymc},
                {"Data-EWK": ratioPt_endcap, "DYJets MC": ratioPt_endcap_dymc},
                args.lumi_text,
                f"{args.output}/plots/ratio{obj}Pt_DataMC",
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
                f"{args.output}/plots/ratio{obj}Eta_Data",
            )
            ZplusL.draw_eta_ratio(
                obj,
                {"Data-EWK": ratioEta, "DYJets MC": ratioEta_dymc},
                args.lumi_text,
                f"{args.output}/plots/ratio{obj}Eta_DataMC",
            )

            # Plot 2D pt vs. eta ratio
            # TODO: 2D (need to invert??)
            ratioPtEta = ZplusL.get_pt_eta_ratio(data_dir, obj)
            ZplusL.draw_pt_eta_ratio(
                obj,
                ratioPtEta,
                args.lumi_text,
                f"{args.output}/plots/ratio{obj}PtEta",
            )

        write_html(args.output, args.hist_order, title=f"ZZ4l{args.year} Fake Rates")

    canvas.Close()


# NOTE: If needed, add more analyses here!
#  To plot new analyses, add a new method with the following signature:
#    def plot_NAME(args: argparse.Namespace):
#  where NAME is the name of the new analysis.

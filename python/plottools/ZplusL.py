import ROOT
from UWVV.VVAnalysis.CMS_lumi import draw_CMS_label


def get_text_box(obj: str) -> ROOT.TPaveText:
    """Get text box to display lepton.

    Made to match Run 2 plots.

    Parameters
    ----------
    obj : str
        The lepton for the text box. Can be either 'Ele' or 'Mu'.

    Returns
    -------
    ROOT.TPaveText
        Text box to display the lepton fake rate title.

    """
    text_box = ROOT.TPaveText(0.2, 0.88, 0.4, 0.81, "blNDC")
    text_box.SetFillColor(0)
    text_box.SetLineColor(ROOT.kBlack)
    text_box.SetTextFont(42)
    labels = {
        "Ele": "e",
        "Mu": "#mu",
    }
    text_box.AddText(f"{labels[obj]} Fake Rate")
    text_box.SetBorderSize(1)
    return text_box


def get_pt_ratios(tdir: ROOT.TDirectory, obj: str, limits: list[float]) -> tuple[ROOT.TGraphAsymmErrors]:
    """Calculate and configure a set of barrel/endcap fake rate ratio graphs by pt.

    Parameters
    ----------
    tdir : ROOT.TDirectory
        The directory containing the tight/loose histograms.
    obj : str
        The lepton used for the histograms (either 'Ele' or 'Mu').
    limits : list[float]
        List of two floats for the y-axis minimum and maximum, respectively.

    Returns
    -------
    tuple[ROOT.TGraphAsymmErrors]
        A tuple of two ratio graphs for the fake rate in the barrel and endcap,
        respectively.

    """
    # Get 1D pt histograms
    tightPt_barrel = tdir.Get(f"tight{obj}Pt_barrel")
    loosePt_barrel = tdir.Get(f"loose{obj}Pt_barrel")
    ratioPt_barrel = ROOT.TGraphAsymmErrors(tightPt_barrel, loosePt_barrel)
    tightPt_endcap = tdir.Get(f"tight{obj}Pt_endcap")
    loosePt_endcap = tdir.Get(f"loose{obj}Pt_endcap")
    ratioPt_endcap = ROOT.TGraphAsymmErrors(tightPt_endcap, loosePt_endcap)

    # Set styles
    ratioPt_barrel.SetMarkerStyle(6)
    ratioPt_endcap.SetMarkerStyle(6)
    ratioPt_barrel.SetLineColor(ROOT.kBlue)
    ratioPt_endcap.SetLineColor(ROOT.kRed)

    # Set limits
    ratioPt_barrel.SetMinimum(limits[0])
    ratioPt_barrel.SetMaximum(limits[1])
    ratioPt_endcap.SetMinimum(limits[0])
    ratioPt_endcap.SetMaximum(limits[1])

    # Set titles
    #  pt
    ratioPt_barrel.SetTitle("")
    ratioPt_endcap.SetTitle("")
    ratioPt_barrel.GetXaxis().SetTitle("p_{T} [GeV]")
    ratioPt_barrel.GetYaxis().SetTitle("Passing Tight / Passing Loose")

    return ratioPt_barrel, ratioPt_endcap


def draw_pt_ratios(obj: str, barrel: dict, endcap: dict, lumi_text: str, filename: str):
    """Draw ratio plots for barrel and endcap graphs to the current ROOT.TPad.

    Parameters
    ----------
    obj : str
        The lepton used for the fake rates (either 'Ele' or 'Mu').
    barrel : dict
        A dictionary containing the barrel ratio graph(s) to plot. The key is the
        name that will show in the legend and the value is the graph to plot.
    endcap : dict
        A dictionary containing the endcap ratio graph(s) to plot. The key is the
        name that will show in the legend and the value is the graph to plot.
    lumi_text : str
        The luminosity text to display in the CMS label.
    filename : str
        The base name of the output file that will be written from the ROOT.TPad.
        Both a PNG and PDF are written.

    """
    for i, graph in enumerate(barrel.values()):
        if i == 0:
            graph.Draw("PA")
        else:
            graph.Draw("P")
    for graph in endcap.values():
        graph.Draw("P")

    text_box = get_text_box(obj)
    text_box.Draw()

    legend = ROOT.TLegend(0.2, 0.80, 0.40, 0.70)
    for name, graph in barrel.items():
        legend.AddEntry(graph, f"barrel {name}", "l")
    for name, graph in endcap.items():
        legend.AddEntry(graph, f"endcap {name}", "l")
    legend.Draw()

    draw_CMS_label(lumi_text=lumi_text)

    ROOT.gPad.SaveAs(f"{filename}.png")
    ROOT.gPad.SaveAs(f"{filename}.pdf")


def get_eta_ratio(tdir: ROOT.TDirectory, obj: str, limits: list[float]) -> ROOT.TGraphAsymmErrors:
    """Calculate and configure a fake rate ratio graph by eta.

    Parameters
    ----------
    tdir : ROOT.TDirectory
        The directory containing the tight/loose histograms.
    obj : str
        The lepton used for the histograms (either 'Ele' or 'Mu').
    limits : list[float]
        List of two floats for the y-axis minimum and maximum, respectively.

    Returns
    -------
    ROOT.TGraphAsymmErrors
        A ratio graph for the fake rate vs. pseudorapidity.

    """
    # Get 1D eta histograms
    tightEta = tdir.Get(f"tight{obj}Eta")
    looseEta = tdir.Get(f"loose{obj}Eta")
    ratioEta = ROOT.TGraphAsymmErrors(tightEta, looseEta)

    # Set styles
    ratioEta.SetMarkerStyle(6)

    # Set limits
    ratioEta.SetMinimum(limits[0])
    ratioEta.SetMaximum(limits[1])

    # Set titles
    ratioEta.SetTitle("")
    ratioEta.GetXaxis().SetTitle("|#eta|")
    ratioEta.GetYaxis().SetTitle("Passing Tight / Passing Loose")

    return ratioEta


def draw_eta_ratio(obj: str, graphs: dict, lumi_text: str, filename: str):
    """Draw ratio plots for pseudorapidity graphs to the current ROOT.TPad.

    Parameters
    ----------
    obj : str
        The lepton used for the fake rates (either 'Ele' or 'Mu').
    graphs : dict
        A dictionary containing the ratio graph(s) to plot. The key is the
        name that will show in the legend and the value is the graph to plot.
    lumi_text : str
        The luminosity text to display in the CMS label.
    filename : str
        The base name of the output file that will be written from the ROOT.TPad.
        Both a PNG and PDF are written.

    """
    for i, graph in enumerate(graphs.values()):
        if i == 0:
            graph.Draw("PA")
        else:
            graph.Draw("P")

    text_box = get_text_box(obj)
    text_box.Draw()

    legend = ROOT.TLegend(0.2, 0.80, 0.40, 0.70)
    for name, graph in graphs.items():
        legend.AddEntry(graph, name, "l")
    legend.Draw()

    draw_CMS_label(lumi_text=lumi_text)

    ROOT.gPad.SaveAs(f"{filename}.png")
    ROOT.gPad.SaveAs(f"{filename}.pdf")


def get_pt_eta_ratio(tdir: ROOT.TDirectory, obj: str) -> ROOT.TH2:
    """Retrieve and configure the 2D fake rate ratio plot.

    Parameters
    ----------
    tdir : ROOT.TDirectory
        The directory containing the tight/loose histograms.
    obj : str
        The lepton used for the histograms (either 'Ele' or 'Mu').

    Returns
    -------
    ROOT.TH2
        A configured 2D ratio plot for the fake rate.

    """
    # Get 2D pt/eta histogram
    ratioPtEta = tdir.Get(f"ratio{obj}PtEta")

    # Set titles
    ratioPtEta.SetTitle("")
    ratioPtEta.GetXaxis().SetTitle("p_{T} [GeV]")
    ratioPtEta.GetYaxis().SetTitle("|#eta|")

    return ratioPtEta


def draw_pt_eta_ratio(obj: str, hist: ROOT.TH2, lumi_text: str, filename: str):
    """Draw 2D ratio plots to the current ROOT.TPad.

    Parameters
    ----------
    obj : str
        The lepton used for the fake rates (either 'Ele' or 'Mu').
    hist : ROOT.TH2
        A 2D histogram with the fake rate ratio.
    lumi_text : str
        The luminosity text to display in the CMS label.
    filename : str
        The base name of the output file that will be written from the ROOT.TPad.
        Both a PNG and PDF are written.

    """
    hist.Draw("COLZ TEXT")

    text_box = get_text_box(obj)
    text_box.Draw()

    draw_CMS_label(lumi_text=lumi_text)

    ROOT.gPad.SaveAs(f"{filename}.png")
    ROOT.gPad.SaveAs(f"{filename}.pdf")

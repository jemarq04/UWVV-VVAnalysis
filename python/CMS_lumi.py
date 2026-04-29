import ROOT


def draw_CMS_label(extra_text: str = "Preliminary", lumi_text: str = "", com_text: str = "13.6 TeV", size: int = 0.05):
    """Draw CMS label on the current ROOT.TPad.

    Parameters
    ----------
    extra_text : str, optional
        The extra text for the CMS label (e.g. Preliminary, Simulation, etc.). Default is 'Preliminary'.
    lumi_text : str, optional
        The luminosity for the data in the plot, if present (default is '').
    com_text : str, optional
        The center-of-mass energy for the plot (default is '13.6 TeV').
    size : int, optional
        The relative size of the CMS label (default is 0.05).

    """
    ROOT.gPad.Update()

    ycoord = 2 * (ROOT.gPad.GetUymax() - ROOT.gPad.GetUymin()) / 100 + ROOT.gPad.GetUymax()

    label_text = "#font[61]{CMS}"
    if extra_text:
        label_text += f"#scale[0.76]{{#font[52]{{ {extra_text}}}}}"
    textCMS = ROOT.TLatex(ROOT.gPad.GetUxmin(), ycoord, label_text)
    textCMS.SetTextSize(size)
    textCMS.DrawClone()

    if lumi_text:
        text = lumi_text
        if com_text:
            text += f" ({com_text})"
        textInfo = ROOT.TLatex(ROOT.gPad.GetUxmax(), ycoord, f"#font[42]{{{text}}}")
        textInfo.SetTextSize(size * 0.76)
        textInfo.SetTextAlign(ROOT.kHAlignRight + ROOT.kVAlignBottom)
        textInfo.DrawClone()

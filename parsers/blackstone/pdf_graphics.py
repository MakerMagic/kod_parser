"""Keep PDF drawing color spaces so spot-color ink is not mistaken for white."""

from pdfminer.pdfinterp import PDFPageInterpreter
from pdfplumber.page import PDFPageAggregatorWithMarkedContent


class _ColorAwareAggregator(PDFPageAggregatorWithMarkedContent):
    def paint_path(self, gstate, stroke, fill, evenodd, path):
        before = len(self.cur_item._objs)
        super().paint_path(gstate, stroke, fill, evenodd, path)
        # pdfminer retains colors on paths but omits their color spaces.
        # pdfplumber already reads ncs/scs when they exist on layout objects.
        for item in self.cur_item._objs[before:]:
            item.ncs = gstate.ncs
            item.scs = gstate.scs


def load_color_layout(page):
    """Build the usual pdfplumber layout once, adding drawing color spaces."""
    if hasattr(page, "_layout"):
        return
    device = _ColorAwareAggregator(
        page.pdf.rsrcmgr, pageno=page.page_number, laparams=page.pdf.laparams
    )
    PDFPageInterpreter(page.pdf.rsrcmgr, device).process_page(page.page_obj)
    page._layout = device.get_result()


def is_white(color, color_space=None):
    """Recognise white only in understood color spaces; keep unknown ink."""
    if color_space in ("DeviceGray", "CalGray"):
        return color == 1 or color == (1,)
    if color_space in ("DeviceRGB", "CalRGB"):
        return color == (1, 1, 1)
    if color_space == "DeviceCMYK":
        return color == (0, 0, 0, 0)
    if color_space is None:
        # Legacy geometry mocks have only unambiguous RGB/CMYK tuples.
        return color in ((1, 1, 1), (0, 0, 0, 0))
    # A scalar tint in Separation/DeviceN/Indexed is not a gray value.
    return False

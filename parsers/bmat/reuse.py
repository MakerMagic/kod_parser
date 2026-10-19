"""Narrow compatibility boundary for proven, source-independent TSA utilities.

No TSA parse_pdf, metadata, question-boundary rules or cleaner is invoked here.
The original utility modules stay in place to avoid a disruptive module move.
"""

from parsers.blackstone.cid_text import decode_cids, supports_shifted_cids
from parsers.blackstone.image_options import attach_visual_text
from parsers.blackstone.parser import (
    _project_body_exclusions as project_admin_exclusions,
)
from parsers.blackstone.parser import _read_page as read_page
from parsers.blackstone.parser import _split_fields as split_graphic_rows
from parsers.blackstone.parser import validate_raw as validate_contract
from parsers.blackstone.visual_inspection import visual_issues
from parsers.blackstone.visual_structure import add_layout
from parsers.blackstone.visuals import save_visuals

__all__ = [
    "add_layout",
    "attach_visual_text",
    "decode_cids",
    "project_admin_exclusions",
    "read_page",
    "save_visuals",
    "split_graphic_rows",
    "supports_shifted_cids",
    "validate_contract",
    "visual_issues",
]

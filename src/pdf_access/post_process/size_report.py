# Standard Python Libraries
import logging
from pathlib import Path

# Third-Party Libraries
import humanize

from .. import PostProcessBase


class SizeReport(PostProcessBase):
    nice_name = "size-report"

    @classmethod
    def apply(self, in_path: Path, out_path: Path, **kwargs):
        # report the change in size with humanize
        in_size = in_path.stat().st_size
        out_size = out_path.stat().st_size
        percent = (out_size - in_size) / in_size * 100.0
        logging.info(
            "Size change: %s -> %s (%s) %.2f%%",
            humanize.naturalsize(in_size, binary=True),
            humanize.naturalsize(out_size, binary=True),
            humanize.naturalsize(out_size - in_size, binary=True),
            percent,
        )

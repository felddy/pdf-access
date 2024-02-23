# Standard Python Libraries
import logging
from pathlib import Path
import subprocess
import tempfile

from .. import PostProcessBase


class GSCompress(PostProcessBase):
    nice_name = "gs-compress"

    @classmethod
    def apply(self, in_path: Path, out_path: Path, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / out_path.name
            # Create a temporary directory to store the compressed files
            cp: subprocess.CompletedProcess = subprocess.run(
                [
                    "gs",
                    "-DQUIET",
                    "-dNOPAUSE",
                    "-dBATCH",
                    "-sDEVICE=pdfwrite",
                    "-sOutputFile=" + str(temp_file),
                    "-f",
                    out_path,
                ]
            )
            if cp.returncode:
                logging.error("Ghostscript failed to compress %s", in_path)
            else:
                temp_file.replace(out_path)

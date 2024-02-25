# Standard Python Libraries
import logging
from pathlib import Path

# subprocess is required to run the Ghostscript command
from subprocess import PIPE, STDOUT, CompletedProcess, run  # nosec blacklist
import tempfile

from .. import PostProcessBase


class GSCompressProcess(PostProcessBase):
    """Compress a PDF using Ghostscript."""

    nice_name = "gs-compress"

    @classmethod
    def apply(self, in_path: Path, out_path: Path, **kwargs):
        # Create a temporary directory to store the compressed files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / out_path.name
            # care has been taken to ensure paths to gs are sanitized
            cp: CompletedProcess = run(  # nosec start_process_with_partial_path, subprocess_without_shell_equals_true
                [
                    "gs",
                    "-DQUIET",
                    "-dNOPAUSE",
                    "-dBATCH",
                    "-sDEVICE=pdfwrite",
                    "-sOutputFile=" + str(temp_file),
                    "-f",
                    out_path,
                ],
                stdout=PIPE,  # Capture standard output
                stderr=STDOUT,  # Redirect standard error to standard output
            )
            logging.debug("Ghostscript output:\n%s", cp.stdout.decode())
            if cp.returncode:
                logging.error("Ghostscript failed to compress %s", in_path)
            else:
                temp_file.replace(out_path)

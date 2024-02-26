"""Post-process a PDF using Ghostscript to compress it."""

# Standard Python Libraries
import logging
from pathlib import Path

# subprocess is required to run the Ghostscript command
from subprocess import PIPE, STDOUT, CompletedProcess, run  # nosec blacklist
import tempfile

# Third-Party Libraries
import fitz

from .. import PostProcessBase


class GSCompressProcess(PostProcessBase):
    """Compress a PDF using Ghostscript."""

    registry_id = "gs-compress"

    @classmethod
    def apply(self, in_path: Path, out_path: Path) -> None:
        """Compress a PDF using Ghostscript.

        Args:
            in_path: Path to the original document.
            out_path: Path to the modified document.
        """
        # save meta-data
        with fitz.open(in_path) as doc:
            saved_metadata = doc.metadata
            logging.debug("Saved metadata: %s", saved_metadata)

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
                    "-dKeepInfo",
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
                # apply original meta-data
                if saved_metadata:
                    logging.debug("Applying saved metadata")
                    with fitz.open(temp_file) as doc:
                        doc.set_metadata(saved_metadata)
                        doc.saveIncr()
                # replace the original file with the compressed file
                temp_file.replace(out_path)

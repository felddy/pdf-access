"""Post-process a PDF using Ghostscript to compress it."""

# Standard Python Libraries
import io
import logging
from pathlib import Path

# subprocess is required to run the Ghostscript command
from subprocess import PIPE, STDOUT, Popen  # nosec blacklist
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
            temp_file: Path = Path(temp_dir) / out_path.name
            # care has been taken to ensure paths to gs are sanitized
            # Set up the command and arguments for the subprocess
            command: list[str] = [
                "gs",
                "-dNOPAUSE",
                "-dBATCH",
                "-sDEVICE=pdfwrite",
                "-dKeepInfo",
                "-sOutputFile=" + str(temp_file),
                "-f",
                str(out_path),
            ]

            # Start the subprocess with Popen and set stdout and stderr to PIPE to capture them
            # The input is sanitized and does not require a shell
            with Popen(  # nosec: subprocess_without_shell_equals_true
                command,
                stdout=PIPE,
                stderr=STDOUT,
            ) as proc:
                if not proc.stdout:  # TextIOWrapper requires a IO[bytes] object
                    raise Exception("Failed to start Ghostscript subprocess")
                with io.TextIOWrapper(
                    proc.stdout, encoding="utf-8", errors="replace"
                ) as text_io:
                    for line in text_io:
                        logging.debug(line.strip())

                if proc.returncode:
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

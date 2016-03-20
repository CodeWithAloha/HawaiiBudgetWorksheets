#!/usr/bin/env python3

"""Hawaii_Legislature_Budget_Worksheet_Converter.py:
Converts Hawaii State Legislature budget worksheets from PDF format to Tab-Separated-Values (TSV) format for import into a spreadsheet programs.
"""

__author__ = "McKay H Davis"
__date__ = "2016-03-20Z20:08"
__copyright__ = "Copyright 2016"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "McKay Davis"
__email__ = "mckay@codeforhawaii.org"


import subprocess
import sys
import getopt



def main():
    text = pdftotext(sys.argv[1])


def pdftotext(pdf_filename):
    cmd = ["pdftotext",
           "-layout",
           "-fixed 3",
           pdf_filename,
           "-"]
    output = subprocess.check_output(" ".join(cmd), shell=True)
    return output


if __name__ == "__main__":
    main()

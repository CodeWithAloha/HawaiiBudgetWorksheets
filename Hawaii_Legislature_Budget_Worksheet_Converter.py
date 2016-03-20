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
import datetime
import re


def main():
    text = pdftotext(sys.argv[1])
    textpages = text.split("\x0c")
    pages = [HBWSPage(pagetext) for pagetext in textpages[:-1]]
    [page.debug_print() for page in pages]



class HBWSPage:
    """Hawaii Budget Worksheet Page"""
    def __init__(self, text):
        self.lines = text.split("\n")
        self.parse()

    def parse_timestamp(self, line):
        # insert leading 0 for hour in time
        if line[2][1] == ":": line[2] = "0" + line[2]
        timestring = " ".join(line[1:3])
        timeformat = "%A, %B %d, %Y %H:%M:%S %p"
        return datetime.datetime.strptime(timestring, timeformat)

    def parse_pagenum(self, text):
        assert text[:5] == "Page "
        components = text[5:].split(" of ")
        assert len(components) == 2, "pagenum parsing failed to find ' of '"
        return (int(components[0]), int(components[1]))


    def parse_line0(self):
        line0 = re.split(" \s+", self.lines[0])
        assert line0[3] == "LEGISLATIVE BUDGET SYSTEM", "line0 is not header "+"\t".join(line0)
        self.datetime = self.parse_timestamp(line0)
        self.pagenum,self.pages = self.parse_pagenum(line0[-1])

    def parse_header(self):
        self.parse_line0()


    def parse(self):
        self.parse_header()

    def debug_print(self):
        print("datetime", self.datetime)
        print("page num", self.pagenum)
        print("pages", self.pages)


def pdftotext(pdf_filename):
    cmd = ["pdftotext",
           "-layout",
           "-fixed 3",
           pdf_filename,
           "-"]
    buf = subprocess.check_output(" ".join(cmd), shell=True)
    text = buf.decode("utf-8")
    return text


if __name__ == "__main__":
    main()

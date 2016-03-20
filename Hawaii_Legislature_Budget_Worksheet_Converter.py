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
    # remove last page, which is emptyHW
    pages = [HBWSPage(pagetext) for pagetext in textpages[:-1]]



class HBWSPage:
    """Hawaii Budget Worksheet Page"""
    def __init__(self, text):
        self.lines = text.split("\n")
        self.parse_header()
        print(self.debug_str()+"\n")

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

    def assert_linepos_is(self, line, pos, isstr):
        assert line[pos] == isstr, "position {} is not '{}', instead is '{}' -- entire line is: '{}' -- Page debug info: {}".format(pos, isstr, line[pos], "\t".join(line), self.debug_str())


    def parse_line0(self, line):
        line = re.split(" \s+", line)
        self.assert_linepos_is(line, 3, "LEGISLATIVE BUDGET SYSTEM")
        self.datetime = self.parse_timestamp(line)
        self.pagenum, self.pages = self.parse_pagenum(line[-1])

    def parse_line1(self, line):
        line = re.split(" \s+", line)
        self.assert_linepos_is(line, 1, "Detail Type:")
        self.assert_linepos_is(line, 3, "BUDGET WORKSHEET")
        self.detail_type = line[2]


    def parse_department_or_program_id(self, line):
        line = re.split(" \s+", line)
        self.department_summary_page = line[1] == "Department:"
        self.program_page = line[1] == "Program ID"

        if (self.department_summary_page or self.program_page) and len(line) > 2 and len(line[2]) > 3:
            self.department_code = line[2][:3]

        if self.program_page:
            self.program_id = int(line[2][3:])
            self.program_name = line[3]

    def parse_structure_number(self, line):
        line = re.split(" \s+", line)
        self.assert_linepos_is(line, 1, "Structure #:")
        # Keeping as string to preserve leading zeros
        self.structure_number = line[2]

    def parse_subject_committee(self, line):
        line = re.split(" \s+", line)
        assert line[1][:-3] == "Subject Committee: "
        self.subject_committe_code = line[1][-3:]
        self.subject_committe_name = line[2]


    def parse_header(self):
        self.parse_line0(self.lines[0])
        self.parse_line1(self.lines[1])
        lnum = 2
        while lnum < len(self.lines) and self.lines[lnum] == "": lnum += 1
        self.parse_department_or_program_id(self.lines[lnum])
        lnum += 1
        if self.program_page:
            self.parse_structure_number(self.lines[lnum])
            lnum += 1
            self.parse_subject_committee(self.lines[lnum])




    def debug_str(self):
        props = ["datetime", "pagenum", "pages", "detail_type", "department_code", "program_id", "program_name", "structure_number", "subject_committee_code", "subject_committee_name"]
        dstrs = []
        for prop in props:
            val = getattr(self, prop, None)
            if not val is None:
                dstrs.append("{}={}".format(prop, val))
        return "\n".join(dstrs)


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

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
        # split the page text into single lines
        self.text = text.split("\n")
        # split each line into components seperated by two or more spaces
        self.lines = [re.split(" \s+", line) for line in self.text]
        self.curline = 0
        self.parse_page_header()
        self.parse_content_header()

        if self.program_page:
            self.parse_program_page()

        print(self.debug_str()+"\n")

    def parse_page_header(self):
        self.parse_page_header_line0(self.getline())
        self.parse_page_header_line1(self.getline())
        self.eat_empty_lines()

    def parse_content_header(self):
        self.parse_department_or_program_id(self.getline())
        self.eat_empty_lines()

    def eat_empty_lines(self):
        while self.curline < len(self.lines) and self.lines[self.curline] == [""]: self.curline += 1

    def getline(self):
        self.curline += 1
        return self.lines[self.curline-1]

    def parse_program_page(self):
        self.parse_structure_number(self.getline())
        self.parse_subject_committee(self.getline())
        self.eat_empty_lines()
        self.parse_program_table_header(self.getline())
        self.eat_empty_lines()


        seq_len = 24
        seqline = self.curline
        special_seq_id = "- 1"

        sequences = { special_seq_id : [] }
        seq_ids = [special_seq_id]

        while seqline < len(self.text):
            text = self.text[seqline]
            seqline += 1

            seq_id = text[:seq_len].strip()

            if len(seq_id):
                print("Sequence id='{}'".format(seq_id))
                if seq_id != special_seq_id:
                    print("Changing sequence id from '{}' to '{}'".format(seq_ids[-1], seq_id))
                    sequences[seq_id] = []
                    seq_ids.append(seq_id)

            seq_id = seq_ids[-1]
            sequences[seq_id].append(text[seq_len:])

        for seq_id in seq_ids:
            txt = "\n> ".join(['']+sequences[seq_id])
            print("Sequence: {} text={}".format(seq_id, txt))



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
        assert line[pos][:len(isstr)] == isstr, "position {} is not '{}', instead is '{}' -- entire line is: '{}' -- Page debug info: {}".format(pos, isstr, line[pos], "\t".join(line), self.debug_str())


    def parse_page_header_line0(self, line):
        self.assert_linepos_is(line, 3, "LEGISLATIVE BUDGET SYSTEM")
        self.datetime = self.parse_timestamp(line)
        self.pagenum, self.pages = self.parse_pagenum(line[-1])

    def parse_page_header_line1(self, line):
        self.assert_linepos_is(line, 1, "Detail Type:")
        self.assert_linepos_is(line, 2, "BUDGET WORKSHEET")
        self.detail_type = line[1][-1:]

    def parse_department_or_program_id(self, line):
        self.department_summary_page = line[1] == "Department:"
        self.program_page = line[1] == "Program ID"

        if (self.department_summary_page or self.program_page) and len(line) > 2 and len(line[2]) > 3:
            self.department_code = line[2][:3]

        if self.program_page:
            self.program_id = int(line[2][3:])
            self.program_name = line[3]

    def parse_structure_number(self, line):
        self.assert_linepos_is(line, 1, "Structure #:")
        # Keeping as string to preserve leading zeros
        self.structure_number = line[2]

    def parse_subject_committee(self, line):
        assert line[1][:-3] == "Subject Committee: "
        self.subject_committe_code = line[1][-3:]
        self.subject_committe_name = line[2]

    def parse_program_table_header(self, line):
        self.assert_linepos_is(line, 1, "SEQ #")
        self.assert_linepos_is(line, 2, "EXPLANATION")
        assert line[3][:-4] == "FY "
        assert line[4][:-4] == "FY "
        self.year0 = int(line[3][-4:])
        self.year1 = int(line[4][-4:])


    def debug_str(self):
        props = ["datetime", "pagenum", "pages", "detail_type", "department_code", "program_id", "program_name", "structure_number", "subject_committee_code", "subject_committee_name", "year0", "year1"]
        dstrs = []
        for prop in props:
            val = getattr(self, prop, None)
            if not val is None:
                dstrs.append("{}={}".format(prop, val))
        return "\n".join(dstrs)


def pdftotext(pdf_filename):
    cmd = ["pdftotext",
           "-layout",
           "-fixed 4",
           pdf_filename,
           "-"]
    buf = subprocess.check_output(" ".join(cmd), shell=True)
    text = buf.decode("utf-8")
    return text


if __name__ == "__main__":
    main()


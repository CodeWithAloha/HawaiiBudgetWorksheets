#!/usr/bin/env python3
__author__ = "McKay H Davis"
__date__ = "2016-03-20Z20:08"
__copyright__ = "Copyright 2016"
__license__ = "GPLv3"
__version__ = "0.0.2"
__maintainer__ = "McKay Davis"
__email__ = "mckay@codeforhawaii.org"
__doc__ = """
Hawaii_Legislature_Budget_Worksheet_Converter.py:
Converts Hawaii State Legislature budget worksheets from PDF format to Tab-Separated-Values (TSV) format for import into a spreadsheet programs.
"""

PDFTOTEXT_FIXED_PARAM = 4

COL_END_SEQUENCE_NUM = 19
COL_BEG_EXPLANATION_NUM = 21

SPECIAL_EXPLANATIONS = ["BASE APPROPRIATIONS",
                        "TOTAL BUDGET CHANGES",
                        "BUDGET TOTALS",
                        "DEPARTMENT APPROPRIATIONS",
                        "TOTAL DEPARTMENT APPROPRIATIONS",
                        "DEPARTMENT BUDGET CHANGES",
                        "TOTAL DEPARTMENT BUDGET CHANGES",
                        "DEPARTMENT TOTAL BUDGET",
                        "TOTAL DEPARTMENT BUDGET",
                        "TOTAL APPROPRIATIONS",
                        "GRAND TOTAL APPROPRIATIONS",
                        "TOTAL CHANGES",
                        "GRAND TOTAL CHANGES",
                        "GRAND TOTAL BUDGET"]

DESC_DEPT = {
    "Department of Agriculture (DOA)" : "AGR",
    "Department of Accounting and General Services (DAGS)" : "AGS",
    "Department of the Attorney General (AG)" : "ATG",
    "Department of Business, Economic Development, and Tourism (DBEDT)" : "BED",
    "Department of Budget and Finance (B&F)" : "BUF",
    "Department of Commerce and Consumer Affairs (DCCA)" : "CCA",
    "Department of Defense (DOD)" : "DEF",
    "Department of Education (DOE)" : "EDN",
    "Office of the Governor" : "GOV",
    "Department of Hawaiian Home Lands (DHHL)" : "HHL",
    "Department of Human Services (DHS)" : "HMS",
    "Department of Human Resources Development (DHRD) " : "HRD",
    "Department of Health (DOH)" : "HTH",
    "Judiciary" : "JUD",
    "Department of Labor and Industrial Relations (DLIR)" : "LBR",
    "Department of Land and Natural Resources (DLNR)" : "LNR",
    "Office of the Lieutenant Governor (LG)" : "LTG",
    "Department of Public Safety (DPS) " : "PSD",
    "Subsidies" : "SUB",
    "Department of Taxation (DOTAX)" : "TAX",
    "Department of Transportation (DOT)" : "TRN",
    "University of Hawaii (UH)" : "UOH",
    "City and County of Honolulu" : "CCH",
    "County of Hawaii" : "COH",
    "County of Kauai" : "COK",
    "County of Maui" : "COM"
}

DEPT_DESC = { v: k for k, v in DESC_DEPT.items() }


MOF = {
    "A" : "general funds",
    "B" : "special funds",
    "C" : "general obligation bond fund",
    "D" : "general obligation bond fund with debt service cost to be paid from special funds",
    "E" : "revenue bond funds",
    "J" : "federal aid interstate funds",
    "K" : "federal aid primary funds",
    "L" : "federal aid secondary funds",
    "M" : "federal aid urban funds",
    "N" : "federal funds",
    "P" : "other federal funds",
    "R" : "private contributions",
    "S" : "county funds",
    "T" : "trust funds",
    "U" : "interdepartmental transfers",
    "W" : "revolving funds",
    "X" : "other funds"
}



import subprocess
import sys
import getopt
import datetime
import re
import collections
import Spans


def err(txt):
    sys.stderr.write(">>> {}".format(txt))
    sys.stderr.write("\n");

def err_col(line, linenum = None):
    prefix = "" if linenum is None else "[{:3d}] ".format(linenum)
    err(prefix+ "".join("{}".format((i//10)%10) for i in range(0,len (line))))
    err(prefix+"".join("{}".format(i%10) for i in range(0,len (line))))
    err(prefix+line)


def main():
    csv_text = pdf_to_csv(sys.argv[1])

    with open(sys.argv[1][:-4] + ".tsv", "wt") as f:
        f.write(csv_text)

    return 0


def row_cells_to_csv(row, delimiter = "\t"):
    rowtxt = ["" if entry is None else entry for entry in row]
    rowtxt = ['"{}"'.format(ent) for ent in rowtxt]
    rowtxt = delimiter.join(rowtxt)
    return rowtxt


def get_pdf_textpages(pdf_filename):
    text = pdftotext(pdf_filename)

    # split pages at pagebreak char
    textpages = text.split("\x0c")

    # remove last page, which texttopdf creates as an empty page
    textpages = textpages[:-1]

    return textpages


def pdf_to_csv(pdf_filename):
    document_csv_rows = []

    # CSV header
    document_csv_rows += [row_cells_to_csv(HBWSPage.get_spreadsheet_header())]

    textpages = get_pdf_textpages(pdf_filename)

    datetimestr = pdf_creation_datetime(pdf_filename)

    badpages = []

    for pagenum, pagetext in enumerate(textpages):
        # 1-based indexing for pagenum
        pagenum += 1

        try:
            page = HBWSPage(pagetext, datetimestr)
            rows = page.get_spreadsheet_rows()
            page_csv_rows = [row_cells_to_csv(row) for row in rows]
            document_csv_rows += page_csv_rows
        except:
            badpages.append(pagenum)
            err("badpage = {}".format(pagenum))
            raise

    if badpages:
        err("badpages (#{}) = {}".format(len(badpages), badpages))

    return "\n".join(document_csv_rows)


def delchar_at_pos(txt, atpos):
    return txt[:atpos] + txt[atpos+1:]

def inschar_at_pos(txt, char, atpos):
    return txt[:atpos] + char + txt[atpos:]


PROGRAM_SEQUENCES_SPANS = Spans.Spans()
DEPARTMENT_SEQUENCES_SPANS = Spans.Spans()


class HBWSPage:
    """Hawaii Budget Worksheet Page"""
    def __init__(self, text, datetimestr):
        global PROGRAM_SEQUENCES_SPANS, DEPARTMENT_SEQUENCES_SPANS

        self.pdf_creation_datetimestr = datetimestr

        # These lines of exactly 84 asterisks mess up parsing
        # by bleeding into the first FY perm, replace them w/ 25 asterisks
        bad = "*************************************************************************************"
        text = text.replace(bad, "*" * 25 + " " * (len(bad) - 25))

        # split the page text into single lines
        self.text = text.split("\n")

        # split each line into components seperated by two or more spaces
        self.lines = [re.split(" \s+", line) for line in self.text]
        self.curline = 0

        line = self.getline()

        hd1_2017 = datetimestr == "Wed Mar 15 14:45:43 2017"
        if hd1_2017:
            line = ["", "Wednesday, March 15, 2017", "14:45:43 AM"] + line[1:]

        self.parse_page_header_line0(line)
        self.parse_page_header_line1(self.getline())
        self.eat_empty_lines()

        self.parse_department_or_program_id(self.getline())
        self.eat_empty_lines()

        self.fix_2017_exec_sheet_bugs()
        self.fix_2017_hd_sheet_bugs()

        if self.program_page:
            # Parse Program Page
            self.parse_structure_number(self.getline())
            self.parse_subject_committee(self.getline())
            self.eat_empty_lines()
            self.parse_program_table_header_line1(self.getline())
        else:
            assert self.department_summary_page
            line = self.getline()
            self.assert_linepos_is(line, 1, "EX")
            self.assert_linepos_is(line, 2, "FIRST FY")
            self.assert_linepos_is(line, 3, "SECOND FY")


        self.parse_program_table_header_line2(self.getline())
        self.eat_empty_lines()


        self.sequences = self.find_sequence_blocks()

        # various program pages have MOF for Y2 in col 162 (instead of 163)
        # this makes the next parse_sequences_span step fail
        # this hack fixes that by inserting a space in col 162 if needed
        if self.program_page:
            self.hack_sequence_blocks(self.sequences, 162)

        spans = self.parse_sequences_spans(self.sequences)

        global_spans = PROGRAM_SEQUENCES_SPANS if self.program_page else DEPARTMENT_SEQUENCES_SPANS



        if not len(global_spans.ss):
            global_spans = spans
        else:
            new_ss = global_spans.union(spans)

            if len(new_ss.ss) == len(global_spans.ss):
                global_spans = new_ss
                spans = new_ss

            if len(spans.ss) != 9:
            #or self.pagenum in [285, 704, 766, 780, 221]:
                #err("\n{}: {}\n{}: {}\n\n{}: {}".format
                #    (len(spans.ss), spans.ss,
                #     len(global_spans.ss), global_spans.ss,
                #     len(new_ss.ss), new_ss.ss
                #    ))

                err("")
                err("pagenum={}".format(self.pagenum))
                err("spans[{}] = {}".format(len(spans.ss), spans.ss))
                self.print_sequences_spans(self.sequences, spans)

                err("")
                err("global_spans[{}] = {}".format(len(global_spans.ss), global_spans.ss))
                self.print_sequences_spans(self.sequences, global_spans)

                err("")
                err("new_ss[{}] = {}".format(len(new_ss.ss), new_ss.ss))
                self.print_sequences_spans(self.sequences, new_ss)

                for i, line in enumerate(self.text):
                    err_col(line, i)
                input()
                assert 0

        if self.program_page:
            PROGRAM_SEQUENCES_SPANS = global_spans
        else:
            DEPARTMENT_SEQUENCES_SPANS = global_spans

        self.spans = spans


    def fix_2017_exec_sheet_bugs(self):
        if not (self.datetime.year == 2017 and
            self.datetime.month == 2 and
            self.datetime.day == 23):
            return

        if self.pagenum == 576:
            for i in range(18, 22):
                line = self.text[i]
                line = delchar_at_pos(line, -14)
                line = inschar_at_pos(line, " ", -1)
                self.text[i] = line

            for i in range(18, 26):
                self.text[i] = inschar_at_pos(self.text[i], " ", -1)

        if self.pagenum == 1018:
            self.text[30] = delchar_at_pos(self.text[30], 99)
            self.text[30] = inschar_at_pos(self.text[30], " ", 110)
            self.text[30] = delchar_at_pos(self.text[30], -15)
            self.text[30] = inschar_at_pos(self.text[30], " ", -1)
            self.text[20] = self.text[20].replace("GRAND TOTAL      APPROPRIATIONS",
                                                  "     GRAND TOTAL APPROPRIATIONS");



    def fix_2017_hd_sheet_bugs(self):
        if not (self.datetime.year == 2017 and
                self.datetime.month == 3 and
                self.datetime.day == 15):
            return

        if self.pagenum == 1093:
            self.text = [line.replace("GRAND TOTAL      APPROPRIATIONS", "     GRAND TOTAL APPROPRIATIONS") for line in self.text]

        if self.pagenum in [285, 704, 766, 780, 221]:
            self.text = [line.replace(" (", "(").replace(") ", ")  ") for line in self.text]

        #self.text = [re.sub("  \(([0-9,\.]+)\) ([A-Z])", r" (\1)  \2", line) for line in self.text]




    def eat_empty_lines(self):
        while self.curline < len(self.lines) and self.lines[self.curline] == [""]:
            self.curline += 1


    def getline(self):
        self.curline += 1
        return self.lines[self.curline-1]


    def hack_sequence_blocks(self, seq_blocks, special_col):
        for seq_id, seq_lines in seq_blocks.items():
            for i, seq_line in enumerate(seq_lines):
                if special_col < len(seq_line) and seq_line[special_col] != " ":
                    seq_lines[i] = inschar_at_pos(seq_line, " ", special_col)
            seq_blocks[seq_id] = seq_lines
        return seq_blocks

    def find_sequence_blocks(self):
        special_explanations = SPECIAL_EXPLANATIONS

        seq_ids = [special_explanations[0]]
        sequences = collections.OrderedDict()
        sequences[seq_ids[-1]] = []

        for seqline in range(self.curline, len(self.text)):
            linetxt = self.text[seqline]

            seq_id = linetxt[:COL_END_SEQUENCE_NUM].strip()
            text = linetxt[COL_BEG_EXPLANATION_NUM:]

            if not seq_id:
                for special in special_explanations:
                    if text.lstrip().startswith(special):
                        seq_id = special
                        break

            if len(seq_id) and not seq_id == seq_ids[-1]:
                sequences[seq_id] = []
                seq_ids.append(seq_id)

            seq_id = seq_ids[-1]
            sequences[seq_id].append(text)

        for key in sequences.keys():
            if not sequences[key]:
                del sequences[key]
                del seq_ids[seq_ids.index(key)]

        assert list(sorted(seq_ids)) == list(sorted(sequences.keys())), "{}\n{}\n".format(list(sorted(seq_ids)), list(sorted(sequences.keys())))
        return sequences

        return (seq_ids, sequences)


    def parse_sequences_spans(self, sequences, debug = False):
        spans = Spans.Spans()
        for seq, seq_lines in sequences.items():
            for i, seq_line in enumerate(seq_lines):
                line_spans = Spans.Spans.from_text(seq_line)
                spans = spans.union(line_spans)

                if debug:
                    err("-"*120)
                    err("seq_line {}".format(i))
                    err_col(seq_line)
                    err(line_spans.ss)
                    err(line_spans.extract_text(seq_line))
                    err(spans.extract_text(seq_line))
                    err(spans.ss)
                    err("-"*120)

        return spans

    def print_sequences_spans(self, sequences, spans):
        indent = max(len(seq) for seq in sequences.keys())
        for seq, seq_lines in sequences.items():
            for seq_line in seq_lines:
                parts = spans.extract_text(seq_line)
                err("seq: {:30s} ---> {}".format(seq, parts))

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
        assert line[pos].startswith(isstr), "position {} is not '{}', instead is '{}' -- entire line is: '{}' -- Page debug info: {}".format(pos, isstr, line[pos], "\t".join(line), self.debug_str())


    def parse_page_header_line0(self, line):
        self.assert_linepos_is(line, 3, "LEGISLATIVE BUDGET SYSTEM")
        self.datetime = self.parse_timestamp(line)
        self.pagenum, self.pages = self.parse_pagenum(line[4])

    def parse_page_header_line1(self, line):
        self.assert_linepos_is(line, 1, "Detail Type:")
        self.assert_linepos_is(line, 2, "BUDGET WORKSHEET")
        self.detail_type = line[1].split()[-1]

    def parse_department_or_program_id(self, line):
        # There are two types of pages in the Budget Worksheets:
        #   Department and Program
        # Determine which this is
        self.department_summary_page = line[1] == "Department:"
        self.program_page = "Program ID" in line[1]

        if self.pagenum == self.pages:
            self.curline -= 1
            assert not self.program_page and not self.department_summary_page
            self.department_summary_page = True
            return

        # Assert that this is either a department or program page
        assert self.program_page or self.department_summary_page

        if ((self.program_page and len(line) > 2 and len(line[2]) > 3) or
            (self.department_summary_page and len(line) > 2)):
            self.department_code = line[2][:3]
            self.department = DEPT_DESC[self.department_code]

        if self.program_page:
            self.program_id = int(line[2][3:])
            self.program_name = line[3]


    def parse_structure_number(self, line):
        if line[1].startswith("Subject Committee"):
            self.curline -= 1
            return

        self.assert_linepos_is(line, 1, "Structure #:")
        # Keeping as string to preserve leading zeros
        if len(line) == 2:
            self.structure_number = line[1].split()[-1]
        else:
            self.structure_number = line[2]


    def parse_subject_committee(self, line):
        assert line[1][:-3] == "Subject Committee: "
        self.subject_committee_code = line[1][-3:]
        self.subject_committee_name = line[2]


    def parse_program_table_header_line1(self, line):
        self.assert_linepos_is(line, 1, "SEQ #")
        self.assert_linepos_is(line, 2, "EXPLANATION")
        assert line[3][:-4] == "FY "
        assert line[4][:-4] == "FY "
        self.year0 = int(line[3][-4:])
        self.year1 = int(line[4][-4:])


    def parse_program_table_header_line2(self, line):
        assert len(line) == 7, line
        assert line[1] == "Perm", line
        assert line[2] == "Temp", line
        assert line[3] == "Amt", line
        assert line[4] == "Perm", line
        assert line[5] == "Temp", line
        assert line[6] == "Amt", line


    def debug_str(self):
        props = ["datetime", "pagenum", "pages", "detail_type", "department_code", "program_id", "program_name", "structure_number", "subject_committee_code", "subject_committee_name", "year0", "year1"]
        dstrs = []
        for prop in props:
            val = getattr(self, prop, None)
            #if not val is None:
            dstrs.append("{}={}".format(prop, val))

        seq_ids = getattr(self, "seq_ids", [])
        for seq_id in seq_ids:
            dstrs.append("")
            dstrs.append("Sequence ID={}".format(seq_id))
            dstrs.append("Explanation:")
            dstrs.append("\n".join(self.explanations[seq_id]))
            dstrs.append("Line Items:")
            dstrs.append(str(self.line_items[seq_id]))

        return "\n".join(dstrs)


    @staticmethod
    def get_spreadsheet_header():
        props = ["datetime", "pagenum", "pages", "year0", "year1", "detail_type", "department_code", "department", "program_id", "program_name", "structure_number", "subject_committee_code", "subject_committee_name", "sequence_num", "explanation", "pos_perm_y0", "pos_temp_y0", "amt_y0", "mof_y0", "pos_perm_y1", "pos_temp_y1", "amt_y1", "mof_y1",]
        return props


    def get_seq_block_explanation(self, seq_lines):
        exp = [self.spans.extract_text(line, 0) for line in seq_lines]
        exp = [line.rstrip() for line in exp]
        while exp and not exp[0].strip(): exp.pop(0)
        while exp and not exp[-1].strip(): exp.pop(-1)
        while exp and "".join(line[0] if line else "X" for line in exp) == " " * len(exp):
            exp = [line[1:] for line in exp]
        exp = "\n".join(exp)
        return exp


    def filter_duplicate_rows(self, rows, y0_pos_offset):
        newrows = [[]]
        for rowdata in rows:
            lastrow = newrows[-1]
            # Filter total duplicates
            if lastrow == rowdata:
                continue
            # if the entire line up to the actual budget numbers is the same
            if rowdata[:y0_pos_offset] == lastrow[:y0_pos_offset]:
                rstr = "".join([str(e) for e in rowdata[y0_pos_offset:]])
                # ... and the budget numbers for the new row are entirely empty
                if not rstr:
                    # Dont emit this row
                    continue
                lstr = "".join([str(e) for e in lastrow[y0_pos_offset:]])
                # if the budget numbers for the new row are NOT empty
                # and the last row's budget numbers ARE empty
                # then replace the last row with this one
                if not lstr:
                    newrows[-1] = rowdata
                    continue
            newrows.append(rowdata)

        return newrows[1:]


    def get_spreadsheet_rows(self):
        props = self.get_spreadsheet_header()
        rows = []
        row = { prop: getattr(self, prop, "") for prop in props }

        y0_pos_offset = props.index("pos_perm_y0")
        num_seq = len(props) - y0_pos_offset

        for seq_id, seq_lines in self.sequences.items():
            row["sequence_num"] = seq_id
            row["explanation"] = self.get_seq_block_explanation(seq_lines)

            for line in seq_lines:
                parts = self.spans.extract_text(line)

                for i in range(num_seq):
                    numtxt = parts[i+1]
                    numtxt = numtxt.strip()
                    numtxt = numtxt.replace(",", "")
                    row[props[i + y0_pos_offset]] = numtxt

                rowdata = [row[prop] for prop in props]
                rows.append(rowdata)

        rows = self.filter_duplicate_rows(rows, y0_pos_offset)

        return rows



def pdftotext(pdf_filename):
    cmd = ["pdftotext",
           "-layout",
           "-fixed {}".format(PDFTOTEXT_FIXED_PARAM),
           '"'+pdf_filename+'"',
           "-"]
    buf = subprocess.check_output(" ".join(cmd), shell=True)
    text = buf.decode("utf-8")
    return text


def pdf_creation_datetime(pdf_filename):
    cmd = ["pdfinfo",
           "-meta",
           '"'+pdf_filename+'"']
    buf = subprocess.check_output(" ".join(cmd), shell=True)
    text = buf.decode("utf-8")
    cdate = [line for line in text.split("\n") if line.startswith("CreationDate:")]
    datetimestr = "" if not cdate else cdate[0].split("CreationDate:")[-1].strip()

    return datetimestr


if __name__ == "__main__":
    main()

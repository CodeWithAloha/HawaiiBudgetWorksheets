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


PDFTOTEXT_FIXED_PARAM = 4
COL_END_SEQUENCE_NUM = 24
COL_END_EXPLANATION_PROGRAM = 86
COL_END_EXPLANATION_DEPT_SUMMARY = 46
TEXT_BASE_APPROPRIATIONS = "BASE APPROPRIATIONS"
TEXT_TOTAL_BUDGET_CHANGES = "TOTAL BUDGET CHANGES"
TEXT_BUDGET_TOTALS = "BUDGET TOTALS"
TEXT_DEPARTMENT_APPROPRIATIONS = "DEPARTMENT APPROPRIATIONS"
TEXT_TOTAL_DEPARTMENT_APPROPRIATIONS = "TOTAL DEPARTMENT APPROPRIATIONS"
TEXT_DEPARTMENT_BUDGET_CHANGES = "DEPARTMENT BUDGET CHANGES"
TEXT_TOTAL_DEPARTMENT_BUDGET_CHANGES = "TOTAL DEPARTMENT BUDGET CHANGES"
TEXT_DEPARTMENT_TOTAL_BUDGET = "DEPARTMENT TOTAL BUDGET"
TEXT_TOTAL_DEPARTMENT_BUDGET = "TOTAL DEPARTMENT BUDGET"
SPECIAL_EXPLANATIONS = [TEXT_BASE_APPROPRIATIONS, TEXT_TOTAL_BUDGET_CHANGES, TEXT_BUDGET_TOTALS, TEXT_DEPARTMENT_APPROPRIATIONS, TEXT_TOTAL_DEPARTMENT_APPROPRIATIONS, TEXT_DEPARTMENT_BUDGET_CHANGES, TEXT_TOTAL_DEPARTMENT_BUDGET_CHANGES, TEXT_DEPARTMENT_TOTAL_BUDGET, TEXT_TOTAL_DEPARTMENT_BUDGET, "TOTAL APPROPRIATIONS", "GRAND TOTAL APPROPRIATIONS", "TOTAL CHANGES", "GRAND TOTAL CHANGES", "GRAND TOTAL BUDGET"]


COL_BEG_FY0_POS = 5
COL_END_FY0_POS = 16
COL_BEG_FY0_AMT = 18
COL_END_FY0_AMT = 33
COL_BEG_FY0_MOF = 35
COL_END_FY0_MOF = 35

COL_BEG_FY1_POS = 44
COL_END_FY1_POS = 55
COL_BEG_FY1_AMT = 57
COL_END_FY1_AMT = 72
COL_BEG_FY1_MOF = 73
COL_END_FY1_MOF = 76



DESC_DEPT = {
    "Department of Accounting and General Services (DAGS)" : "AGS",
    "Department of Agriculture (DOA)" : "AGR",
    "Department of the Attorney General (AG)" : "ATG",
    "Department of Budget and Finance (B&F)" : "BUF",
    "Department of Business, Economic Development, and Tourism (DBEDT)" : "BED",
    "Department of Commerce and Consumer Affairs (DCCA)" : "CCA",
    "Department of Defense (DOD)" : "DEF",
    "Department of Education (DOE)" : "EDN",
    "Office of the Governor" : "GOV",
    "Department of Hawaiian Home Lands (DHHL)" : "HHL",
    "Department of Health (DOH)" : "HTH",
    "Department of Human Resources Development (DHRD) " : "HRD",
    "Department of Human Services (DHS)" : "HMS",
    "Department of Labor and Industrial Relations (DLIR)" : "LBR",
    "Department of Land and Natural Resources (DLNR)" : "LNR",
    "Office of the Lieutenant Governor (LG)" : "LTG",
    "Department of Public Safety (DPS) " : "PSD",
    "Department of Taxation (DOTAX)" : "TAX",
    "Department of Transportation (DOT)" : "TRN",
    "University of Hawaii (UH)" : "UOH",
    "Subsidies" : "SUB",
    "City and County of Honolulu" : "CCH",
    "County of Hawaii" : "COH",
    "County of Kauai" : "COK",
    "County of Maui" : "COM"
}

DEPT_DESC = { v: k for k, v in DESC_DEPT.items() }



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
    #for page in pages:
    #    print(page.debug_str())
    text = get_spreadsheet(pages);
    print(text)



def get_spreadsheet(pages, delimiter="\t"):
    text = []
    DELIMITER = "\t"
    header = True
    for page in pages:
        for row in page.get_spreadsheet_rows(header):
            header = False
            row = ['""' if ent is None else ent for ent in row]
            text.append(DELIMITER.join(row))
    return "\n".join(text)




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
        else:
            if self.department_summary_page:
                line = self.getline()
                self.assert_linepos_is(line, 1, "EX PLANATION")
                self.assert_linepos_is(line, 2, "FIRST FY")
                self.assert_linepos_is(line, 3, "SECOND FY")
            self.eat_empty_lines()
            self.parse_sequences(COL_END_EXPLANATION_DEPT_SUMMARY)

        #print(self.debug_str()+"\n")

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
        self.parse_sequences(COL_END_EXPLANATION_PROGRAM)


    def parse_sequences(self, col_end_explanation):
        (seq_ids, sequences) = self.parse_sequences_step1()
        self.parse_sequences_step2(seq_ids, sequences, col_end_explanation)


    def parse_sequences_step1(self):
        seq_len = COL_END_SEQUENCE_NUM
        seqline = self.curline

        special_explanations = SPECIAL_EXPLANATIONS

        seq_ids = [special_explanations[0]]
        sequences = { seq_ids[-1] : [] }

        while seqline < len(self.text):
            text = self.text[seqline]
            seqline += 1

            seq_id = text[:seq_len].strip()
            text = text[seq_len:]

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

        return (seq_ids, sequences)

    def parse_sequences_step2(self, seq_ids, sequences, col_end_explanation):
        self.explanations = {}
        self.line_items = {}
        self.seq_ids = []

        for seq_id in seq_ids:
            ex, li = self.parse_sequence(seq_id, sequences[seq_id], col_end_explanation)
            if len(ex) or len(li):
                self.explanations[seq_id], self.line_items[seq_id] = (ex, li)
                self.seq_ids.append(seq_id)



    def parse_sequence(self, seq_id, lines, col_end_explanation):
        explanations = []
        line_items = []
        for line in lines:
            explanation = line[:col_end_explanation]
            #print("EXPLANATION FROM:'{}' TO '{}'".format(line, explanation))
            explanation = explanation.rstrip()
            if explanation.lstrip().startswith(seq_id): explanation = explanation.lstrip();
            if explanation: explanations.append(explanation)

            line = line[col_end_explanation:]
            line_item = self.parse_line_item(line)
            line_items.append(line_item)

        while len(line_items) > 1 and not "".join(line_items[-1]) and not "".join(line_items[-2]): line_items = line_items[:-1]

        return (explanations, line_items)

    def parse_line_item(self, line):
        fy0_pos = line[COL_BEG_FY0_POS:COL_END_FY0_POS+1]
        fy0_amt = line[COL_BEG_FY0_AMT:COL_END_FY0_AMT+1]
        fy0_mof = line[COL_BEG_FY0_MOF:COL_END_FY0_MOF+1]
        fy1_pos = line[COL_BEG_FY1_POS:COL_END_FY1_POS+1]
        fy1_amt = line[COL_BEG_FY1_AMT:COL_END_FY1_AMT+1]
        fy1_mof = line[COL_BEG_FY1_MOF:COL_END_FY1_MOF+1]
        result = [txt.strip(' *') for txt in [fy0_pos, fy0_amt, fy0_mof, fy1_pos, fy1_amt, fy1_mof]]

        if 0:
            print("parse:")
            print(line)
            print("00000000001111111111222222222233333333334444444444555555555566666666667777777777")
            print("0123456789"*8)
            print()
            print("parsed:",result)

        return result


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
        self.pagenum, self.pages = self.parse_pagenum(line[-1])

    def parse_page_header_line1(self, line):
        self.assert_linepos_is(line, 1, "Detail Type:")
        self.assert_linepos_is(line, 2, "BUDGET WORKSHEET")
        self.detail_type = line[1][-1:]

    def parse_department_or_program_id(self, line):
        self.department_summary_page = line[1] == "Department:"
        self.program_page = line[1] == "Program ID"

        if ((self.program_page and len(line) > 2 and len(line[2]) > 3) or
            (self.department_summary_page and len(line) > 2)):
            self.department_code = line[2][:3]
            self.department = DEPT_DESC[self.department_code]

        if self.program_page:
            self.program_id = int(line[2][3:])
            self.program_name = line[3]

    def parse_structure_number(self, line):
        self.assert_linepos_is(line, 1, "Structure #:")
        # Keeping as string to preserve leading zeros
        self.structure_number = line[2]

    def parse_subject_committee(self, line):
        assert line[1][:-3] == "Subject Committee: "
        self.subject_committee_code = line[1][-3:]
        self.subject_committee_name = line[2]

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

        seq_ids = getattr(self, "seq_ids", [])
        for seq_id in seq_ids:
            dstrs.append("")
            dstrs.append("Sequence ID={}".format(seq_id))
            dstrs.append("Explanation:")
            dstrs.append("\n".join(self.explanations[seq_id]))
            dstrs.append("Line Items:")
            dstrs.append(str(self.line_items[seq_id]))

        return "\n".join(dstrs)


    def get_spreadsheet_header(self):
        props = ["datetime", "pagenum", "pages", "year0", "year1", "detail_type", "department_code", "department", "program_id", "program_name", "structure_number", "subject_committee_code", "subject_committee_name", "sequence_num", "explanation", "pos_y0", "amt_y0", "mof_y0", "pos_y1", "amt_y1", "mof_y1",]
        return props


    def get_spreadsheet_rows(self, emit_header = False):
        props = self.get_spreadsheet_header()
        seq_ids = getattr(self, "seq_ids", [])
        rows = []
        row = [str(getattr(self, prop, "")) for prop in props]
        idxof = dict(zip(props, range(len(props))))
        for seq_id in seq_ids:
            row[idxof["sequence_num"]] = seq_id
            row[idxof["explanation"]] = "\\n".join(self.explanations[seq_id])
            line_items = self.line_items[seq_id] if len(self.line_items[seq_id]) else [[None]*6]
            for line_item in line_items:
                row[idxof["pos_y0"]],row[idxof["amt_y0"]],row[idxof["mof_y0"]] = line_item[0:3]
                row[idxof["pos_y1"]],row[idxof["amt_y1"]],row[idxof["mof_y1"]] = line_item[3:6]
                rows.append(row[:])

        return [props] + rows if emit_header else rows



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

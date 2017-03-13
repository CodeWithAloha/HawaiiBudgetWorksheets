__author__ = "McKay H Davis"
__date__ = "2017-03-13Z11:47"
__copyright__ = "Copyright 2017"
__license__ = "GPLv3"
__maintainer__ = "McKay Davis"
__email__ = "mckay@codeforhawaii.org"
__doc__ = """
Spans.py:
Python class to handle 1D spans, used to deduce columns in text output from pdftotext
"""

class Spans(object):
    neg_inf = float('-inf')
    pos_inf = float('inf')
    range_all = (neg_inf, pos_inf)
    def __init__(self, a = None, b = None, quant = None):
        self.ss = []
        if a is not None and b is not None:
            if quant:
                a = int(math.floor(a/quant)+0.1)
                b = int(math.floor(b/quant)+0.1)

            self.ss = [(a,b)]



    def __str__(self):
        return "{}".format(self.ss)

    @staticmethod
    def _combine(*args):
        result = []

        for sss in args:
            result += [(s[0], 0) for s in sss.ss]
            result += [(s[1], 1) for s in sss.ss]

        result = list(sorted(result))

        return result

    def union(self, them):
        both = []
        count = 0
        combined = Spans._combine(self, them)
        for s in combined:
            if s[1] == 0:
                count += 1
                if count == 1:
                    left = s[0]
            else:
                count -= 1
                if count == 0:
                    both.append((left, s[0]))

        res = Spans()
        res.ss = both

        return res


    def intersect(self, them):
        both = []
        count = 0
        for s in Spans._combine(self,them):
            if s[1] == 0:
                count += 1
                if count == 2:
                    left = s[0]
            else:
                count -= 1
                if count == 1:
                    both.append((left, s[0]))

        res = Spans()
        res.ss = both

        return res

    def index(self, span):
        i = 0
        while i < len(self.ss) and span[0] > self.ss[i][1]:
            i += 1
        if i < len(self.ss) and span[0] <= self.ss[i][1]:
            assert span[0] >= self.ss[i][0], "span={} ss[{}]={}".format(span, i, self.ss[i])
            assert span[1] <= self.ss[i][1], "span={} ss[{}]={}".format(span, i, self.ss[i])
            return i
        return -1


    @staticmethod
    def from_text(text):
        spans = Spans()
        char_spans = [Spans(i, i+1) for i, char in enumerate(text) if char != " "]
        for char_span in char_spans:
            spans = spans.union(char_span)
        return spans


    def to_text():
        txt = ""
        for span in this.ss:
            txt += " " * span[0]
            txt += "*" * span[1]
        return text()


    def extract_text(self, text, column=None):
        ss = self.ss
        if column is None:
            if ss:
                text = text + " "*(ss[-1][1] - len(text))
            return [text[a:b] for a,b in ss]
        elif column >= len(ss):
            return None
        else:
            return text[ss[column][0]:ss[column][1]]

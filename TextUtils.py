def BinaryApprox1(List, Val):
    Len = len(List)
    CurLen = Len
    Pos = Len >> 1
    while CurLen > 0:
        if (Pos+1 >= len(List) or Val < List[Pos+1]) and  Val >= List[Pos]:
            return Pos
        elif Val < List[Pos]:
            CurLen >>= 1
            Pos -= (CurLen + 1) >> 1
        else:
            CurLen = (CurLen - 1) >> 1
            Pos += (CurLen >> 1) + 1
    return Len

class TextLineView(object):
    def __init__(self, Str, LineSep="\n"):
        self.Str = list()
        self.LineSep = "\n"
        self.Lines = []
        self.SetStr(Str, LineSep)
    def SetStr(self, Str, LineSep=None):
        if LineSep is None: LineSep = self.LineSep
        else: self.LineSep = LineSep
        self.Lines = [0] * (Str.count(LineSep)+1)
        Pos = 0
        for c in xrange(1, len(self.Lines)):
            Pos = Str.find(LineSep, Pos) + len(LineSep)
            self.Lines[c] = Pos
        self.Str = list(Str)
    def GetRowLen(self, Row):
        if Row >= len(self.Lines):
            raise ValueError("Row too big")
        return (self.Lines[Row+1] if Row + 1 < len(self.Lines) else len(self.Str)) - self.Lines[Row]
    def GetDrawRowLen(self, Row):
        if Row >= len(self.Lines):
            raise ValueError("Row too big")
        return (self.Lines[Row+1]-len(self.LineSep) if Row + 1 < len(self.Lines) else len(self.Str)) - self.Lines[Row]
    def RowColToPos(self, Col, Row):
        if Col > self.GetRowLen(Row):
            raise ValueError("Column too big for row %u of length %u"%(Row,self.GetRowLen(Row)))
        return self.Lines[Row] + Col
    def tRowColToPos(self, ColRow):
        Col, Row = ColRow
        if Col > self.GetRowLen(Row):
            raise ValueError("Column too big for row %u of length %u"%(Row, self.GetRowLen(Row)))
        return self.Lines[Row] + Col
    def PosToRowCol(self, Pos):
        if Pos > len(self.Str):
            raise ValueError("Pos out of range of Str")
        Row = BinaryApprox1(self.Lines, Pos)
        if Row >= len(self.Lines) and Row > 0: Row = len(self.Lines)-1
        Col = Pos - self.Lines[Row]
        return [Col, Row]
    def GetDrawRow(self, Row):
        End = (self.Lines[Row + 1] - len(self.LineSep)) if Row + 1 < len(self.Lines) else len(self.Str)
        return u"".join(self.Str[self.Lines[Row]:End]).replace("\0", "\x1b")
    def Insert(self, Str, Pos):
        if Str.count(self.LineSep) == 0:
            Col, Row = self.PosToRowCol(Pos)
            self.Str[Pos:Pos] = Str
            for c in xrange(Row+1, len(self.Lines)):
                self.Lines[c] += len(Str)
        else:
            self.Str[Pos:Pos] = Str
            Col, Row = self.PosToRowCol(Pos)
            Lines = [0] * (Str.count(self.LineSep))
            PrevPos = 0
            for c in xrange(len(Lines)):
                PrevPos = Str.find(self.LineSep, PrevPos)
                Lines[c] = PrevPos + Pos
                PrevPos += len(self.LineSep)
            for c in xrange(Row+1, len(self.Lines)):
                self.Lines[c] += len(Str)
            self.Lines[Row+1:Row+1] = Lines
            #self.SetStr(self.Str[:Pos] + Str + self.Str[Pos:])
    def Replace(self, Str, Pos0, Pos1):
        self.SetStr(u"".join(self.Str[:Pos0]) + Str + u"".join(self.Str[Pos1:]))
    def Delete(self, Pos0, Pos1):
        self.SetStr(u"".join(self.Str[:Pos0]) + u"".join(self.Str[Pos1:]))
    def GetStr(self, Pos0, Pos1):
        return u"".join(self.Str[Pos0:Pos1])
class ClipboardHandler(object):
    def put(self, typ, data):
        pass
    def get(self, typ):
        pass
if __name__ == "__main__":
    Lst = [0, 12, 23, 33]
    for c in xrange(Lst[-1] + 12):
        Res = BinaryApprox1(Lst, c)
        assert Lst[Res] <= c
        if Res+1 < len(Lst):
            assert c < Lst[Res+1]
    Inst = TextLineView("hello\nhi\n\nnever")
    assert Inst.Lines == [0,6, 9, 10]
    print map(Inst.PosToRowCol, xrange(len(Inst.Str)))
    Inst.Insert("hi", 9)
    print Inst.Lines, repr(Inst.Str)
    assert Inst.Lines == [0, 6, 9, 12]
    print Inst.Str
    Inst.Insert("\nhehi", Inst.RowColToPos(2, 2))
    print Inst.Str
    assert Inst.Lines == [0, 6, 9, 12, 17]
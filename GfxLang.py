from InetProt import DataPacker
from InetProt import DataObj,DataLong,DataInt,DataVarBytes,\
    DataArray,DataCondFmt,DataVarFmt
import pygame

GfxCmdNames = [] # the source code names like $pop$
GfxCmdNAMES = [] # the constant names like GFX_CMD_DISCARD
GfxCmds = []
class GfxCmd(object):
    ErrFmt1 = "%s.__call__ (Id=%s ($%s$)) expected %u (given %u)"
    def FormatError1(self, args):
        return self.ErrFmt1 % (
            self.__class__.__name__, GfxCmdNAMES[self.CmdId],
            GfxCmdNames[self.CmdId], len(self.Args), len(args))
    def __init__(self, CmdId, Args, Func, IsSpecial=False):
        self.CmdId = CmdId
        self.Args = Args
        self.Func = Func
        self.IsSpecial = IsSpecial
        self.ResCmdPtr = False
    def __call__(self, *args):
        if len(args) != len(self.Args):
            raise TypeError(self.FormatError1(args))
        try:
            return self.Func(*args)
        except StandardError as Exc:
            NamePair = GfxCmdNAMES[self.CmdId],GfxCmdNames[self.CmdId]
            raise StandardError(Exc, "CmdId = %s ($%s$)"%NamePair)
class StackGfxCmd(GfxCmd):
    def __init__(self, CmdId, StackChk, Func, StackChkArgs=(), ResCmdPtr=False):
        super(StackGfxCmd, self).__init__(CmdId, [], Func)
        self.CmdId = CmdId
        self.StackChk = StackChk
        self.Func = Func
        self.StackChkArgs = StackChkArgs
        self.ResCmdPtr = ResCmdPtr
    def __call__(self, Stack, CmdPtr):
        Chk = self.StackChk(Stack, *self.StackChkArgs)
        if Chk is not None:
            NamePair = GfxCmdNAMES[self.CmdId], GfxCmdNames[self.CmdId]
            raise ValueError(Chk + ";CmdId = %s ($%s$)"%NamePair)
        return self.Func(Stack)
class ComplexGfxCmd(StackGfxCmd):
    def __init__(self, CmdId, StackChk, Func, StackChkArgs=(), ResCmdPtr=True):
        super(ComplexGfxCmd, self).__init__(CmdId, StackChk, Func, StackChkArgs, ResCmdPtr)
    def __call__(self, Stack, CmdPtr):
        Chk = self.StackChk(Stack, *self.StackChkArgs)
        if Chk is not None:
            NamePair = GfxCmdNAMES[self.CmdId], GfxCmdNames[self.CmdId]
            raise ValueError(Chk + ";CmdId = %s ($%s$)" % NamePair)
        return self.Func(Stack, CmdPtr)
def CheckSzStack(Stack, Sz=1):
    if len(Stack) < Sz:
        return "Not enough args on stack"
def SwapList(Lst, i0, i1):
    Tmp = Lst[i0]
    Lst[i0] = Lst[i1]
    Lst[i1] = Tmp
class GfxCmdFiller(object):
    def __init__(self, Len, LstCONST, LstName, LstCmds):
        self.Len = Len
        LstCONST[:] = [None] * Len
        LstName[:] = [None] * Len
        LstCmds[:] = [None] * Len
        self.Lst0 = LstCONST
        self.Lst1 = LstName
        self.Lst2 = LstCmds
        self.NextPos = 0
    def Alloc(self, Obj0, Obj1, Cls2, *ArgsCls):
        Rtn = self.NextPos
        if Rtn >= self.Len:
            raise ValueError(
                "Not enough command slots allocated for %s, %s"%(Obj0, Obj1))
        Obj2 = Cls2(Rtn, *ArgsCls)
        self.NextPos += 1
        self.Lst0[Rtn] = "GFX_CMD_" + Obj0
        self.Lst1[Rtn] = Obj1
        self.Lst2[Rtn] = Obj2
        return Rtn
GfxCmdAlloc = GfxCmdFiller(40, GfxCmdNAMES, GfxCmdNames, GfxCmds)
GFX_CMD_DISCARD =   GfxCmdAlloc.Alloc(
    "DISCARD","pop", StackGfxCmd,
    CheckSzStack, lambda Stack: Stack.pop())
GFX_CMD_COPY =      GfxCmdAlloc.Alloc(
    "COPY",   "copy", StackGfxCmd,
    CheckSzStack, lambda Stack: Stack.append(Stack[-1]))
GFX_CMD_SWAP =      GfxCmdAlloc.Alloc(
    "SWAP",   "swap", StackGfxCmd,
    CheckSzStack, lambda Stack: SwapList(Stack, -1, -2), (2,))
GFX_CMD_JMP =       GfxCmdAlloc.Alloc(
    "JMP",    "jmp", ComplexGfxCmd,
    CheckSzStack, lambda Stack, CmdPtr: Stack.pop())
GFX_CMD_JMPIF =     GfxCmdAlloc.Alloc(
    "JMPIF",  "jmpif", ComplexGfxCmd,
    CheckSzStack, lambda Stack, CmdPtr: (CmdPtr+1, Stack.pop())[bool(Stack.pop())], (2,))
GFX_CMD_RJMP =      GfxCmdAlloc.Alloc(
    "RJMP",   "rjmp", ComplexGfxCmd,
    CheckSzStack, lambda Stack, CmdPtr: CmdPtr+Stack.pop())
GFX_CMD_RJMPIF =    GfxCmdAlloc.Alloc(
    "RJMPIF", "rjmpif", ComplexGfxCmd,
    CheckSzStack, lambda Stack, CmdPtr: (CmdPtr+(1,Stack.pop())[bool(Stack.pop())]), (2,))
EndStackCmds =      GfxCmdAlloc.NextPos
GFX_CMD_FILL =      GfxCmdAlloc.Alloc(
    "FILL",   "fill", GfxCmd,
    ["Tgt", "Color", "Rect", "SpecialFlags"],
    lambda Tgt, Color, Rect, SpecialFlags: Tgt.fill(Color, Rect, SpecialFlags))
GFX_CMD_BLIT =      GfxCmdAlloc.Alloc(
    "BLIT",   "blit", GfxCmd,
    ["Tgt", "Src", "Dest", "Area", "SpecialFlags"],
    lambda Tgt, Src, Dest, Area, SpecialFlags: Tgt.blit(Src, Dest, Area, SpecialFlags))
GFX_CMD_TEXT =      GfxCmdAlloc.Alloc(
    "TEXT",   "text", GfxCmd,
    ["Fnt", "Text", "Antialias", "Color", "Background"],
    lambda Fnt, Text, Antialias, Color, Background: Fnt.render(Text, Antialias, Color, Background))
GFX_CMD_SUBSURF =   GfxCmdAlloc.Alloc(
    "SUBSURF","subsurf", GfxCmd,
    ["Tgt", "Rect"],
    lambda Tgt, Rect: Tgt.subsurface(Rect))
GFX_CMD_GET_VAR =   GfxCmdAlloc.Alloc(
    "GET_VAR","get", GfxCmd,
    ["Context", "Name"],
    lambda Context, Name: Context[Name], True)
GFX_CMD_SET_VAR =   GfxCmdAlloc.Alloc(
    "SET_VAR","set", GfxCmd,
    ["Context", "Value", "Name"],
    lambda Context, Value, Name: Context.__setitem__(Name, Value), True)
GFX_CMD_MK_FNT =    GfxCmdAlloc.Alloc(
    "MK_FNT", "makefont", GfxCmd,
    ["Name", "Size", "Bold", "Italic"],
    lambda Name, Size, Bold, Italic: pygame.font.SysFont(Name, Size, Bold, Italic))
GFX_CMD_RECT =      GfxCmdAlloc.Alloc(
    "RECT",   "rect", GfxCmd,
    ["Surface", "Color", "Rect", "Width"],
    lambda Surface, Color, Rect, Width: pygame.draw.rect(Surface, Color, Rect, Width))
GFX_CMD_POLY =      GfxCmdAlloc.Alloc(
    "POLY",   "poly", GfxCmd,
    ["Surface", "Color", "PointList", "Width"],
    lambda Surface, Color, PointList, Width: pygame.draw.polygon(Surface, Color, PointList, Width))
GFX_CMD_CIRCLE =    GfxCmdAlloc.Alloc(
    "CIRCLE", "circle", GfxCmd,
    ["Surface", "Color", "Pos", "Radius", "Width"],
    lambda Surface, Color, Pos, Radius, Width: pygame.draw.circle(Surface, Color, Pos, Radius, Width))
GFX_CMD_ELLIPSE =   GfxCmdAlloc.Alloc(
    "ELLIPSE","ellipse", GfxCmd,
    ["Surface", "Color", "Rect", "Width"],
    lambda Surface, Color, Rect, Width: pygame.draw.ellipse(Surface, Color, Rect, Width))
GFX_CMD_ARC =       GfxCmdAlloc.Alloc(
    "ARC",    "arc", GfxCmd,
    ["Surface", "Color", "Rect", "StartAngle", "StopAngle", "Width"],
    lambda Surface, Color, Rect, StartAngle, StopAngle, Width: pygame.draw.arc(Surface, Color, Rect, StartAngle, StopAngle, Width))
GFX_CMD_LINE =      GfxCmdAlloc.Alloc(
    "LINE",   "line", GfxCmd,
    ["Surface", "Color", "StartPos", "EndPos", "Width"],
    lambda Surface, Color, StartPos, EndPos, Width: pygame.draw.line(Surface, Color, StartPos, EndPos, Width))
GFX_CMD_LINES =     GfxCmdAlloc.Alloc(
    "LINES",  "lines", GfxCmd,
    ["Surface", "Color", "Closed", "Pointlist", "Width"],
    lambda Surface, Color, Closed, Pointlist, Width: pygame.draw.lines(Surface, Color, Closed, Pointlist, Width))
GFX_CMD_AALINE =    GfxCmdAlloc.Alloc(
    "AALINE", "aaline", GfxCmd,
    ["Surface", "Color", "StartPos", "EndPos", "Width"],
    lambda Surface, Color, StartPos, EndPos, Width: pygame.draw.aaline(Surface, Color, StartPos, EndPos, Width))
GFX_CMD_AALINES =   GfxCmdAlloc.Alloc(
    "AALINES","aalines", GfxCmd,
    ["Surface", "Color", "Closed", "Pointlist", "Width"],
    lambda Surface, Color, Closed, Pointlist, Width: pygame.draw.aalines(Surface, Color, Closed, Pointlist, Width))
GFX_CMD_SIZE =      GfxCmdAlloc.Alloc(
    "SIZE",   "size", GfxCmd,
    ["Surface"],
    lambda Surface: Surface.get_size())
GFX_CMD_MK_RECT =   GfxCmdAlloc.Alloc(
    "MK_RECT","mkrect", GfxCmd,
    ["Pos", "Size"],
    lambda Pos, Size: pygame.Rect(Pos, Size))
GFX_CMD_ADD =       GfxCmdAlloc.Alloc(
    "ADD",    "add", GfxCmd,
    ["a", "b"], lambda a, b: a + b)
GFX_CMD_SUB =       GfxCmdAlloc.Alloc(
    "SUB",    "sub", GfxCmd,
    ["a", "b"], lambda a, b: a - b)
GFX_CMD_MUL =       GfxCmdAlloc.Alloc(
    "MUL",    "mul", GfxCmd,
    ["a", "b"], lambda a, b: a * b)
GFX_CMD_DIV =       GfxCmdAlloc.Alloc(
    "DIV",    "div", GfxCmd,
    ["a", "b"], lambda a, b: a / b)
GFX_CMD_MOD =       GfxCmdAlloc.Alloc(
    "MOD",    "mod", GfxCmd,
    ["a", "b"], lambda a, b: a % b)
GFX_CMD_NOT =       GfxCmdAlloc.Alloc(
    "NOT",    "not", GfxCmd,
    ["a"], lambda a: not a)
GFX_CMD_OR =        GfxCmdAlloc.Alloc(
    "OR",     "or", GfxCmd,
    ["a", "b"], lambda a, b: a | b)
GFX_CMD_AND =       GfxCmdAlloc.Alloc(
    "AND",    "and", GfxCmd,
    ["a", "b"], lambda a, b: a & b)
GFX_CMD_XOR =       GfxCmdAlloc.Alloc(
    "XOR",    "xor", GfxCmd,
    ["a", "b"], lambda a, b: a ^ b)
GFX_CMD_LT =        GfxCmdAlloc.Alloc(
    "LT",     "lt", GfxCmd,
    ["a", "b"], lambda a, b: a < b)
GFX_CMD_LE =        GfxCmdAlloc.Alloc(
    "LE",     "le", GfxCmd,
    ["a", "b"], lambda a, b: a <= b)
GFX_CMD_GT =        GfxCmdAlloc.Alloc(
    "GT",     "gt", GfxCmd,
    ["a", "b"], lambda a, b: a > b)
GFX_CMD_GE =        GfxCmdAlloc.Alloc(
    "GE",     "ge", GfxCmd,
    ["a", "b"], lambda a, b: a >= b)
GFX_CMD_EQ =        GfxCmdAlloc.Alloc(
    "EQ",     "eq", GfxCmd,
    ["a", "b"], lambda a, b: a == b)
GFX_CMD_NE =        GfxCmdAlloc.Alloc(
    "NE",     "ne", GfxCmd,
    ["a", "b"], lambda a, b: a != b)
GfxCompilerCmdNames = {Name:c for c, Name in enumerate(GfxCmdNames)}

for c in xrange(len(GfxCmds)):
    assert GfxCmds[c].CmdId == c, "Error: CmdId=%u;c=%u, CmdId does not match up with index" % (GfxCmds[c].CmdId, c)

TypeDescFn = lambda PrevData: TypeDescLst[PrevData]
TypeDescLst = map(DataPacker.ProcExtType, [
    DataInt(1),#Null (But which type?; 0:None, 1:[])
    DataInt(1),# unsigned
    DataInt(1),# signed
    DataInt(2),# unsigned
    DataInt(2),# signed
    DataInt(4),# unsigned
    DataInt(4),# signed
    DataInt(8),# unsigned
    DataInt(8),# signed
    DataLong(2, 1),
    DataVarBytes(4),
    DataVarBytes(4),
    DataObj( # array/list
        DataInt(1),
        DataVarFmt(lambda PrevData: DataArray(TypeDescFn(PrevData), 4, 1))),
    DataObj( # array/tuple
        DataInt(1),
        DataVarFmt(lambda PrevData: DataArray(TypeDescFn(PrevData), 4, 1)))])

def GetBestType(Data):
    if Data is None:
        return 0
    elif isinstance(Data, (long, int)):
        BitLen = Data.bit_length()
        Type = 1
        if Data < 0:
            BitLen = abs(Data + 1).bit_length() + 1
            Type += 1
        NumBytes = (BitLen + 7) / 8
        if NumBytes > 8:
            Type = 9
        elif NumBytes > 4:
            Type += 6
        elif NumBytes > 2:
            Type += 4
        elif NumBytes > 1:
            Type += 2
        return Type
    elif isinstance(Data, basestring):
        Type = 10
        if isinstance(Data, unicode):
            Type += 1
        return Type
    elif isinstance(Data, list):
        if len(Data) == 0:
            return 0
        else:
            return 12, max(map(GetBestType, Data))
    elif isinstance(Data, tuple):
        if len(Data) == 0:
            return 0
        else:
            return 13, max(map(GetBestType, Data))
    raise TypeError("Unrecognized or unsupported type: '%s'"%type(Data).__name__)
def EncodeAsType(Data, OpCode, InclOpCode=True):
    Rtn = None.__class__
    if OpCode == 0:
        if Data is None:
            Rtn = 0
        elif isinstance(Data, list) and len(Data) == 0:
            Rtn = 1
        else:
            raise TypeError("Unrecognized Null Type value %s" % repr(Data))
    elif 1 <= OpCode <= 8:
        assert isinstance(Data, (long, int))
        Type = OpCode
        Type -= 1
        if Data >= 0 or Type % 2 == 0:
            Rtn = Data
        else:
            Type /= 2
            Mask = 1 << (2 ** (Type+3))
            Data += Mask
            Rtn = Data
    elif OpCode == 9:
        assert isinstance(Data, (long,int))
        Rtn = Data
    elif OpCode == 10:
        assert isinstance(Data, basestring)
        Rtn = Data
    elif OpCode == 11:
        assert isinstance(Data, unicode)
        Rtn = Data.encode("utf-8")
    elif isinstance(OpCode, tuple):
        if OpCode[0] in {12, 13}:
            Rtn = map(lambda x: EncodeAsType(x, OpCode[1], False), Data)
            if InclOpCode:
                OpCodes = [OpCode]
                c = 0
                while c < len(OpCodes):
                    if isinstance(OpCodes[c], tuple):
                        OpCodes[c:c+1] = OpCodes[c]
                    else:
                        c += 1
                for OpCode in OpCodes[::-1]:
                    Rtn = [OpCode, Rtn]
            return Rtn
        else:
            raise TypeError("Unrecognized multi-OpCode")
    if Rtn is None.__class__:
        raise TypeError("Unrecognized OpCode TypeID %s" % repr(OpCode))
    if InclOpCode:
        return [OpCode, Rtn]
    else:
        return Rtn
def TypeEncoder(Data):
    return EncodeAsType(Data, GetBestType(Data))
def TypeDecoder(Data):
    OpCode, Data = Data
    if isinstance(OpCode, list) and len(OpCode) == 1:
        OpCode = OpCode[0]
    Same = lambda x: x
    Rtn = None.__class__
    if isinstance(OpCode, list):
        Ctor = {12: list, 13: tuple}[OpCode[0]]
        Rtn = Ctor(map(lambda x: TypeDecoder([OpCode[1:], x]), Data))
    elif OpCode in {12, 13}:
        OpCodes = [OpCode]
        while OpCode in {12, 13}:
            OpCode, Data = Data
            OpCodes.append(OpCode)
        Rtn = TypeDecoder([OpCodes, Data])
    elif 0 <= OpCode <= 11:
        Rtn = {
            0:lambda x:[None, list()][x],
            1: Same,
            2:lambda x: x if x < 0x80 else (x-0x100),
            3: Same,
            4: lambda x: x if x < 0x8000 else (x - 0x10000),
            5: Same,
            6: lambda x: x if x < 0x80000000 else (x - 0x100000000),
            7: Same,
            8: lambda x: x if x < 0x8000000000000000 else (x - 0x10000000000000000),
            9: Same,
            10:Same,
            11:lambda x: x.decode("utf-8"),
        }[OpCode](Data)
    return Rtn
TypeVarPackArgs = DataInt(1), DataVarFmt(TypeDescFn)
class GfxCmdStack(object):
    Serializer = DataPacker(
        DataArray(
            DataObj(
                DataInt(1),
                DataCondFmt(
                    lambda PrevData: int(bool(PrevData&0x80)),
                    DataVarFmt(TypeDescFn),
                    DataObj()))))
    @classmethod
    def Unserialize(cls, Data):
        LstData = cls.Serializer.Unpack(Data)[0]
        for c in xrange(len(LstData)):
            OpCode, Data = LstData[c]
            IsCmd = bool(OpCode & 0x80)
            LstData[c] = (IsCmd, OpCode & 0x7F if IsCmd else TypeDecoder([OpCode, Data]))
        return GfxCmdStack(LstData)
    def __init__(self, CmdList=None):
        if CmdList is None: CmdList = []
        self.CmdList = CmdList
    def Add(self, IsCmd, Data):
        if IsCmd:
            assert isinstance(Data, (int, long)) and 0 <= Data < len(GfxCmds)
        self.CmdList.append((IsCmd, Data))

    def Serialize(self, Fl=None):
        LstData = [
            ([Data | 0x80, []] if IsCmd else TypeEncoder(Data))
            for IsCmd, Data in self.CmdList]
        return self.Serializer.Pack([LstData],Fl)

    def Exec(self, Context, StackData=None):
        Stack = [] if StackData is None else list(StackData)
        CmdPtr = 0
        while CmdPtr < len(self.CmdList):
            IsCmd, Data = self.CmdList[CmdPtr]
            if IsCmd:
                CurCmd = GfxCmds[Data]
                if Data < EndStackCmds:
                    Res = CurCmd(Stack, CmdPtr)
                    if CurCmd.ResCmdPtr: CmdPtr = Res
                    else: CmdPtr += 1
                    continue
                NumArgs = len(CurCmd.Args)
                Args = []
                if CurCmd.IsSpecial:
                    Args.insert(0, Context)
                    NumArgs -= 1
                if len(Stack) < NumArgs:
                    raise TypeError(
                        "Insufficient Stack size to pass to command Data=%s ($%s$)"%(
                            GfxCmdNAMES[Data], GfxCmdNames[Data]))
                Args += Stack[-NumArgs:]
                Stack = Stack[:-NumArgs]
                Rtn = CurCmd(*Args)
                Stack.append(Rtn)
            else:
                Stack.append(Data)
            CmdPtr += 1
        return Stack
def ForthParse(Str):
    Tokens = [""]
    Quote = 0
    Backslash = False
    LstBindingOps = list()
    BindOps = ['(', '[', '{']
    UnbindOps = [')', ']', '}']
    for Ch in Str:
        if Quote > 0:
            if Backslash:
                Tokens[-1] += Ch
                Backslash = False
            elif {'\'':1, '"':2}.get(Ch, 0) == Quote:
                Quote = 0
                Tokens[-1] += Ch
                Tokens.append("")
            else:
                Tokens[-1] += Ch
                if Ch == '\\': Backslash = True
        elif Ch == '\'':
            Quote = 1
            Tokens[-1] += Ch
        elif Ch == '"':
            Quote = 2
            Tokens[-1] += Ch
        elif Ch in BindOps:
            LstBindingOps.append(Ch)
            Tokens[-1] += Ch
        elif Ch in UnbindOps:
            assert len(LstBindingOps) > 0
            assert {')':'(', ']':'[', '}':'{'}[Ch] == LstBindingOps[-1]
            LstBindingOps.pop()
            Tokens[-1] += Ch
        elif Ch.isspace():
            if len(LstBindingOps) > 0: Tokens[-1] += Ch
            else: Tokens.append("")
        else: Tokens[-1] += Ch
    return filter(len, Tokens)
def GfxCompiler(Str):
    Rtn = GfxCmdStack()
    Tokens = ForthParse(Str)
    for Tok in Tokens:
        if Tok.startswith("$") and Tok.endswith("$"):
            Tok = Tok[1:-1]
            if Tok.isdigit():
                Rtn.Add(True, int(Tok))
            elif Tok.replace("_", "").isalnum():
                Rtn.Add(True, GfxCompilerCmdNames[Tok])
        else:
            Rtn.Add(False, eval(Tok))
    return Rtn
GfxDecompilerCmdNames = GfxCmdNames
def GfxDecompiler(CmdStack):
    assert isinstance(CmdStack, GfxCmdStack)
    Tokens = []
    for IsCmd, Data in CmdStack.CmdList:
        if IsCmd:
            Tokens.append("$%s$"%GfxDecompilerCmdNames[Data])
        else:
            Str = repr(Data)
            if len(ForthParse(Str)) > 1:
                Str = "(%s)" % Str
            Tokens.append(Str)
    return " ".join(Tokens)
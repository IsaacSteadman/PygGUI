import pygame
import sys
import Queue
sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 2)[0] + "/ReFiSys")
from InetProt import DataPacker, AnyFile
#from InetProt import DATA_BYTES_LEFT, DATA_BYTES, DATA_VAR_BYTES, DATA_INT
#from InetProt import DATA_COND_FMT, DATA_ARRAY, DATA_LONG, DATA_OBJ, DATA_VAR_FMT
from InetProt import DataObj,DataLong,DataInt,DataVarBytes,\
    DataArray,DataBytesLeft,DataCondFmt,DataVarFmt,IdAllocator#,DataBytes

GfxCmdNames = []
class GfxCmd(object):
    def __init__(self, CmdId, Args, Func, IsSpecial=False):
        self.CmdId = CmdId
        self.Args = Args
        self.Func = Func
        self.IsSpecial = IsSpecial
        self.ResCmdPtr = False
    def __call__(self, *args, **kwargs):
        if len(args) != len(self.Args):
            raise TypeError("%s.__init__ called with %u arguments in addition to self (expected %u) ID:%u" % (
                self.__class__.__name__, len(args), len(self.Args), self.CmdId))
        CallArgs = [None] * len(self.Args)
        c = 0
        for Arg in args:
            CallArgs[c] = Arg
            c += 1
        for c0 in xrange(c, len(self.Args)):
            CallArgs[c] = kwargs[self.Args[c]]
        for k in kwargs:
            if k not in self.Args:
                raise TypeError("invalid kwarg: '%s'"%k)
        try:
            return self.Func(*CallArgs)
        except StandardError as Exc:
            raise StandardError(Exc, ("CmdId = %s"%GfxCmdNames[self.CmdId],))
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
            raise ValueError(Chk + "(CmdId = %s)"%GfxCmdNames[self.CmdId])
        return self.Func(Stack)
class ComplexGfxCmd(StackGfxCmd):
    def __init__(self, CmdId, StackChk, Func, StackChkArgs=(), ResCmdPtr=True):
        super(ComplexGfxCmd, self).__init__(CmdId, StackChk, Func, StackChkArgs, ResCmdPtr)
    def __call__(self, Stack, CmdPtr):
        Chk = self.StackChk(Stack, *self.StackChkArgs)
        if Chk is not None:
            raise ValueError(Chk + "(CmdId = %s)"%GfxCmdNames[self.CmdId])
        return self.Func(Stack, CmdPtr)
def CheckSzStack(Stack, Sz=1):
    if len(Stack) < Sz:
        return "Not enough args on stack"
def SwapList(Lst, i0, i1):
    Tmp = Lst[i0]
    Lst[i0] = Lst[i1]
    Lst[i1] = Tmp
class ListFiller(object):
    def __init__(self, Len, Lst=None):
        self.Len = Len
        if Lst is None: Lst = []
        Lst[:] = [None] * Len
        self.Lst = Lst
        self.NextPos = 0
    def Alloc(self, Obj):
        Rtn = self.NextPos
        self.NextPos += 1
        self.Lst[Rtn] = Obj
        return Rtn
GfxCmdAlloc = ListFiller(40, GfxCmdNames)
GFX_CMD_DISCARD = GfxCmdAlloc.Alloc("GFX_CMD_DISCARD")
GFX_CMD_COPY = GfxCmdAlloc.Alloc("GFX_CMD_COPY")
GFX_CMD_SWAP = GfxCmdAlloc.Alloc("GFX_CMD_SWAP")
GFX_CMD_JMP = GfxCmdAlloc.Alloc("GFX_CMD_JMP")
GFX_CMD_JMPIF = GfxCmdAlloc.Alloc("GFX_CMD_JMPIF")
GFX_CMD_RJMP = GfxCmdAlloc.Alloc("GFX_CMD_RJMP")
GFX_CMD_RJMPIF = GfxCmdAlloc.Alloc("GFX_CMD_RJMPIF")
EndStackCmds = GfxCmdAlloc.NextPos
GFX_CMD_FILL = GfxCmdAlloc.Alloc("GFX_CMD_FILL")
GFX_CMD_BLIT = GfxCmdAlloc.Alloc("GFX_CMD_BLIT")
GFX_CMD_TEXT = GfxCmdAlloc.Alloc("GFX_CMD_TEXT")
GFX_CMD_SUBSURF = GfxCmdAlloc.Alloc("GFX_CMD_SUBSURF")
GFX_CMD_GET_VAR = GfxCmdAlloc.Alloc("GFX_CMD_GET_VAR")
GFX_CMD_SET_VAR = GfxCmdAlloc.Alloc("GFX_CMD_SET_VAR")
GFX_CMD_MK_FNT = GfxCmdAlloc.Alloc("GFX_CMD_MK_FNT")
GFX_CMD_RECT = GfxCmdAlloc.Alloc("GFX_CMD_RECT")
GFX_CMD_POLY = GfxCmdAlloc.Alloc("GFX_CMD_POLY")
GFX_CMD_CIRCLE = GfxCmdAlloc.Alloc("GFX_CMD_CIRCLE")
GFX_CMD_ELLIPSE = GfxCmdAlloc.Alloc("GFX_CMD_ELLIPSE")
GFX_CMD_ARC = GfxCmdAlloc.Alloc("GFX_CMD_ARC")
GFX_CMD_LINE = GfxCmdAlloc.Alloc("GFX_CMD_LINE")
GFX_CMD_LINES = GfxCmdAlloc.Alloc("GFX_CMD_LINES")
GFX_CMD_AALINE = GfxCmdAlloc.Alloc("GFX_CMD_AALINE")
GFX_CMD_AALINES = GfxCmdAlloc.Alloc("GFX_CMD_AALINES")
GFX_CMD_SIZE = GfxCmdAlloc.Alloc("GFX_CMD_SIZE")
GFX_CMD_MK_RECT = GfxCmdAlloc.Alloc("GFX_CMD_MK_RECT")
GFX_CMD_ADD = GfxCmdAlloc.Alloc("GFX_CMD_ADD")
GFX_CMD_SUB = GfxCmdAlloc.Alloc("GFX_CMD_SUB")
GFX_CMD_MUL = GfxCmdAlloc.Alloc("GFX_CMD_MUL")
GFX_CMD_DIV = GfxCmdAlloc.Alloc("GFX_CMD_DIV")
GFX_CMD_MOD = GfxCmdAlloc.Alloc("GFX_CMD_MOD")
GFX_CMD_NOT = GfxCmdAlloc.Alloc("GFX_CMD_NOT")
GFX_CMD_OR = GfxCmdAlloc.Alloc("GFX_CMD_OR")
GFX_CMD_AND = GfxCmdAlloc.Alloc("GFX_CMD_AND")
GFX_CMD_XOR = GfxCmdAlloc.Alloc("GFX_CMD_XOR")
GFX_CMD_LT = GfxCmdAlloc.Alloc("GFX_CMD_LT")
GFX_CMD_LE = GfxCmdAlloc.Alloc("GFX_CMD_LE")
GFX_CMD_GT = GfxCmdAlloc.Alloc("GFX_CMD_GT")
GFX_CMD_GE = GfxCmdAlloc.Alloc("GFX_CMD_GE")
GFX_CMD_EQ = GfxCmdAlloc.Alloc("GFX_CMD_EQ")
GFX_CMD_NE = GfxCmdAlloc.Alloc("GFX_CMD_NE")
GfxCmds = [
    StackGfxCmd(
        GFX_CMD_DISCARD, CheckSzStack,
        lambda Stack: Stack.pop()),
    StackGfxCmd(
        GFX_CMD_COPY, CheckSzStack,
        lambda Stack: Stack.append(Stack[-1])),
    StackGfxCmd(
        GFX_CMD_SWAP, CheckSzStack,
        lambda Stack: SwapList(Stack, -1, -2), (2,)),
    ComplexGfxCmd(
        GFX_CMD_JMP, CheckSzStack,
        lambda Stack, CmdPtr: Stack.pop()),
    ComplexGfxCmd(
        GFX_CMD_JMPIF, CheckSzStack,
        lambda Stack, CmdPtr: (CmdPtr+1, Stack.pop())[bool(Stack.pop())], (2,)),
    ComplexGfxCmd(
        GFX_CMD_RJMP, CheckSzStack,
        lambda Stack, CmdPtr: CmdPtr+Stack.pop()),
    ComplexGfxCmd(
        GFX_CMD_RJMPIF, CheckSzStack,
        lambda Stack, CmdPtr: (CmdPtr+(1,Stack.pop())[bool(Stack.pop())]), (2,)),
    GfxCmd(
        GFX_CMD_FILL, ["Tgt", "Color", "Rect", "SpecialFlags"],
        lambda Tgt, Color, Rect, SpecialFlags: Tgt.fill(Color, Rect, SpecialFlags)),
    GfxCmd(
        GFX_CMD_BLIT, ["Tgt", "Src", "Dest", "Area", "SpecialFlags"],
        lambda Tgt, Src, Dest, Area, SpecialFlags: Tgt.blit(Src, Dest, Area, SpecialFlags)),
    GfxCmd(
        GFX_CMD_TEXT, ["Fnt", "Text", "Antialias", "Color", "Background"],
        lambda Fnt, Text, Antialias, Color, Background: Fnt.render(Text, Antialias, Color, Background)),
    GfxCmd(
        GFX_CMD_SUBSURF, ["Tgt", "Rect"],
        lambda Tgt, Rect: Tgt.subsurface(Rect)),
    GfxCmd(
        GFX_CMD_GET_VAR, ["Context", "Name"],
        lambda Context, Name: Context[Name], True),
    GfxCmd(
        GFX_CMD_SET_VAR, ["Context", "Value", "Name"],
        lambda Context, Value, Name: Context.__setitem__(Name, Value), True),
    GfxCmd(
        GFX_CMD_MK_FNT, ["Name", "Size", "Bold", "Italic"],
        lambda Name, Size, Bold, Italic: pygame.font.SysFont(Name, Size, Bold, Italic)),
    GfxCmd(
        GFX_CMD_RECT, ["Surface", "Color", "Rect", "Width"],
        lambda Surface, Color, Rect, Width: pygame.draw.rect(Surface, Color, Rect, Width)),
    GfxCmd(
        GFX_CMD_POLY, ["Surface", "Color", "PointList", "Width"],
        lambda Surface, Color, PointList, Width: pygame.draw.polygon(Surface, Color, PointList, Width)),
    GfxCmd(
        GFX_CMD_CIRCLE, ["Surface", "Color", "Pos", "Radius", "Width"],
        lambda Surface, Color, Pos, Radius, Width: pygame.draw.circle(Surface, Color, Pos, Radius, Width)),
    GfxCmd(
        GFX_CMD_ELLIPSE, ["Surface", "Color", "Rect", "Width"],
        lambda Surface, Color, Rect, Width: pygame.draw.ellipse(Surface, Color, Rect, Width)),
    GfxCmd(
        GFX_CMD_ARC, ["Surface", "Color", "Rect", "StartAngle", "StopAngle", "Width"],
        lambda Surface, Color, Rect, StartAngle, StopAngle, Width: pygame.draw.arc(Surface, Color, Rect, StartAngle, StopAngle, Width)),
    GfxCmd(
        GFX_CMD_LINE, ["Surface", "Color", "StartPos", "EndPos", "Width"],
        lambda Surface, Color, StartPos, EndPos, Width: pygame.draw.line(Surface, Color, StartPos, EndPos, Width)),
    GfxCmd(
        GFX_CMD_LINES, ["Surface", "Color", "Closed", "Pointlist", "Width"],
        lambda Surface, Color, Closed, Pointlist, Width: pygame.draw.lines(Surface, Color, Closed, Pointlist, Width)),
    GfxCmd(
        GFX_CMD_AALINE, ["Surface", "Color", "StartPos", "EndPos", "Width"],
        lambda Surface, Color, StartPos, EndPos, Width: pygame.draw.aaline(Surface, Color, StartPos, EndPos, Width)),
    GfxCmd(
        GFX_CMD_AALINES, ["Surface", "Color", "Closed", "Pointlist", "Width"],
        lambda Surface, Color, Closed, Pointlist, Width: pygame.draw.aalines(Surface, Color, Closed, Pointlist, Width)),
    GfxCmd(
        GFX_CMD_SIZE, ["Surface"],
        lambda Surface: Surface.get_size()),
    GfxCmd(
        GFX_CMD_MK_RECT, ["Pos", "Size"],
        lambda Pos, Size: pygame.Rect(Pos, Size)),
    GfxCmd(
        GFX_CMD_ADD, ["a", "b"], lambda a, b: a + b),
    GfxCmd(
        GFX_CMD_SUB, ["a", "b"], lambda a, b: a - b),
    GfxCmd(
        GFX_CMD_MUL, ["a", "b"], lambda a, b: a * b),
    GfxCmd(
        GFX_CMD_DIV, ["a", "b"], lambda a, b: a / b),
    GfxCmd(
        GFX_CMD_MOD, ["a", "b"], lambda a, b: a % b),
    GfxCmd(
        GFX_CMD_NOT, ["a"], lambda a: not a),
    GfxCmd(
        GFX_CMD_OR, ["a", "b"], lambda a, b: a | b),
    GfxCmd(
        GFX_CMD_AND, ["a", "b"], lambda a, b: a & b),
    GfxCmd(
        GFX_CMD_XOR, ["a", "b"], lambda a, b: a ^ b),
    GfxCmd(
        GFX_CMD_LT, ["a", "b"], lambda a, b: a < b),
    GfxCmd(
        GFX_CMD_LE, ["a", "b"], lambda a, b: a <= b),
    GfxCmd(
        GFX_CMD_GT, ["a", "b"], lambda a, b: a > b),
    GfxCmd(
        GFX_CMD_GE, ["a", "b"], lambda a, b: a >= b),
    GfxCmd(
        GFX_CMD_EQ, ["a", "b"], lambda a, b: a == b),
    GfxCmd(
        GFX_CMD_NE, ["a", "b"], lambda a, b: a != b)
]

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
    elif 1 <= OpCode <= 9:
        assert isinstance(Data, (long, int))
        if OpCode == 9: Rtn = Data
        Type = OpCode
        Type -= 1
        if Data >= 0 or Type % 2 == 0:
            Rtn = Data
        else:
            Type /= 2
            Mask = 1 << (2 ** (Type+3))
            Data += Mask
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
                    raise TypeError("Insufficient Stack size to pass to command %u (%s)"%(Data, GfxCmdNames[Data]))
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
GfxCompilerCmdNames = {
    "pop":GFX_CMD_DISCARD,
    "copy":GFX_CMD_COPY,
    "swap":GFX_CMD_SWAP,
    "jmp":GFX_CMD_JMP,
    "jmpif":GFX_CMD_JMPIF,
    "rjmp":GFX_CMD_RJMP,
    "rjmpif":GFX_CMD_RJMPIF,
    "fill":GFX_CMD_FILL,
    "blit":GFX_CMD_BLIT,
    "text":GFX_CMD_TEXT,
    "subsurf":GFX_CMD_SUBSURF,
    "get":GFX_CMD_GET_VAR,
    "set":GFX_CMD_SET_VAR,
    "makefont":GFX_CMD_MK_FNT,
    "rect":GFX_CMD_RECT,
    "poly":GFX_CMD_POLY,
    "circle":GFX_CMD_CIRCLE,
    "ellipse":GFX_CMD_ELLIPSE,
    "arc":GFX_CMD_ARC,
    "line":GFX_CMD_LINE,
    "lines":GFX_CMD_LINES,
    "aaline":GFX_CMD_AALINE,
    "aalines":GFX_CMD_AALINES,
    "size":GFX_CMD_SIZE,
    "mkrect":GFX_CMD_MK_RECT,
    "add": GFX_CMD_ADD,
    "sub": GFX_CMD_SUB,
    "mul": GFX_CMD_MUL,
    "div": GFX_CMD_DIV,
    "mod": GFX_CMD_MOD,
    "not": GFX_CMD_NOT,
    "or": GFX_CMD_OR,
    "and": GFX_CMD_AND,
    "xor": GFX_CMD_XOR,
    "lt": GFX_CMD_LT,
    "le": GFX_CMD_LE,
    "gt": GFX_CMD_GT,
    "ge": GFX_CMD_GE,
    "eq": GFX_CMD_EQ,
    "ne": GFX_CMD_NE
}
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
GfxDecompilerCmdNames = {GfxCompilerCmdNames[k]:k for k in GfxCompilerCmdNames}
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
class GfxEvent(object):
    def __init__(self, Data, Global):
        self.Data = Data
        self.Global = Global
    def SetRedraw(self, Obj):
        self.Global.SetRedraw(Obj)
class GfxChange(GfxEvent):
    def __init__(self, Data, Global, DispList):
        super(GfxChange, self).__init__(Data, Global)
        self.DispList = DispList
def LstRectUnion(Rects):
    if len(Rects) == 0:
        return None
    else:
        return Rects[0] if len(Rects) == 1 else Rects[0].unionall(Rects[1:])
class GfxCtl(object):
    def __init__(self, GfxObj=None, Context=None, PreGfxObj=None):
        self.Context = SynchDict({"BKGR":(0,0,0),"PrevRect":None})
        if Context is not None: self.Context.update(Context)
        self.PrevRect = self.Context["PrevRect"]
        if PreGfxObj is None:
            PreGfxObj = GfxCompiler(
                """
                "Surf" $get$
                "BKGR" $get$
                "PrevRect" $get$
                0
                $fill$
                """
            )
        self.PreGfxObj = PreGfxObj
        if GfxObj is None: GfxObj = GfxCmdStack()
        self.GfxObj = GfxObj
    def ChangePre(self, PreGfxObj):
        self.PreGfxObj = PreGfxObj
        return True
    def Change(self, GfxObj):
        self.GfxObj = GfxObj
        return True
    def Update(self, Data):
        self.Context.update(Data)
        return True
    def UpdateSynch(self, Data):
        self.Context.UpdateMeta(Data)
        for k in Data:
            if Data[k] & SYNCH_F2B:
                self.Context.MetaData[k] |= SYNCH_CHGD
        return False
    def GetChanges(self):
        MatchMask = SYNCH_F2B|SYNCH_CHGD
        Rtn = {}
        for k in self.Context:
            Meta = self.Context.GetMeta(k)
            if Meta & MatchMask == MatchMask:
                Rtn[k] = self.Context[k]
                self.Context.SetMeta(k, Meta ^ SYNCH_CHGD)
        return Rtn
    def DirtyRedraw(self, LstRects): # returns bool
        return (
            self.PreDirty or (
                self.PrevRect is not None and
                self.PrevRect.collidelist(LstRects) != -1))
    def PreDirtyRedraw(self, LstRects): # returns bool
        self.PreDirty = (
            self.PrevRect is not None and
            self.PrevRect.collidelist(LstRects) != -1)
        return self.PreDirty
    def Draw(self):
        Rects = self.GfxObj.Exec(self.Context)
        self.PrevRect = self.Context["PrevRect"] = LstRectUnion(Rects)
        return Rects
    def PreDraw(self):
        Rtn = []
        if self.Context["PrevRect"] is not None:
            Rtn = self.PreGfxObj.Exec(self.Context)
            self.PrevRect = self.Context["PrevRect"] = None
        return Rtn

def MappedCmp(x, y):
    a = isinstance(x, GfxCtl)
    b = isinstance(y, GfxCtl)
    if a != b: return -1 if a else 1
    elif a and b: return 0
    else: return cmp(y, x)
class GfxGlobal(object):
    def __init__(self):
        self.LstCtl = []
        self.LstRedraw = set()
    def MapCtls(self, Item):
        try:
            return self.LstCtl.index(Item)
        except ValueError:
            return Item
    def SetRedraw(self, Obj):
        self.LstRedraw.add(Obj)
    def DoDraw(self, Surf):
        LstCurDraw = map(self.MapCtls, self.LstRedraw)
        LstCurDraw.sort(MappedCmp)
        LstRects = []
        i = 0
        while i < len(LstCurDraw) and isinstance(LstCurDraw[i], GfxCtl):
            Ctl = LstCurDraw[i]
            Ctl.Context["Surf"] = Surf
            LstRects.extend(Ctl.PreDraw())
            del Ctl.Context["Surf"]
            i += 1
        c = len(self.LstCtl)
        MatchPos = i
        LenCurDraw = len(LstCurDraw)
        while c > 0:
            c -= 1
            Ctl = self.LstCtl[c]
            Ctl.Context["Surf"] = Surf
            if MatchPos < LenCurDraw and c == LstCurDraw[MatchPos]:
                MatchPos += 1
                LstRects.extend(Ctl.PreDraw())
            elif Ctl.PreDirtyRedraw(LstRects):
                LstRects.extend(Ctl.PreDraw())
        c = len(self.LstCtl)
        MatchPos = i
        while c > 0:
            c -= 1
            Ctl = self.LstCtl[c]
            if MatchPos < LenCurDraw and c == LstCurDraw[MatchPos]:
                MatchPos += 1
                LstRects.extend(Ctl.Draw())
            elif Ctl.DirtyRedraw(LstRects):
                LstRects.extend(Ctl.Draw())
            del Ctl.Context["Surf"]
        self.LstRedraw = set()
        return LstRects
def Main():
    Init = GfxCompiler(
    """
    "Courier New" 16 0 0 $makefont$
    "MyFnt" $set$
    """)
    Context = {}
    pygame.display.init()
    pygame.font.init()
    Context["Surf"] = pygame.display.set_mode((640, 480))
    Init.Exec(Context)
    Draw1 = GfxCompiler(
        """
        "Surf" $get$
        (0,0,0) None 0 $fill$
        "Surf" $get$
        "MyFnt" $get$
        "Hello World" 0 (255, 0, 255) None $text$
        (200, 200) None 0 $blit$""")
    Draw2 = GfxCompiler(
        """
        "Surf" $get$
        (64,128,255) None 0 $fill$
        "Surf" $get$
        "MyFnt" $get$
        "Hello World" 0 (0, 255, 255) None $text$
        (400, 200) None 0 $blit$""")
    while True:
        Evt = pygame.event.wait()
        if Evt.type == pygame.QUIT: break
        elif Evt.type == pygame.KEYDOWN:
            if Evt.key == pygame.K_1:
                pygame.display.update(Draw1.Exec(Context))
            elif Evt.key == pygame.K_2:
                pygame.display.update(Draw2.Exec(Context))

    pygame.quit()
def Main1():
    Init = GfxCompiler(
        """
        "Courier New" 16 0 0 $makefont$
        "MyFnt" $set$
        """)
    Context = {}
    pygame.display.init()
    pygame.font.init()
    Context["Surf"] = pygame.display.set_mode((640, 480))
    Init.Exec(Context)
    Draw = GfxCompiler(
        """
        "Surf" $get$
        "MyFnt" $get$
        "Hello World" 0 (255, 0, 255) (0, 191, 255) $text$ 1 23-11 $rjmpif$
        $copy$ $copy$ $size$ (0,0) $swap$ $mkrect$
        (255, 64, 0) $swap$ 2 $ellipse$ $pop$
        "Pos" $get$ None 0 $blit$""")
    Inst = GfxGlobal()
    Inst.LstCtl.append(GfxCtl(Draw, {"MyFnt":Context["MyFnt"],"Pos":(200, 200)}))
    Inst.LstCtl.append(GfxCtl(Draw, {"MyFnt":Context["MyFnt"],"Pos":(400, 200)}))
    Inst.LstRedraw = set(Inst.LstCtl)
    Ctl0Dct = {
        pygame.K_w: lambda x, y: (x, y - 1),
        pygame.K_a: lambda x, y: (x - 1, y),
        pygame.K_s: lambda x, y: (x, y + 1),
        pygame.K_d: lambda x, y: (x + 1, y),
    }
    Ctl1Dct = {
        pygame.K_UP: lambda x, y: (x, y - 1),
        pygame.K_LEFT: lambda x, y: (x - 1, y),
        pygame.K_DOWN: lambda x, y: (x, y + 1),
        pygame.K_RIGHT: lambda x, y: (x + 1, y),
    }
    while True:
        Evt = pygame.event.wait()
        if Evt.type == pygame.QUIT:
            break
        elif Evt.type == pygame.KEYDOWN:
            if Evt.key in Ctl0Dct:
                Ctl = Inst.LstCtl[0]
                assert isinstance(Ctl, GfxCtl)
                Pos = Ctl.Context["Pos"]
                Pos = Ctl0Dct[Evt.key](*Pos)
                if Ctl.Update(GfxEvent({"Pos":Pos}, Inst)):
                    Inst.SetRedraw(Ctl)
            elif Evt.key in Ctl1Dct:
                Ctl = Inst.LstCtl[1]
                assert isinstance(Ctl, GfxCtl)
                Pos = Ctl.Context["Pos"]
                Pos = Ctl1Dct[Evt.key](*Pos)
                if Ctl.Update(GfxEvent({"Pos":Pos}, Inst)):
                    Inst.SetRedraw(Ctl)
        if len(Inst.LstRedraw) > 0:
            pygame.display.update(Inst.DoDraw(Context["Surf"]))
    pygame.quit()
SYNCH_F2B = 1 # front-end to back-end
SYNCH_B2F = 2 # back-end to front-end
SYNCH_INF = 3
SYNCH_CHGD = 4 # changed
SYNCH_INF_CHGD = 8 # synch info changed
class SynchDict(dict):
    def __init__(self, *args, **kwargs):
        super(SynchDict, self).__init__(*args, **kwargs)
        self.MetaData = {k: 0 for k in self}
    def __setitem__(self, key, value):
        if key not in self:
            self.MetaData[key] = 0
        else:
            if self.__getitem__(key) != value:
                self.MetaData[key] |= SYNCH_CHGD
        super(SynchDict, self).__setitem__(key, value)
    def __delitem__(self, key):
        super(SynchDict, self).__delitem__(key)
        self.MetaData.__delitem__(key)
    def SetMeta(self, key, value):
        if self.MetaData[key] & SYNCH_INF != value & SYNCH_INF:
            value |= SYNCH_INF_CHGD
        self.MetaData[key] = value
    def ClearInfChg(self, key):
        if self.MetaData[key] & SYNCH_INF_CHGD:
            self.MetaData[key] ^= SYNCH_INF_CHGD
    def UpdateMeta(self, Other):
        self.MetaData.update(Other)
    def GetMeta(self, key):
        return self.MetaData[key]
class MainCtl(object):
    def __init__(self, Synch):
        self.Synch = SynchDict(Synch)
        self.Redraw = True
        self.ChgDraw = False
        self.ChgPreDraw = False
        self.Draw = GfxCompiler(""" "Surf" $get$ (255, 255, 255) "TotRect" $get$ 0 $fill$ """)
        self.PreDraw = GfxCompiler(""" "Surf" $get$ "BKGR" $get$ "PrevRect" $get$ 0 $fill$ """)
    def OnChange(self, DctUpd):
        self.Synch.update(DctUpd)
    def OnEvt(self, Evt, Pos):
        return False
    def OnEvtGlobal(self, Evt):
        return False
    def OnMouseEnter(self):
        return False
    def OnMouseExit(self):
        return False
    def CollidePt(self, Pt):
        return False
EVT_TYPE_MASK = 3
EVT_CHANGE = 0
EVT_WIDGETS = 1
EVT_EXEC = 2
EVT_QUIT = 3
EVT_EXEC_GLOBAL = 0
EVT_EXEC_WID = 4
EVT_EXEC_GLOBAL_WID = 8
EVT_EXEC_WID_GLOBAL = 12
EVT_EXEC_MASK = 12
EVT_WID_INIT = 0
EVT_WID_ADD = 4
EVT_WID_REM = 8
EVT_WID_DEL = 12
EVT_WID_MASK = 12
EVT_CHG_PREDRAW = 4
EVT_CHG_DRAW = 8
EVT_CHG_VARS = 16
EVT_CHG_SYNCH = 32
EVT_CHG_PAINT = 64
EvtVarsPacker = DataPacker(DataArray(DataObj(DataVarBytes(2), *TypeVarPackArgs)))
EvtSynchInfPacker = DataPacker(DataArray(DataObj(DataVarBytes(2), DataInt(1))))
def ProcPackMainCtl(Ctl):
    assert isinstance(Ctl, MainCtl)
    EvtCode = EVT_CHANGE
    Bytes = ""
    if Ctl.ChgPreDraw:
        EvtCode |= EVT_CHG_PREDRAW
        Bytes += Ctl.PreDraw.Serialize()
    if Ctl.ChgDraw:
        EvtCode |= EVT_CHG_DRAW
        Bytes += Ctl.Draw.Serialize()
    MatchMask = SYNCH_CHGD|SYNCH_B2F
    SynchLst = [k for k in Ctl.Synch if Ctl.Synch.GetMeta(k) & MatchMask == MatchMask]
    SynchInfLst = [k for k in Ctl.Synch if Ctl.Synch.GetMeta(k) & SYNCH_INF_CHGD]
    if len(SynchLst):
        EvtCode |= EVT_CHG_VARS
        Bytes += EvtVarsPacker.Pack([[[k] +list(TypeEncoder(Ctl.Synch[k])) for k in SynchLst]])
    if len(SynchInfLst):
        EvtCode |= EVT_CHG_SYNCH
        map(Ctl.Synch.ClearInfChg, SynchInfLst)
        Bytes += EvtSynchInfPacker.Pack([[[k, Ctl.Synch.GetMeta(k) & SYNCH_INF] for k in SynchInfLst]])
    if Ctl.Redraw:
        EvtCode |= EVT_CHG_PAINT
    Ctl.ChgPreDraw = False
    Ctl.ChgDraw = False
    Ctl.Redraw = False
    return EvtCode, Bytes
def ProcMainCtl(Ctl):
    assert isinstance(Ctl, MainCtl)
    MatchMask = SYNCH_CHGD | SYNCH_B2F
    SynchLst = [(k, Ctl.Synch[k]) for k in Ctl.Synch if Ctl.Synch.GetMeta(k) & MatchMask == MatchMask]
    SynchInfLst = [(k, Ctl.Synch.GetMeta(k) & SYNCH_INF) for k in Ctl.Synch if Ctl.Synch.GetMeta(k) & SYNCH_INF_CHGD]
    Rtn = [
        [Ctl.ChgPreDraw, None],
        [Ctl.ChgDraw, None],
        [bool(len(SynchLst)), None],
        [bool(len(SynchInfLst)), None],
        [Ctl.Redraw, None]
    ]
    Ctl.ChgPreDraw = False
    Ctl.ChgDraw = False
    Ctl.Redraw = False
    if Rtn[0][0]: Rtn[0][1] = Ctl.PreDraw
    if Rtn[1][0]: Rtn[1][1] = Ctl.Draw
    if Rtn[2][0]: Rtn[2][1] = SynchLst
    if Rtn[3][0]: Rtn[3][1] = SynchInfLst
    return Rtn
def PackMainCtl(Data):
    Fl = AnyFile("")
    EvtCode = EVT_CHANGE
    if Data[0][0]:
        Data[0][1].Serialize(Fl)
        EvtCode |= EVT_CHG_PREDRAW
    if Data[1][0]:
        Data[1][1].Serialize(Fl)
        EvtCode |= EVT_CHG_DRAW
    if Data[2][0]:
        EvtVarsPacker.Pack([map(lambda x: [x[0]] + list(TypeEncoder(x[1])), Data[2][1])], Fl)
        EvtCode |= EVT_CHG_VARS
    if Data[3][0]:
        EvtSynchInfPacker.Pack([Data[3][1]], Fl)
        EvtCode |= EVT_CHG_SYNCH
    if Data[4][0]:
        EvtCode |= EVT_CHG_PAINT
    return EvtCode, Fl.Obj
def UnpackGfxCtl(EvtCode, Bytes):
    Fl = AnyFile(Bytes)
    Rtn = map(lambda x: [bool(EvtCode & x), None], [EVT_CHG_PREDRAW, EVT_CHG_DRAW, EVT_CHG_VARS, EVT_CHG_SYNCH, EVT_CHG_PAINT])
    if Rtn[0][0]:
        Rtn[0][1] = GfxCmdStack.Unserialize(Fl)
    if Rtn[1][0]:
        Rtn[1][1] = GfxCmdStack.Unserialize(Fl)
    if Rtn[2][0]:
        Vars = EvtVarsPacker.Unpack(Fl)[0]
        Rtn[2][1] = {x[0]: TypeDecoder(x[1:]) for x in Vars}
    if Rtn[3][0]:
        Vars = EvtSynchInfPacker.Unpack(Fl)[0]
        Rtn[3][1] = dict(Vars)
    return Rtn
class Layer1Communicator(object):
    Layer = 1
    def __init__(self, QueuePair):
        self.SendQueue, self.RecvQueue = QueuePair
    def Send(self, Data):
        self.SendQueue.put(Data)
        self.SendQueue.join()
    def Recv(self):
        Rtn = self.RecvQueue.get()
        self.RecvQueue.task_done()
        return Rtn
def MkLayer1Pair():
    QueuePair = Queue.Queue(), Queue.Queue()
    return Layer1Communicator(QueuePair), Layer1Communicator(QueuePair[::-1])
class MyEvent(object):
    QUIT = pygame.QUIT
    ACTIVEEVENT = pygame.ACTIVEEVENT
    KEYDOWN = pygame.KEYDOWN
    KEYUP = pygame.KEYUP
    MOUSEMOTION = pygame.MOUSEMOTION
    MOUSEBUTTONUP = pygame.MOUSEBUTTONUP
    MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
    JOYAXISMOTION = pygame.JOYAXISMOTION
    JOYBALLMOTION = pygame.JOYBALLMOTION
    JOYHATMOTION = pygame.JOYHATMOTION
    JOYBUTTONUP = pygame.JOYBUTTONUP
    JOYBUTTONDOWN = pygame.JOYBUTTONDOWN
    VIDEORESIZE = pygame.VIDEORESIZE
    VIDEOEXPOSE = pygame.VIDEOEXPOSE
    USEREVENT = pygame.USEREVENT
    Dispatch = {
        ACTIVEEVENT: ["gain", "state"],
        KEYDOWN: ["unicode", "key", "mod"],
        KEYUP: ["key", "mod"],
        MOUSEMOTION: ["pos", "rel", "buttons"],
        MOUSEBUTTONUP: ["pos", "button"],
        MOUSEBUTTONDOWN: ["pos", "button"],
        JOYAXISMOTION: ["joy", "axis", "value"],
        JOYBALLMOTION: ["joy", "bal", "rel"],
        JOYHATMOTION: ["joy", "hat", "value"],
        JOYBUTTONUP: ["joy", "button"],
        JOYBUTTONDOWN: ["joy", "button"],
        VIDEORESIZE: ["size", "w", "h"],
        USEREVENT: []}
    @classmethod
    def InitCls(cls, DctEvents):
        for k in DctEvents:
            setattr(cls, k, DctEvents)
        cls.Dispatch = {
            cls.ACTIVEEVENT: ["gain", "state"],
            cls.KEYDOWN: ["unicode", "key", "mod"],
            cls.KEYUP: ["key", "mod"],
            cls.MOUSEMOTION: ["pos", "rel", "buttons"],
            cls.MOUSEBUTTONUP: ["pos", "button"],
            cls.MOUSEBUTTONDOWN: ["pos", "button"],
            cls.JOYAXISMOTION: ["joy", "axis", "value"],
            cls.JOYBALLMOTION: ["joy", "bal", "rel"],
            cls.JOYHATMOTION: ["joy", "hat", "value"],
            cls.JOYBUTTONUP: ["joy", "button"],
            cls.JOYBUTTONDOWN: ["joy", "button"],
            cls.VIDEORESIZE: ["size", "w", "h"],
            cls.USEREVENT: []}
    def __init__(self, Type, data):
        self.type = Type
        if self.type in [self.QUIT, self.VIDEOEXPOSE]:
            return
        map(lambda k, v: setattr(self, k, v), self.Dispatch.get(self.type, []), data)
class NetGfxBackEnd(object):
    def __init__(self, Comms):
        self.Comms = Comms
        self.Layer = Comms.Layer
        self.Widgets = {}
        self.DctEvtFunc = {}
        self.NextEvents = []
        self.ChgdPos = False
        self.LstCtl = []
        self.IdAlloc = IdAllocator(65535)
        self.CurPos = (0,0)
        self.CurCtl = None
    def DelWidget(self, WidNum):
        assert self.Layer == 1
        self.IdAlloc.FreeId(WidNum)
        self.NextEvents.append((WidNum, EVT_WIDGETS|EVT_WID_DEL, None))
    def AddWidget(self, WidNum, Index):
        assert self.Layer == 1
        self.LstCtl.insert(Index, self.Widgets[WidNum])
        self.NextEvents.append((WidNum, EVT_WIDGETS | EVT_WID_ADD, Index))
    def InitWidget(self, Ctl):
        assert self.Layer == 1
        assert isinstance(Ctl, MainCtl)
        WidNum = self.IdAlloc.AllocId()
        self.Widgets[WidNum] = Ctl
        Context = {k: Ctl.Synch[k] for k in Ctl.Synch if Ctl.Synch.GetMeta(k) & SYNCH_B2F}
        self.NextEvents.append((WidNum, EVT_WIDGETS | EVT_WID_INIT, GfxCtl(Ctl.Draw, Context, Ctl.PreDraw)))
        return WidNum
    def RemWidget(self, WidNum):
        assert self.Layer == 1
        self.LstCtl.remove(self.Widgets[WidNum])
        self.NextEvents.append((WidNum, EVT_WIDGETS|EVT_WID_REM, None))
    def ExecWidget(self, WidNum, GfxObj):
        self.NextEvents.append((WidNum, EVT_EXEC | EVT_EXEC_WID, GfxObj))
    def ExecGlobal(self, GfxObj):
        self.NextEvents.append((0, EVT_EXEC | EVT_EXEC_GLOBAL, GfxObj))
    def ExecWidgetGlobal(self, WidNum, GfxObjWid, GfxObjGlobal):
        self.NextEvents.append((WidNum, EVT_EXEC | EVT_EXEC_WID_GLOBAL, [GfxObjWid, GfxObjGlobal]))
    def ExecGlobalWidget(self, WidNum, GfxObjGlobal, GfxObjWid):
        self.NextEvents.append((WidNum, EVT_EXEC|EVT_EXEC_GLOBAL_WID, [GfxObjGlobal, GfxObjWid]))
    def RecvEvent(self):
        return self.Comms.Recv()[0]
    def SendEvents(self, LstEvents):
        self.Comms.Send((LstEvents,))
    def RecvChanges(self):
        return self.Comms.Recv()[0]
    def ProcChange(self, WidNum, Changes):
        Widget = self.Widgets[WidNum]
        assert isinstance(Widget, MainCtl)
        Widget.OnChange(Changes)
    @staticmethod
    def CalcCollide(CurCtl, LstCtl, CurPos):
        if CurCtl is None or not CurCtl.CollidePt(CurPos):
            if CurCtl is not None: CurCtl.OnMouseExit()
            CurCtl = None
            for Ctl in LstCtl:
                if Ctl.CollidePt(CurPos):
                    Ctl.OnMouseEnter()
                    CurCtl = Ctl
                    break
        elif CurCtl is not None:
            Pos = len(LstCtl)
            if CurCtl in LstCtl: Pos = LstCtl.index(CurCtl)
            for c in xrange(Pos):
                Ctl = LstCtl[c]
                if Ctl.CollidePt(CurPos):
                    CurCtl.OnMouseExit()
                    Ctl.OnMouseEnter()
                    CurCtl = Ctl
                    break
            if not CurCtl in LstCtl: CurCtl = None
        return CurCtl
    def Main(self):
        LstCtl = []
        while True:
            Evt = self.RecvEvent()
            if Evt.type == pygame.VIDEORESIZE:
                if Evt.type in self.DctEvtFunc:
                    self.DctEvtFunc[Evt.type](Evt)
            AllowRedraw = True
            CtlEvtAllow = True
            if Evt.type == pygame.QUIT:
                self.NextEvents.append((0, EVT_QUIT, None))
                self.SendEvents(self.NextEvents)
                self.NextEvents = []
                return -1
            elif self.ChgdPos:
                self.ChgdPos = False
                self.CurCtl = self.CalcCollide(self.CurCtl, self.LstCtl, self.CurPos)
            elif Evt.type == pygame.MOUSEMOTION:
                self.CurPos = Evt.pos
                self.CurCtl = self.CalcCollide(self.CurCtl, self.LstCtl, self.CurPos)
            elif Evt.type in self.DctEvtFunc:
                CtlEvtAllow = False
                if not self.DctEvtFunc[Evt.type](Evt): AllowRedraw = False
            if CtlEvtAllow:
                if self.CurCtl is not None and Evt.type != pygame.VIDEORESIZE:
                    self.CurCtl.OnEvt(Evt, self.CurPos)
                for Ctl in self.LstCtl:
                    Ctl.OnEvtGlobal(Evt)
            for WidNum in self.Widgets:
                Widget = self.Widgets[WidNum]
                assert isinstance(Widget, MainCtl)
                Data = ProcMainCtl(Widget)
                Code = 0
                if Data[0][0]: Code |= EVT_CHG_PREDRAW
                if Data[1][0]: Code |= EVT_CHG_DRAW
                if Data[2][0]: Code |= EVT_CHG_VARS
                if Data[3][0]: Code |= EVT_CHG_SYNCH
                if Data[4][0]: Code |= EVT_CHG_PAINT
                if Code: self.NextEvents.append((WidNum, EVT_CHANGE|Code, Data))

            self.SendEvents(self.NextEvents)
            if len(self.NextEvents) == 0: continue
            LstCtl = self.LstCtl
            self.NextEvents = []
            LstChanges = self.RecvChanges()
            for WidNum, Changes in LstChanges:
                Widget = self.Widgets[WidNum]
                assert isinstance(Widget, MainCtl)
                Widget.OnChange(Changes)
            #TODO: you have
            #TODO:   Recv Event
            #TODO:   Process Evt
            #TODO:   Process B2F
            #TODO:   Send LstEvents
            #TODO:   Recv Changes
            #TODO:   Process F2B
            #TODO: missing: NONE
# Gfx Back-End Loop
#   Recv Event
#   Process Evt and EvtGlobal
#   Process B2F
#   Send
#   Recv
#   Process F2B
class NetGfxFrontEnd(GfxGlobal):
    def __init__(self, Comms):
        super(NetGfxFrontEnd, self).__init__()
        self.Widgets = {}
        self.Comms = Comms
        self.Layer = Comms.Layer
        self.Context = {}
    def ProcEvt(self, WidNum, EvtCode, Data):
        EvtType = EvtCode & EVT_TYPE_MASK
        if EvtType == EVT_WIDGETS:
            Code = EvtCode & EVT_WID_MASK
            if Code == EVT_WID_INIT:
                if WidNum in self.Widgets: return 2 # widget must not exist
                self.Widgets[WidNum] = Data
            elif Code == EVT_WID_DEL:
                if WidNum not in self.Widgets: return 1 # widget must exist
                Widget = self.Widgets[WidNum]
                if Widget in self.LstCtl: return 3 # widget must be removed
                del self.Widgets[WidNum]
            elif Code == EVT_WID_ADD:
                Index = Data
                if WidNum not in self.Widgets: return 1  # widget must exist
                Widget = self.Widgets[WidNum]
                if Widget in self.LstCtl: return 3 # widget must be removed
                self.LstCtl.insert(Index, self.Widgets[WidNum])
            elif Code == EVT_WID_REM:
                if WidNum not in self.Widgets: return 1  # widget must exist
                try:
                    self.LstCtl.remove(self.Widgets[WidNum])
                except ValueError:
                    return 4 # widget must be added
        elif EvtType == EVT_CHANGE:
            Widget = self.Widgets[WidNum]
            assert isinstance(Widget, GfxCtl)
            if Data[0][0]: Widget.ChangePre(Data[0][1])
            if Data[1][0]: Widget.Change(Data[1][1])
            if Data[2][0]: Widget.Update(dict(Data[2][1]))
            if Data[3][0]: Widget.UpdateSynch(dict(Data[3][1]))
            if Data[4][0]:
                self.LstRedraw.add(Widget)
        elif EvtType == EVT_EXEC:
            Code = EvtCode & EVT_EXEC_MASK
            if Code == EVT_EXEC_WID:
                assert isinstance(Data, GfxCmdStack)
                Widget = self.Widgets[WidNum]
                assert isinstance(Widget, GfxCtl)
                Data.Exec(Widget.Context)
            elif Code == EVT_EXEC_GLOBAL:
                assert isinstance(Data, GfxCmdStack)
                Data.Exec(self.Context)
            elif Code == EVT_EXEC_GLOBAL_WID:
                assert isinstance(Data, (list, tuple))
                assert len(Data) == 2
                assert isinstance(Data[0], GfxCmdStack)
                assert isinstance(Data[1], GfxCmdStack)
                Widget = self.Widgets[WidNum]
                assert isinstance(Widget, GfxCtl)
                Stack = Data[0].Exec(self.Context)
                Data[1].Exec(Widget.Context, Stack)
            elif Code == EVT_EXEC_WID_GLOBAL:
                assert isinstance(Data, (list, tuple))
                assert len(Data) == 2
                assert isinstance(Data[0], GfxCmdStack)
                assert isinstance(Data[1], GfxCmdStack)
                Widget = self.Widgets[WidNum]
                assert isinstance(Widget, GfxCtl)
                Stack = Data[0].Exec(Widget.Context)
                Data[1].Exec(self.Context, Stack)
        else: return 0xFF #unrecognized command
        return 0 # no error
    def SendEvent(self, Evt):
        Evt = MyEvent(Evt.type, map(lambda k: getattr(Evt, k), MyEvent.Dispatch.get(Evt.type, [])))
        self.Comms.Send((Evt,))
    def RecvEvents(self):
        return self.Comms.Recv()[0]
    def SendChanges(self, LstChanges):
        self.Comms.Send((LstChanges,))
    def Main(self):
        Surf = pygame.display.get_surface()
        while True:
            Evt = pygame.event.wait()
            self.SendEvent(Evt)
            EvtLst = self.RecvEvents()
            if len(EvtLst) == 0:
                continue
            for Evt in EvtLst:
                if Evt[1] & EVT_TYPE_MASK == EVT_QUIT:
                    return -1
                self.ProcEvt(*Evt)
            pygame.display.update(self.DoDraw(Surf))
            LstChanges = []
            for WidNum in self.Widgets:
                Widget = self.Widgets[WidNum]
                assert isinstance(Widget, GfxCtl)
                Changes = Widget.GetChanges()
                if len(Changes) > 0: LstChanges.append((WidNum, Changes))
            self.SendChanges(LstChanges)

# Gfx Front-End loop
#   GetEvt
#   Send
#   Recv; continue if len(Res) == 0
#   Process B2F
#   Draw
#   Process F2B
#   Send
EvtFmt = DataPacker(
    DataInt(2), # widget number
    DataInt(1), # Event Code
    DataBytesLeft() # the rest of the bytes
)
class TestButton(MainCtl):
    def __init__(self, Title, Colors, Pos):
        super(TestButton, self).__init__({
            "Title": Title,
            "Color0": Colors[0],
            "Color1": Colors[1],
            "Pos": Pos,
            "IsInit": False})
        self.Fnt = pygame.font.SysFont("Courier New", 16, 0, 0)
        Size = self.Fnt.size(Title)
        self.Colors = Colors
        for k in self.Synch:
            self.Synch.SetMeta(k, SYNCH_B2F)
        self.Synch.SetMeta("IsInit", SYNCH_B2F|SYNCH_F2B)
        self.Draw = GfxCompiler(
            """
            "IsInit" $get$ 13 $rjmpif$
            1 "IsInit" $set$ $pop$ "Courier New" 16 0 0 $makefont$ "MyFnt" $set$ $pop$
            "Surf" $get$
            "MyFnt" $get$ "Title" $get$ 0 "Color0" $get$ "Color1" $get$ $text$
            "Pos" $get$ None 0 $blit$""")
        self.TotRect = pygame.Rect(Pos, Size)
    def OnMouseEnter(self):
        a = .3 # opacity of the blended color
        if self.Colors[1] is not None:
            self.Synch["Color1"] = tuple(map(
                lambda x, y: int((1.-a) * x + a * y),
                self.Colors[1], (255,255,255) ))
            self.Redraw = True
    def OnMouseExit(self):
        if self.Colors[1] is not None:
            self.Synch["Color1"] = self.Colors[1]
            self.Redraw = True
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN:
            print "Hello Down"
    def CollidePt(self, Pt):
        return self.TotRect.collidepoint(Pt)
def Main2_Backend(Comms):
    Inst = NetGfxBackEnd(Comms)
    TheButton0 = TestButton("Hello World", [(255, 255,255), (255, 0, 0)], (20,200))
    TheButton1 = TestButton("Hi World", [(255, 255, 255), (0, 255, 0)], (220, 200))
    TheButton2 = TestButton("Another Button", [(255, 255, 255), (0, 0, 255)], (420, 200))
    BtnId0 = Inst.InitWidget(TheButton0)
    BtnId1 = Inst.InitWidget(TheButton1)
    BtnId2 = Inst.InitWidget(TheButton2)
    Inst.AddWidget(BtnId0, 0)
    Inst.AddWidget(BtnId1, 1)
    Inst.AddWidget(BtnId2, 2)
    Inst.Main()
# the gfx front end main function
def Main2():
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((640, 480))
    CommF, CommB = MkLayer1Pair()
    import threading
    Thrd = threading.Thread(target=Main2_Backend, args=(CommB,))
    Thrd.start()
    Inst = NetGfxFrontEnd(CommF)
    Inst.Main()
    print "EXITTING Front-End"
    Thrd.join()
    pygame.quit()


#if __name__ == "__main__": Main1()

import pygame
class GfxCmd(object):
    def __init__(self, CmdId, Args, Func, IsSpecial=False):
        self.CmdId = CmdId
        self.Args = Args
        self.Func = Func
        self.IsSpecial = IsSpecial
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
            raise StandardError(Exc, ("CmdId = %u"%self.CmdId,))
class StackGfxCmd(GfxCmd):
    def __init__(self, CmdId, StackChk, Func, StackChkArgs=()):
        super(StackGfxCmd, self).__init__(CmdId, [], Func)
        self.CmdId = CmdId
        self.StackChk = StackChk
        self.Func = Func
        self.StackChkArgs = StackChkArgs
    def __call__(self, Stack):
        Chk = self.StackChk(Stack, *self.StackChkArgs)
        if Chk is not None:
            raise ValueError(Chk + "(CmdId = %u)"%self.CmdId)
        return self.Func(Stack)
def CheckSzStack(Stack, Sz=1):
    if len(Stack) < Sz:
        return "Not enough args on stack"
def SwapList(Lst, i0, i1):
    Tmp = Lst[i0]
    Lst[i0] = Lst[i1]
    Lst[i1] = Tmp
GFX_CMD_DISCARD = 0
GFX_CMD_COPY = 1
GFX_CMD_SWAP = 2
GFX_CMD_FILL = 3
GFX_CMD_BLIT = 4
GFX_CMD_TEXT = 5
GFX_CMD_SUBSURF = 6
GFX_CMD_GET_VAR = 7
GFX_CMD_SET_VAR = 8
GFX_CMD_MK_FNT = 9
GFX_CMD_RECT = 10
GFX_CMD_POLY = 11
GFX_CMD_CIRCLE = 12
GFX_CMD_ELLIPSE = 13
GFX_CMD_ARC = 14
GFX_CMD_LINE = 15
GFX_CMD_LINES = 16
GFX_CMD_AALINE = 17
GFX_CMD_AALINES = 18
GFX_CMD_SIZE = 19
GFX_CMD_MK_RECT = 20
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
        lambda Pos, Size: pygame.Rect(Pos, Size))
]
for c in xrange(len(GfxCmds)):
    assert GfxCmds[c].CmdId == c, "Error: CmdId=%u;c=%u, CmdId does not match up with index" % (GfxCmds[c].CmdId, c)
class GfxCmdStack(object):
    def __init__(self, CmdList=None):
        if CmdList is None: CmdList = []
        self.CmdList = []
    def Add(self, IsCmd, Data):
        if IsCmd:
            assert isinstance(Data, (int, long)) and 0 <= Data < len(GfxCmds)
        self.CmdList.append((IsCmd, Data))
    def Exec(self, Context):
        Stack = []
        for IsCmd, Data in self.CmdList:
            if IsCmd:
                if Data < 3:
                    GfxCmds[Data](Stack)
                    continue
                CurCmd = GfxCmds[Data]
                NumArgs = len(CurCmd.Args)
                Args = []
                if CurCmd.IsSpecial:
                    Args.insert(0, Context)
                    NumArgs -= 1
                if len(Stack) < NumArgs:
                    raise TypeError("Insufficient Stack size to pass to command %u"%Data)
                Args += Stack[-NumArgs:]
                Stack = Stack[:-NumArgs]
                Rtn = CurCmd(*Args)
                Stack.append(Rtn)
            else:
                Stack.append(Data)
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
    "mkrect":GFX_CMD_MK_RECT
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
        self.Context = {"BKGR":(0,0,0),"PrevRect":None}
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
    def ChangePre(self, Evt):
        self.PreGfxObj.CmdList = Evt.DispList
        self.Context.update(Evt.Data)
        return True
    def Change(self, Evt):
        self.GfxObj.CmdList = Evt.DispList
        self.Context.update(Evt.Data)
        return True
    def Update(self, Evt):
        self.Context.update(Evt.Data)
        return True
    def DirtyRedraw(self, LstRects): # returns bool
        return self.PreDirty or self.PrevRect.collidelist(LstRects) != -1
    def PreDirtyRedraw(self, LstRects): # returns bool
        self.PreDirty = self.PrevRect.collidelist(LstRects) != -1
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
    if isinstance(x, GfxCtl):
        return -1
    elif isinstance(y, GfxCtl):
        return 1
    else:
        return cmp(y, x)
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
        "Hello World" 0 (255, 0, 255) (0, 191, 255) $text$
        $copy$ $copy$ $size$ (0,0) $swap$ $mkrect$
        (255, 64, 0) $swap$ 2 $ellipse$ $pop$
        "Pos" $get$ None 0 $blit$""")
    Draw1 = GfxCompiler(
        """
        "Surf" $get$
        "MyFnt" $get$
        "Hello World" 0 (255, 0, 255) None $text$
        (200, 200) None 0 $blit$""")
    Draw2 = GfxCompiler(
        """
        "Surf" $get$
        "MyFnt" $get$
        "Hello World" 0 (0, 255, 255) None $text$
        (400, 200) None 0 $blit$""")
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


if __name__ == "__main__": Main1()

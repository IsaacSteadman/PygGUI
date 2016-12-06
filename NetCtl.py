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
GFX_CMD_DISCARD = 0
GFX_CMD_FILL = 1
GFX_CMD_BLIT = 2
GFX_CMD_TEXT = 3
GFX_CMD_SUBSURF = 4
GFX_CMD_GET_VAR = 5
GFX_CMD_SET_VAR = 6
GFX_CMD_MK_FNT = 7
GfxCmds = [
    None,
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
]
class GfxCmdStack(object):
    def __init__(self):
        self.CmdList = []
    def Add(self, IsCmd, Data):
        if IsCmd:
            assert isinstance(Data, (int, long)) and 0 <= Data < len(GfxCmds)
        self.CmdList.append((IsCmd, Data))
    def Exec(self, Context):
        Stack = []
        for IsCmd, Data in self.CmdList:
            if IsCmd:
                if Data == 0:
                    Stack.pop()
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
    "fill":GFX_CMD_FILL,
    "blit":GFX_CMD_BLIT,
    "text":GFX_CMD_TEXT,
    "subsurf":GFX_CMD_SUBSURF,
    "get":GFX_CMD_GET_VAR,
    "set":GFX_CMD_SET_VAR,
    "makefont":GFX_CMD_MK_FNT}
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
        (0,0,0) None 0 $fill$ $pop$
        "Surf" $get$
        "MyFnt" $get$
        "Hello World" 0 (255, 0, 255) None $text$
        (200, 200) None 0 $blit$""")
    Draw2 = GfxCompiler(
        """
        "Surf" $get$
        (64,128,255) None 0 $fill$ $pop$
        "Surf" $get$
        "MyFnt" $get$
        "Hello World" 0 (0, 255, 255) None $text$
        (400, 200) None 0 $blit$""")
    while True:
        Evt = pygame.event.wait()
        if Evt.type == pygame.QUIT: break
        elif Evt.type == pygame.KEYDOWN:
            if Evt.key == pygame.K_1:
                Draw1.Exec(Context)
                pygame.display.update()
            elif Evt.key == pygame.K_2:
                Draw2.Exec(Context)
                pygame.display.update()
    pygame.quit()


if __name__ == "__main__": Main()
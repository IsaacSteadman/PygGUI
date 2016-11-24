import PygCtl
from PygCtl import pygame
from ModuleHelper import *
#PygCtl = AttrWatcher(PygCtl)
CacheImgs = False
PygCtlAttrs = [
    "PygCtl",
    "RED",
    "GREEN",
    "WHITE",
    "BKGR",
    "PressBtn",
    "Init",
    "LstCtl",
    "SetRedraw",
    "ChgdPos",
    "RunCtls"]
for attr in PygCtlAttrs:
    RequireAttr(PygCtl, attr)
def UpdPos():
    PygCtl.ChgdPos = True
def Combine(a, b, Amt):
    return int(b[0] * Amt + a[0] * (1 - Amt)), int(b[1] * Amt + a[1] * (1 - Amt)), int(b[2] * Amt + a[2] * (1 - Amt))
def InitGrad(Lst, From, To):
    for c in xrange(len(Lst)):
        Lst[c] = Combine(From, To, float(c) / len(Lst))
def MulColor(a, Amt):
    return tuple([int(x * Amt) for x in a])
class ListChild(PygCtl.PygCtl):
    def __init__(self, zIndex):
        self.PrevRect = None
        self.Pos = None
        self.zIndex = zIndex
        self.Parent = None
        self.Img = None
        self.IsShow = True
        self.CollRect = None
    def Hide(self):
        self.IsShow = False
        PygCtl.SetRedraw(self)
        try:
            PygCtl.LstCtl.remove(self)
        except:
            pass
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN:
            if Evt.button == 5:
                self.Parent.ScrollDown()
            elif Evt.button == 4:#Wheel rolled up
                self.Parent.ScrollUp()
            elif Evt.button == 1 or Evt.button == 3:#left click
                if self.RelPos == 0:#selected
                    return self.Click(Evt)
                elif self.RelPos > 0:
                    #self.Parent.ScrollDown()
                    return self.Click(Evt)
                elif self.RelPos < 0:
                    #self.Parent.ScrollUp()
                    return self.Click(Evt)
        return False
    def Click(self, Evt):
        return False
    def Show(self):
        self.IsShow = True
        if not(self in PygCtl.LstCtl):
            PygCtl.LstCtl.insert(self.zIndex, self)
        PygCtl.SetRedraw(self)
    def Draw(self, Surf):
        if self.IsShow and self.Pos != None:
            Img = self.Img
            if self.Img == None: Img = self.GetImg()
            if Img == None: return []
            self.PrevRect = Surf.blit(Img, self.Pos)
            return [self.PrevRect]
        return []
    def PreDraw(self, Surf):
        if self.PrevRect != None:
            Rtn = Surf.fill(PygCtl.BKGR, self.PrevRect)
            self.PrevRect = None
            return [Rtn]
        return []
    def SetPos(self, Pos, Index):
        self.Pos = Pos
        if self.IsShow: PygCtl.SetRedraw(self)
        self.RelPos = Index - self.Parent.CurPos
        self.CollRect = pygame.rect.Rect(self.Pos, self.GetSize())
    def CollidePt(self, Pt):
        return self.CollRect != None and self.CollRect.collidepoint(Pt)
    def GetSize(self):
        try:
            return self.Img.get_size()
        except AttributeError:
            return (0, 0)
    def GetImg(self):
        return None
def Hyperbola(y, b, a):
    return -a * (((y ** 2.0)/(b ** 2.0) + 1) ** .5)
class ScrollBase(PygCtl.PygCtl):
    def __init__(self, LstPrn, nDisp, Pos, Spacing, Anim=True):
        self.LstPrn = LstPrn
        for Child in self.LstPrn:
            Child.Parent = self
        self.CurPos = 0
        self.nDisp = nDisp
        self.RealPos = Pos
        self.PrevRect = None
        self.EvtTick = pygame.USEREVENT
        self.LnColor = PygCtl.WHITE
        pygame.time.set_timer(self.EvtTick, 1000 / 20)
        Off = .5
        if self.nDisp % 2 == 1: Off = 1
        self.Center = (self.nDisp - Off) * Spacing
        self.Spacing = Spacing
        self.Tick = 0
        self.MaxTick = 10
        self.Width = 0
        for Elem in LstPrn:
            ElemW = Elem.GetSize()[0]
            if ElemW > self.Width: self.Width = ElemW
        self.xOffPos = 0
        self.SetVisual(nDisp, Spacing)
        if Anim: self.Animate()
    def GetElemXOff(self, yOffCenter):
        return 0
    def SetVisual(self, nDisp, Spacing = None):
        self.nDisp = nDisp
        if Spacing != None: self.Spacing = Spacing
        StartOff = (self.nDisp / 2) * self.Spacing
        self.xOffPos = self.GetElemXOff(StartOff - self.Center)
        MidOff = self.GetElemXOff(0)
        yOffPos = (self.nDisp - self.nDisp % 2) * self.Spacing / 2
        self.Pos = (self.RealPos[0] - self.xOffPos, self.RealPos[1] - yOffPos)
        self.CollRect = pygame.rect.Rect(self.RealPos[0], self.RealPos[1], self.Width + (MidOff - self.xOffPos), self.nDisp * self.Spacing)
        #print self.xOffPos, MidOff, self.Width
    def PreDraw(self, Surf):
        if self.PrevRect != None:
            Surf.fill(PygCtl.BKGR, self.PrevRect)
            Rtn = self.PrevRect
            self.PrevRect = None
            return [Rtn]
        return []
    def Draw(self, Surf):
        #Fixes a problem with antialiased alpha blending ListChild instances
        #  Only a Temporary fix
        Surf.fill(PygCtl.BKGR, self.CollRect)
        self.PrevRect = pygame.draw.rect(Surf, self.LnColor, self.CollRect, 1)
        return [self.PrevRect]
    def OnEvtGlobal(self, Evt):
        if Evt.type == self.EvtTick:
            if self.Tick == 0: return False
            elif self.Tick > 0: self.Tick -= 1
            elif self.Tick < 0: self.Tick += 1
            self.Animate()
        return False
    def Animate(self):
        Start = self.CurPos - self.nDisp / 2
        StartOff = (self.nDisp / 2) * self.Spacing + (self.Tick * self.Spacing / self.MaxTick)
        if Start < 0:
            StartOff += -Start * self.Spacing
            Start = 0
        End = self.CurPos + (self.nDisp + 1) / 2
        if End > len(self.LstPrn):
            End = len(self.LstPrn)
        for c in xrange(max(0, Start - self.nDisp), Start):
            self.LstPrn[c].Hide()
        for c in xrange(Start, End):
            self.LstPrn[c].Show()
            xOffPos = self.GetElemXOff(StartOff - self.Center)
            self.LstPrn[c].SetPos((self.Pos[0] + xOffPos, StartOff + self.Pos[1]), c)
            StartOff += self.Spacing
        for c in xrange(End, min(len(self.LstPrn), End + self.nDisp)):
            self.LstPrn[c].Hide()
        UpdPos()
    def CollidePt(self, Pt):
        return self.CollRect.collidepoint(Pt)
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN:
            if Evt.button == 5:
                self.ScrollDown()
            elif Evt.button == 4:#Wheel rolled up
                self.ScrollUp()
        return False
    def ScrollDown(self):
        if self.CurPos < len(self.LstPrn) - 1:
            self.CurPos += 1
            self.Tick = self.MaxTick
            self.Animate()
    def ScrollUp(self):
        if self.CurPos > 0:
            self.CurPos -= 1
            self.Tick = -self.MaxTick
            self.Animate()
class HyperScroll(ScrollBase):
    def __init__(self, LstPrn, nDisp, Pos, Spacing, aH = 50, bH = 60):
        self.aH = aH
        self.bH = bH
        super(HyperScroll, self).__init__(LstPrn, nDisp, Pos, Spacing)
    def GetElemXOff(self, y):#y = yOffCenter
        return -self.aH * (((y ** 2.0)/(self.bH ** 2.0) + 1) ** .5)
class ClkLstElem(ListChild):
    def __init__(self, Lbl, Fnt, Color = (PygCtl.WHITE, PygCtl.RED)):
        super(ClkLstElem, self).__init__(0)
        self.Fnt = Fnt
        self.SetLbl(Lbl, Color)
    def SetLbl(self, Lbl = None, Color = None):
        global CacheImgs
        if Color != None: self.Color = Color
        if Lbl != None: self.Lbl = Lbl
        if CacheImgs: self.Img = self.GetImg()
        if self in PygCtl.LstCtl: PygCtl.SetRedraw(self)
    def Click(self, Evt):
        return False
    def GetImg(self):
        if self.Color[1] == None:
            return self.Fnt.render(self.Lbl, False, self.Color[0])
        return self.Fnt.render(self.Lbl, False, self.Color[0], self.Color[1])
    def GetSize(self):
        global CacheImgs
        if CacheImgs: return super(ListChild, self).GetSize()
        else: return self.Fnt.size(self.Lbl)
class LblElem(ClkLstElem):
    def __init__(self, Lbl, Fnt, Color = (PygCtl.WHITE, PygCtl.RED)):
        super(LblElem, self).__init__(Lbl, Fnt, Color)
        self.Selected = False
        self.Queued = False
    def Click(self, Evt):
        if Evt.button == 1:
            self.Selected = not self.Selected
        elif Evt.button == 3:
            self.Queued = not self.Queued
        else: return False
        self.Color = (PygCtl.WHITE, PygCtl.RED)
        if self.Queued:
            self.Color = (PygCtl.WHITE, (0, 0, 255))
        if self.Selected:
            self.Color = (PygCtl.WHITE, PygCtl.GREEN)
        self.SetLbl()
SymCh = "!@#$%^&*()[]{}:;<>,./?~`-+=\\|"
def GetPosInKern(Fnt, Txt0, Pos):
    CurW = Fnt.size(Txt0[:Pos + 1])[0]
    ChW = Fnt.size(Txt0[Pos:Pos + 1])[0]
    return CurW - ChW
#Translated from C++ from TemplateUtils.h in KyleUtils
def BinaryApprox(List, Val):
    Len = len(List)
    CurLen = Len
    Pos = Len >> 1
    while CurLen > 0:
        if Val <= List[Pos] and (Pos == 0 or Val >= List[Pos - 1]):
            return Pos
        elif Val < List[Pos]:
            CurLen >>= 1
            Pos -= (CurLen + 1) >> 1
        else:
            CurLen = (CurLen - 1) >> 1
            Pos += (CurLen >> 1) + 1
    return Len
class FuncListView(object):
    def __init__(self, Func, Len):
        self.Cache = [None] * Len
        self.Func = Func
    def __len__(self):
        return len(self.Cache)
    def __getitem__(self, Index):
        if self.Cache[Index] == None: self.Cache[Index] = self.Func(Index)
        return self.Cache[Index]
ClipBoardTypes = [pygame.SCRAP_TEXT, "STRING", "UTF8_STRING"]
"""
EntryLine(Fnt, Pos, Size, Colors, PreChg, PostChg, Enter, DefTxt, Censor)
    Fnt: type FROM pygame.font: Font, SysFont
        Effect: Style of the text that the user types in the EntryLine
    Size: indexable, 2 elements
        Example (list): [Width, Height]
        Units: pixels
        Effect: Size of the collision box of the EntryLine
    Colors: type iterable, 1 or 2 3-tuples
        Effect:
            Colors[0] is the color of the text
            Colors[1] if 2 elements, is the background color
                else, background color is transparent
        Units: 3-tuples of (R, G, B) each is 0-255
    PreChg: OPTIONAL, type (callable)(Inst, Evt) -> bool(AllowEdit)
        Effect:
            called after an event is processed but before the text is changed,
            returning False will result in the edit not going through
            returning True will result in the edit going through
            NOTE: do not change the text in this function, do that in PostChg
    PostChg: OPTIONAL, type (callable)(Inst, Evt)
        Effect:
            called after text is changed
            NOTE: you can change the text in this function
    Enter: OPTIONAL, type (callable)(Inst)
        Effect:
            called after the return/enter key is pressed
    DefTxt: OPTIONAL, type iterable of characters ie: str, list (of len 1 str)
        Effect:
            Text that is already in the EntryLine box,
            This text is treated the same way as text entered by the user
                It does not disappear when the user types/clicks in the box
    Censor: OPTIONAL, type (callable)(Txt) -> (str/unicode)(CensoredTxt)
        Effect:
            called during drawing to get the text that will be displayed
            called for mouse clicks and moves to get the text for
                selection region and cursor positioning calculation
            NOTE: does not change the actual text in the box
Attributes for EntryLine:
    HiLtCol: type iterable, 1 or 2 3-tuples
        Effect: For highlighted text
            Colors[0] is the color of the text
            Colors[1] if 2 elements, is the background color
                else, background color is transparent
"""
class EntryLine(PygCtl.PygCtl):
    CursorTmr = pygame.USEREVENT + 1
    #Cursor Threshhold, the fraction of character width
    #  that represents border between 2 char positions
    CursTH = .3
    @staticmethod
    def NextWord(LstTxt, TxtPos):
        CurTyp = -1
        for c in xrange(TxtPos, len(LstTxt)):
            Ch = LstTxt[c]
            if Ch.isalnum() or Ch == '_':
                if CurTyp == -1: CurTyp = 0
                elif CurTyp != 0: return c
            elif Ch in SymCh:
                if CurTyp == -1: CurTyp = 1
                elif CurTyp != 1: return c
            elif Ch.isspace():
                if CurTyp != -1: return c
            else:
                if CurTyp == -1: CurTyp = 2
                elif CurTyp != 2: return c
        return len(LstTxt)
    @staticmethod
    def PrevWord(LstTxt, TxtPos):
        CurTyp = -1
        for c in xrange(TxtPos, 0, -1):
            Ch = LstTxt[c - 1]
            if Ch.isalnum() or Ch == '_':
                if CurTyp == -1: CurTyp = 0
                elif CurTyp != 0: return c
            elif Ch in SymCh:
                if CurTyp == -1: CurTyp = 1
                elif CurTyp != 1: return c
            elif Ch.isspace():
                if CurTyp != -1: return c
            else:
                if CurTyp == -1: CurTyp = 2
                elif CurTyp != 2: return c
        return 0
    @classmethod
    def InitTimer(cls, EvtCode = None):
        if EvtCode != None: cls.CursorTmr = EvtCode
        pygame.time.set_timer(cls.CursorTmr, 500)
        pygame.scrap.init()
    def __init__(self, Fnt, Pos, Size, Colors, PreChg=None, PostChg=None, Enter=None, DefTxt="", Censor=None):
        self.Colors = Colors
        self.HltCol = [(255,255,255),(0,0,255)]
        self.Pos = Pos
        self.Size = Size
        self.PreChg = PreChg
        self.PostChg = PostChg
        self.Enter = Enter
        self.Censor = Censor
        self.IsSel = False
        self.HiLite = False
        self.HiLtPos = 0
        self.Txt = list(DefTxt)
        self.ChPos = 0
        self.ChOff = 0#x offset in pixels
        self.CurKey = None
        self.CollRect = pygame.rect.Rect(self.Pos, self.Size)
        self.PrevRect = self.CollRect
        self.Fnt = Fnt
        self.CursorSt = True
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN:
            DrawTxt = u"".join(self.Txt)
            if self.Censor != None: DrawTxt = self.Censor(DrawTxt)
            self.HiLite = True
            self.IsSel = True
            Pos = (Pos[0] - self.Pos[0], Pos[1] - self.Pos[1])
            CTH = EntryLine.CursTH
            GetSzTxt = lambda x: self.Fnt.size(DrawTxt[:x])[0]
            LstV = FuncListView(GetSzTxt, len(DrawTxt))
            #since LstV[0] == 0 and Pos[0] >= 0 is True, result->ChPos >= 1
            ChPos = BinaryApprox(LstV, Pos[0])
            if ChPos < len(LstV):
                OffX = LstV[ChPos-1]
                ChW = LstV[ChPos] - OffX
                if Pos[0] - OffX <= CTH * ChW:ChPos -= 1
            self.ChPos = ChPos
            self.HiLtPos = ChPos
            return True
        return False
    def OnPreChg(self, Evt):
        return self.PreChg == None or self.PreChg(self, Evt)
    def OnEvtGlobal(self, Evt):
        if Evt.type == pygame.MOUSEBUTTONDOWN:
            if self.CollRect.collidepoint(Evt.pos): return False
            if (self.HiLite or self.IsSel):
                self.HiLite = False
                self.IsSel = False
        elif Evt.type == pygame.MOUSEBUTTONUP:
            if self.HiLite: self.HiLite = False
        elif Evt.type == pygame.MOUSEMOTION and self.HiLite:
            DrawTxt = u"".join(self.Txt)
            if self.Censor != None: DrawTxt = self.Censor(DrawTxt)
            Pos = Evt.pos
            Pos = [Pos[0] - self.Pos[0], Pos[1] - self.Pos[1]]
            if Pos[0] < 0: Pos[0] = 0
            CTH = EntryLine.CursTH
            GetSzTxt = lambda x: self.Fnt.size(DrawTxt[:x])[0]
            LstV = FuncListView(GetSzTxt, len(DrawTxt))
            #since LstV[0] == 0 and Pos[0] >= 0 is True, result->ChPos >= 1
            ChPos = BinaryApprox(LstV, Pos[0])
            if ChPos < len(LstV):
                OffX = LstV[ChPos-1]
                ChW = LstV[ChPos] - OffX
                if Pos[0] - OffX <= CTH * ChW:ChPos -= 1
            self.ChPos = ChPos
            return True
        elif Evt.type == pygame.KEYDOWN and self.IsSel:
            IsChg = False
            if Evt.key == pygame.K_BACKSPACE:
                if not ((self.ChPos > 0 or self.ChPos != self.HiLtPos) and self.OnPreChg(Evt)):
                    return False
                elif Evt.mod & pygame.KMOD_CTRL > 0:
                    Start = EntryLine.PrevWord(self.Txt, self.ChPos)
                    self.Txt[Start:self.ChPos] = []
                    Off = self.ChPos - Start
                    DoOff = 0#Default make HiLtPos = ChPos
                    if self.HiLtPos > self.ChPos: DoOff = 1#Offset HiLtPos same amount as ChPos
                    elif self.HiLtPos < self.ChPos - Start: DoOff = 2#Leave HiLtPos Alone
                    self.ChPos = Start
                    if DoOff == 1: self.HiLtPos -= Off
                    elif DoOff == 0: self.HiLtPos = self.ChPos
                    IsChg = True
                else:
                    if self.ChPos != self.HiLtPos:
                        Start, End = sorted((self.ChPos, self.HiLtPos))
                        self.Txt[Start:End] = []
                        self.ChPos = Start
                    else:
                        self.ChPos -= 1
                        self.Txt.pop(self.ChPos)
                    IsChg = True
                    self.HiLtPos = self.ChPos
            elif Evt.key == pygame.K_DELETE:
                if not ((self.ChPos < len(self.Txt) or self.ChPos != self.HiLtPos) and self.OnPreChg(Evt)):
                    return False
                elif Evt.mod & pygame.KMOD_CTRL > 0:
                    End = EntryLine.NextWord(self.Txt, self.ChPos)
                    self.Txt[self.ChPos:End] = []
                    Off = End - self.ChPos
                    if self.HiLtPos > self.ChPos: self.HiLtPos -= Off
                    IsChg = True
                else:
                    if self.ChPos != self.HiLtPos:
                        Start, End = sorted((self.ChPos, self.HiLtPos))
                        self.Txt[Start:End] = []
                        self.ChPos = Start
                        self.HiLtPos = Start
                    else:
                        self.Txt.pop(self.ChPos)
                    IsChg = True
                self.HiLtPos = self.ChPos
            elif Evt.key == pygame.K_HOME:
                self.ChPos = 0
                if Evt.mod & pygame.KMOD_SHIFT == 0:self.HiLtPos = self.ChPos
            elif Evt.key == pygame.K_END:
                self.ChPos = len(self.Txt)
                if Evt.mod & pygame.KMOD_SHIFT == 0:self.HiLtPos = self.ChPos
            elif Evt.key == pygame.K_RETURN:
                if self.Enter != None: self.Enter(self)
            elif Evt.key == pygame.K_LEFT:
                if Evt.mod & pygame.KMOD_CTRL > 0:
                    self.ChPos = EntryLine.PrevWord(self.Txt, self.ChPos)
                elif self.ChPos > 0:
                    if Evt.mod&pygame.KMOD_SHIFT==0 and self.ChPos!=self.HiLtPos:
                        Start, End = sorted((self.ChPos, self.HiLtPos))
                        self.ChPos = Start
                    else: self.ChPos -= 1
                if Evt.mod & pygame.KMOD_SHIFT == 0:self.HiLtPos = self.ChPos
            elif Evt.key == pygame.K_RIGHT:
                if Evt.mod & pygame.KMOD_CTRL > 0:
                    self.ChPos = EntryLine.NextWord(self.Txt, self.ChPos)
                elif self.ChPos < len(self.Txt):
                    if Evt.mod&pygame.KMOD_SHIFT==0 and self.ChPos!=self.HiLtPos:
                        Start, End = sorted((self.ChPos, self.HiLtPos))
                        self.ChPos = End
                    else: self.ChPos += 1
                if Evt.mod & pygame.KMOD_SHIFT == 0:self.HiLtPos = self.ChPos
            elif Evt.mod & pygame.KMOD_CTRL > 0:
                Start, End = sorted((self.ChPos, self.HiLtPos))
                if Evt.key == pygame.K_v:
                    Data = None
                    for Item in ClipBoardTypes:
                        if Item in pygame.scrap.get_types():
                            Data = pygame.scrap.get(Item)
                            if Data != None:break
                    if Data == None or not self.OnPreChg(Evt): return False
                    self.Txt[Start:End] = Data
                    self.ChPos = Start + len(Data)
                    self.HiLtPos = self.ChPos
                    IsChg = True
                elif Evt.key == pygame.K_c:
                    pygame.scrap.put(pygame.SCRAP_TEXT, bytes(u"".join(self.Txt[Start:End])))
                elif Evt.key == pygame.K_x:
                    if Start == End or not self.OnPreChg(Evt): return False
                    pygame.scrap.put(pygame.SCRAP_TEXT, bytes(u"".join(self.Txt[Start:End])))
                    self.Txt[Start:End] = []
                    self.ChPos = Start
                    self.HiLtPos = Start
                    IsChg = True
            elif len(Evt.unicode) > 0:
                if not self.OnPreChg(Evt): return False
                Start, End = sorted((self.ChPos, self.HiLtPos))
                self.Txt[Start:End] = Evt.unicode
                self.ChPos = Start + 1
                self.HiLtPos = self.ChPos
                IsChg = True
            if IsChg and self.PostChg != None: self.PostChg(self, Evt)
            return True
        elif Evt.type == EntryLine.CursorTmr:
            if self.IsSel:
                self.CursorSt = not self.CursorSt
                return True
        return False
    def Draw(self, Surf):
        DrawTxt = u"".join(self.Txt)
        if self.Censor != None: DrawTxt = self.Censor(DrawTxt)
        Img = None
        if self.ChPos != self.HiLtPos:
            Start, End = sorted((self.ChPos, self.HiLtPos))
            BegW = GetPosInKern(self.Fnt, DrawTxt, Start)
            EndW = GetPosInKern(self.Fnt, DrawTxt, End)
            Img = pygame.Surface(self.Fnt.size(DrawTxt), pygame.SRCALPHA)
            Img.blit(self.Fnt.render(DrawTxt[:Start], True, self.Colors[0]), (0, 0))
            Img.blit(self.Fnt.render(DrawTxt[Start:End], True, *self.HltCol), (BegW, 0))
            Img.blit(self.Fnt.render(DrawTxt[End:], True, self.Colors[0]), (EndW, 0))
        else:
            Img = self.Fnt.render(DrawTxt, True, self.Colors[0])
        Rtn = []
        if len(self.Colors) > 1: Rtn.append(Surf.fill(self.Colors[1], self.CollRect))
        Rtn.append(Surf.blit(Img, self.Pos))
        if self.CursorSt:
            CursX = self.Fnt.size(DrawTxt[:self.ChPos])[0] + self.Pos[0] - 1
            Rtn.append(Surf.fill(self.Colors[0], pygame.Rect(CursX, self.Pos[1], 2, Img.get_height())))
        self.PrevRect = Rtn[-1].unionall(Rtn[:-1])
        return Rtn
    """def Draw(self, Surf):
        DrawTxt = u"".join(self.Txt)
        Img = self.Fnt.render(DrawTxt, True, self.Colors[0])
        Rtn = []
        if len(self.Colors) > 1: Rtn.append(Surf.fill(self.Colors[1], self.CollRect))
        Rtn.append(Surf.blit(Img, self.Pos))
        if self.CursorSt:
            CursX = self.Fnt.size(DrawTxt[:self.ChPos])[0] + self.Pos[0] - 1
            Rtn.append(Surf.fill(self.Colors[0], pygame.Rect(CursX, self.Pos[1], 2, Img.get_height())))
        self.PrevRect = Rtn[-1].unionall(Rtn[:-1])
        return Rtn"""
    def PreDraw(self, Surf):
        if self.PrevRect != None:
            Rtn = Surf.fill(PygCtl.BKGR, self.PrevRect)
            self.PrevRect = None
            return [Rtn]
        return []
    def CollidePt(self, Pt):
        return self.CollRect.collidepoint(Pt)
class Drawable(object):
    def Draw(self, Surf, Pos):
        return []
    def GetSize(self):
        return (0,0)
    def Rotate(self, IsClkWise):
        pass
class YGradient(Drawable):
    def __init__(self, Size, StartColor, EndColor):
        self.Size = Size
        self.GradDir = True #False: up, True: down
        self.LstGrad = [0] * self.Size[1]
        InitGrad(self.LstGrad, StartColor, EndColor)
        self.Img = pygame.surface.Surface(self.Size)
        for y in xrange(self.Size[1]):
            self.Img.fill(self.LstGrad[y], pygame.rect.Rect((0, y), (self.Size[0], 1)))
    def Draw(self, Surf, Pos):
        return [Surf.blit(self.Img, Pos)]
    def GetSize(self):
        return self.Img.get_size()
    def Rotate(self, IsClkWise):
        Angle = 90
        if IsClkWise: Angle = -Angle
        self.Img = pygame.transform.rotate(self.Img, Angle)
    def SetGradDir(self, Down = True):
        if self.GradDir != Down:
            if Down:
                for y in xrange(self.Size[1]):
                    self.Img.fill(self.LstGrad[y], pygame.rect.Rect((0, y), (self.Size[0], 1)))
            else:
                for y in xrange(1, self.Size[1] + 1):
                    self.Img.fill(self.LstGrad[-y], pygame.rect.Rect((0, y), (self.Size[0], 1)))
            self.GradDir = Down
DefGradBtn = {"n-from": (0xF7, 0xF7, 0xF7), "n-to": (0xDC, 0xDC, 0xDC), "border": (1, (0x99, 0x99, 0x99), (0x77, 0x77, 0x77)), "txt-color": (0,0,0)}
MyGradBtn = dict(DefGradBtn)
#MyGradBtn["n-from"] = Combine(DefGradBtn["n-from"], (0, 0, 255), .23)
#MyGradBtn["n-to"] = Combine(DefGradBtn["n-to"], (0, 255, 0), .23)
#MyGradBtn["border"] = DefGradBtn["border"][0:1] + (MulColor(0, 255, 255), 9/15.0), MulColor((0, 255, 255), 7/15.0))
MyGradBtn["border"] = DefGradBtn["border"][0:1] + ((128, 0, 0), (255, 0, 0))
class GradBtn(PygCtl.PressBtn):
    def __init__(self, Lbl, ActFunc, Pos, Fnt, Padding = None, Colors = DefGradBtn):
        self.Pos = Pos
        self.ActFunc = ActFunc
        if Padding == None: Padding = (2, 2)
        self.BoxSz = Colors["border"][0]
        self.BoxColor = Colors["border"][1]
        self.BoxColors = Colors["border"][1:3]
        self.TxtColor = Colors["txt-color"]
        self.Padding = Padding
        self.Lbl = Lbl
        self.Fnt = Fnt
        self.CurSt = False
        self.TotRect = None
        self.RecalcRect()
        self.DrawObj = YGradient(self.Size, Colors["n-from"], Colors["n-to"])
        #self.BrdRect = pygame.rect.Rect(self.Pos[0] + self.BoxSz, self.Pos[1] + self.BoxSz, self.Size[0] - self.BoxSz, self.Size[1] - self.BoxSz)
        self.BrdRect = self.TotRect
    def OnMouseEnter(self):
        if not self.CurSt: self.BoxColor = self.BoxColors[1]
        return True
    def OnMouseExit(self):
        self.BoxColor = self.BoxColors[0]
        return True
    def OnMDown(self, Evt):
        if Evt.button != 1: return False
        self.CurSt = True
        self.DrawObj.SetGradDir(False)
        self.BoxColor = self.BoxColors[0]
        return True
    def OnMUp(self, Evt):
        if Evt.button != 1: return False
        if not self.CurSt: return False
        self.CurSt = False
        self.BoxColor = self.BoxColors[1]
        self.DrawObj.SetGradDir(True)
        if self.ActFunc != None: self.ActFunc(self, Evt.pos)
        return True
    def OnEvtGlobal(self, Evt):
        if self.CurSt and Evt.type == pygame.MOUSEBUTTONUP and Evt.button == 1:
            self.CurSt = False
            self.DrawObj.SetGradDir(True)
            return True
        return False
    def Draw(self, Surf):
        Rtn = []
        Rtn.extend(self.DrawObj.Draw(Surf, self.Pos))
        Rtn.append(pygame.draw.rect(Surf, self.BoxColor, self.BrdRect, self.BoxSz))
        Rtn.append(Surf.blit(self.TxtImg, (self.Pos[0] + self.TxtOff[0], self.Pos[1] + self.TxtOff[1])))
        self.PrevRect = self.TotRect
        return Rtn
    def RecalcRect(self):
        TxtSz = self.Fnt.size(self.Lbl)
        Padding = self.Padding[0] + self.BoxSz + 1, self.Padding[1] + self.BoxSz + 1
        Size = TxtSz[0] + Padding[0] * 2, TxtSz[1] + Padding[1] * 2
        self.TxtOff = (Size[0] - TxtSz[0]) / 2, (Size[1] - TxtSz[1]) / 2
        self.Size = Size
        self.TxtImg = self.Fnt.render(self.Lbl, 1, self.TxtColor)
        self.PrevRect = self.TotRect
        self.TotRect = pygame.rect.Rect(self.Pos, self.Size)
        
def Main():
    PygCtl.Init()
    MyFnt = pygame.font.SysFont("Courier New", 20)
    MyLst = [
        LblElem("hello", MyFnt),
        LblElem("Not Really", MyFnt),
        LblElem("Of Course", MyFnt),
        LblElem("But Maybe", MyFnt),
        LblElem("Who Are You?", MyFnt),
        LblElem("This is a Text", MyFnt),
        LblElem("There are no", MyFnt),
        LblElem("swear words", MyFnt),
        LblElem("in this Test", MyFnt)]
    PygCtl.LstCtl.extend(MyLst)
    PygCtl.LstCtl.append(HyperScroll(MyLst, 6, (200, 100), MyFnt.size("h")[1]+ 8))
    PygCtl.LstCtl[-1].Animate()
    PygCtl.RunCtls()
    PygCtl.LstCtl = list()
    pygame.quit()
def FindLstWord(Txt, Lst, *args):
    Rtn = -1
    CurLen = 0
    for Word in Lst:
        Pos = Txt.find(Word, *args)
        if Pos != -1:
            if Pos < Rtn or Rtn == -1:
                CurLen = len(Word)
                Rtn = Pos
    return (Rtn, CurLen)
def Main1():
    PygCtl.BKGR = (192,192,192)
    PygCtl.Init()
    DctShared = {"Done": False}
    BanWords = ["ban", "bomb", "weird", "stupid"]
    def OnPreChg(Ln, Evt):
        return True
    def OnPostChg(Ln, Evt):
        Txt = u"".join(Ln.Txt).lower()
        for Word in BanWords:
            if Word in Txt:
                print "found banned word: " + Word
    def OnEnter(Ln):
        DctShared["Done"] = True
    def OnCensor(DrawTxt):
        LowTxt = DrawTxt.lower()
        Pos, Len = FindLstWord(LowTxt, BanWords)
        while Pos != -1:
            DrawTxt = DrawTxt[:Pos] + u"\u2022" * Len + DrawTxt[Pos+Len:]
            Pos, Len = FindLstWord(LowTxt, BanWords, Pos + 1)
        return DrawTxt
    IsDone = lambda: not DctShared["Done"]
    FntName = "Courier New"
    if pygame.font.match_font(FntName) == None: FntName = "liberation sans"
    MyFnt = pygame.font.SysFont(FntName, 16)
    MyLine = EntryLine(
        MyFnt, (25, 25), (200, MyFnt.size("M")[1] + 4),
        ((0, 0, 0),(128,192,192)), OnPreChg, OnPostChg, OnEnter,
        "BOMB you", OnCensor)
    PygCtl.LstCtl = [MyLine]
    pygame.key.set_repeat(250, 1000/30)
    EntryLine.InitTimer()
    PygCtl.RunCtls(IsDone)
    pygame.quit()
def PrnFunc(Btn, Pos):
    print "hello: " + str(Pos)
def Main2():
    PygCtl.Init()
    PygCtl.BKGR = (0xD0, 0xD0, 0xD0)
    FntName = "Arial"
    if pygame.font.match_font(FntName) == None: FntName = "liberation sans"
    MyFnt = pygame.font.SysFont(FntName, 12)
    PygCtl.LstCtl.append(GradBtn("hello there", PrnFunc, (10, 10), MyFnt, (6, 2)))
    PygCtl.LstCtl.append(GradBtn("hello there", PrnFunc, (10, 35), MyFnt, (6, 2), MyGradBtn))
    PygCtl.RunCtls()
    PygCtl.LstCtl = list()
    pygame.quit()
if __name__ == "__main__": Main1()

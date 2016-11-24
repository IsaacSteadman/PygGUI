import pygame
import random

#return True: redraw, False: no-redraw
class PygCtl(object):
    def Draw(self, Surf):
        return []
    def PreDraw(self, Surf):
        return []
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
    def DirtyRedraw(self, Surf, LstRects):
        Rtn = []
        try:
            if not isinstance(self.PrevRect, pygame.rect.RectType):
                raise AttributeError()
        except AttributeError: pass
        else:
            if self.PrevRect.collidelist(LstRects) != -1:
                Rtn.extend(self.Draw(Surf))
            return Rtn
        try:
            if not isinstance(self.TotRect, pygame.rect.RectType):
                raise AttributeError()
        except AttributeError: pass
        else:
            if self.TotRect.collidelist(LstRects) != -1:
                Rtn.extend(self.Draw(Surf))
            return Rtn
        return []
RED = (255,0,0)
GREEN = (0,255,0)
WHITE = (255,255,255)
BLACK = (0,0,0)
BKGR = BLACK
def CollidePtCircle(PtTest, PtCirc, Rad):
    OffX = PtTest[0] - PtCirc[0]
    OffY = PtTest[1] - PtCirc[1]
    return (OffX ** 2 + OffY ** 2) <= Rad ** 2
def CollideLineWidth(PtTest, Pt1, Pt2, Width):
    if CollidePtCircle(PtTest, Pt1, Width) or CollidePtCircle(PtTest, Pt2, Width): return True
    x1 = Pt1[0]
    x2 = Pt2[0]
    if x1 > Pt2[0]:
        x1 = Pt2[0]
        x2 = Pt1[0]
    y1 = Pt1[1]
    y2 = Pt2[1]
    if y1 > Pt2[1]:
        y1 = Pt2[1]
        y2 = Pt1[1]
    TheRect = None
    if Pt2[0] == Pt1[0]: TheRect = pygame.rect.Rect(Pt1[0] - Width, y1, Width * 2, y2 - y1)
    if Pt2[1] == Pt1[1]: TheRect = pygame.rect.Rect(x1, Pt1[1] - Width, x2 - x1, Width * 2)
    if TheRect is not None: return TheRect.collidepoint(PtTest)
    Slope = float(Pt2[1] - Pt1[1]) / (Pt2[0] - Pt1[0])
    m = Slope + 1 / Slope
    b1 = Pt1[1] - Pt1[0] * Slope
    b2 = PtTest[1] + PtTest[0] / Slope
    b = b1 - b2
    Cx = -b / m
    Cy = Slope * Cx + b1
    if Cx < x1 or Cx > x2 or Cy < y1 or Cy > y2: return False
    return CollidePtCircle(PtTest, (Cx, Cy), Width)
def GetEuclidDist(Pt1, Pt2):
    return ((Pt1[0] - Pt2[0]) ** 2 + (Pt1[1] - Pt2[1]) ** 2) ** .5
class Wire(PygCtl):
    def __init__(self, LstPts, Color, ActFunc = None):
        self.LstPts = list(LstPts)
        self.Color = Color
        self.Width = 1
        self.PrevWidth = 1
        self.PrevLstPts = None
        self.mWidth = 5
        self.ActFunc = ActFunc
        self.TotRect = None
    def PreDraw(self, Surf):
        if self.PrevLstPts is not None:
            return [pygame.draw.lines(Surf, BKGR, False, self.PrevLstPts, self.PrevWidth)]
        return []
    def Draw(self, Surf):
        if len(self.LstPts) < 2: return []
        self.PrevWidth = self.Width
        self.PrevLstPts = list(self.LstPts)
        self.TotRect = pygame.draw.lines(Surf, self.Color, False, self.LstPts, self.Width)
        return [self.TotRect]
    def DirtyRedraw(self, Surf, LstRects):
        if self.TotRect is not None and self.TotRect.collidelist(LstRects) == -1: return []
        Rtn = []
        for c in xrange(len(self.LstPts) - 1):
            x1 = self.LstPts[c][0]
            y1 = self.LstPts[c][1]
            x2 = self.LstPts[c + 1][0]
            y2 = self.LstPts[c + 1][1]
            if x2 < x1:
                xTmp = x2
                x2 = x1
                x1 = xTmp
            if y2 < y1:
                yTmp = y2
                y2 = y1
                y1 = yTmp
            LstColl = pygame.rect.Rect(x1, y1, x2 - x1, y2 - y1).collidelistall(LstRects)
            if len(LstColl) > 0:
                NewRect = pygame.draw.line(Surf, self.Color, self.LstPts[c], self.LstPts[c + 1], self.Width)
                for Index in LstColl:
                    if LstRects[Index].contains(NewRect): break
                else: Rtn.append(NewRect)
        return Rtn
    def OnMouseEnter(self):
        self.Width = 2
        return True
    def OnMouseExit(self):
        self.Width = 1
        return True
    def CollidePt(self, Pt):
        if len(self.LstPts) < 2: return False
        for c in xrange(len(self.LstPts) - 1):
            if CollideLineWidth(Pt, self.LstPts[c], self.LstPts[c + 1], self.mWidth): return True
        return False
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN and Evt.button == 1:
            Rtn = self.Cut(Pos)
            if self.ActFunc is not None: self.ActFunc()
            return Rtn
        else: return False
    def Cut(self, Pt):
        global LstCtl
        CurDist = 800
        CurPt = None
        CurPtPos = -1
        for c in xrange(len(self.LstPts)):
            FindPt = self.LstPts[c]
            TheDist = GetEuclidDist(FindPt, Pt)
            if TheDist < CurDist:
                CurPt = FindPt
                CurDist = TheDist
                CurPtPos = c
        c = CurPtPos
        LstNewPts = self.LstPts[0:c - 1]
        LstNewPts.append((self.LstPts[c][0] - 3, self.LstPts[c][1] + 10))
        self.LstPts = self.LstPts[c:]
        self.LstPts[0] = (self.LstPts[0][0] - 3, self.LstPts[0][1] - 10)
        NewWire = Wire(LstNewPts, self.Color, self.ActFunc)
        LstCtl.append(NewWire)
        SetRedraw(NewWire)
        return True
class Timer(PygCtl):
    def __init__(self, Hr, Min, Sec, Fnt, Pos, ActFunc = None):
        self.Sec = Sec + Min * 60 + Hr * 3600
        self.Color = WHITE
        self.Fnt = Fnt
        self.Pos = Pos
        Width, Height = Fnt.size("0")
        self.TotRect = pygame.rect.Rect(Pos, (Width * 8 + 1, Height))
        self.HrPos = Pos
        self.ColonPos1 = Pos[0] + Width * 2, Pos[1]
        self.MinPos = Pos[0] + Width * 3, Pos[1]
        self.ColonPos2 = Pos[0] + Width * 5, Pos[1]
        self.SecPos = Pos[0] + Width * 6, Pos[1]
        self.ImgColon = Fnt.render(":", False, self.Color)
        self.Disp = [Hr,Min,Sec]
        self.ActFunc = ActFunc
    def CalcNums(self):
        self.Disp[2] = self.Sec % 60
        self.Disp[1] = self.Sec / 60
        self.Disp[0] = self.Disp[1] / 60
        self.Disp[1] -= self.Disp[0] * 60
    def SetSec(self, Sec):
        self.Sec = Sec
        self.CalcNums()
    def PreDraw(self, Surf):
        return [Surf.fill(BKGR, self.TotRect)]
    def Draw(self, Surf):
        StrDisp = []
        for Num in self.Disp:
            Str = str(Num)
            StrDisp.append((2 - len(Str)) * "0" + Str)
        Surf.blit(self.Fnt.render(StrDisp[0], False, self.Color), self.HrPos)
        Surf.blit(self.ImgColon, self.ColonPos1)
        Surf.blit(self.Fnt.render(StrDisp[1], False, self.Color), self.MinPos)
        Surf.blit(self.ImgColon, self.ColonPos2)
        Surf.blit(self.Fnt.render(StrDisp[2], False, self.Color), self.SecPos)
        return [self.TotRect]
    def CollidePt(self, Pt):
        return self.TotRect.collidepoint(Pt)
    def OnEvtGlobal(self, Evt):
        if Evt.type == pygame.USEREVENT:
            self.Sec -= 1
            if self.Sec <= 0:
                self.Disp = [0,0,0]
                pygame.time.set_timer(pygame.USEREVENT, 0)
                if self.ActFunc is not None: self.ActFunc()
                return True
            self.Disp[2] -= 1
            if self.Disp[2] < 0:
                self.Disp[1] -= 1
                self.Disp[2] += 60
                if self.Disp[1] < 0:
                    self.Disp[0] -= 1
                    self.Disp[1] += 60
            return True
        return False
class Label(PygCtl):
    def __init__(self, Lbl, Pos, Fnt, TxtColor = (BKGR, WHITE)):
        self.Lbl = Lbl
        self.Fnt = Fnt
        self.Pos = Pos
        self.Color = TxtColor
        self.TotRect = pygame.rect.Rect(Pos, Fnt.size(Lbl))
        self.PrevRect = self.TotRect
    def CollidePt(self, Pos):
        return self.TotRect.collidepoint(Pos)
    def PreDraw(self, Surf):
        return [Surf.fill(BKGR, self.PrevRect)]
    def Draw(self, Surf):
        return [Surf.blit(self.Fnt.render(self.Lbl, 0, self.Color[1], self.Color[0]), self.Pos)]
    def SetLbl(self, Lbl):
        self.Lbl = Lbl
        self.PrevRect = self.TotRect
        self.TotRect = pygame.rect.Rect(Pos, Fnt.size(Lbl))
        SetRedraw(self)
class Button(PygCtl):
    def __init__(self, Lbl):
        self.Lbl = Lbl
        self.TotRect = None
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN:
            return self.OnMDown(Evt)
        elif Evt.type == pygame.MOUSEBUTTONUP:
            return self.OnMUp(Evt)
        elif Evt.type == pygame.KEYDOWN:
            return self.OnKDown(Evt, Pos)
        elif Evt.type == pygame.KEYUP:
            return self.OnKUp(Evt, Pos)
        else: return False
    def OnMDown(self, Evt):
        return False
    def OnMUp(self, Evt):
        return False
    def OnKDown(self, Evt, Pos):
        return False
    def OnKUp(self, Evt, Pos):
        return False
    def CollidePt(self, Pt):
        return self.TotRect is not None and self.TotRect.collidepoint(Pt)
    def RecalcRect(self):
        pass
    def SetLbl(self, Lbl):
        global LstRedraw
        self.Lbl = Lbl
        self.RecalcRect()
        SetRedraw(self)
class TogBtn(Button):
    def __init__(self, Lbl, Pos, Fnt, LstColors = ((RED, WHITE), (GREEN, WHITE)), LstActions = (None, None)):
        self.Lbl = Lbl
        self.LstColors = list(LstColors)
        self.LstActions = list(LstActions)
        self.CurSt = 0
        self.Pressed = False
        self.Pos = Pos
        self.Fnt = Fnt
        self.TotRect = pygame.rect.Rect(Pos, Fnt.size(Lbl))
        self.PrevRect = self.TotRect
    def OnMDown(self, Evt):
        if Evt.button != 1: return False
        self.Pressed = True
        return False
    def OnMUp(self, Evt):
        if Evt.button != 1: return False
        if not self.Pressed: return False
        self.Pressed = False
        self.CurSt += 1
        self.CurSt %= len(self.LstColors)
        CurAct = self.LstActions[self.CurSt]
        if CurAct is not None: CurAct(self, Evt.pos)
        return True
    def PreDraw(self, Surf):
        return [Surf.fill(BKGR, self.PrevRect)]
    def Draw(self, Surf):
        CurColor = self.LstColors[self.CurSt]
        return [Surf.blit(self.Fnt.render(self.Lbl, False, CurColor[1], CurColor[0]), self.Pos)]
    def RecalcRect(self):
        self.PrevRect = self.TotRect
        self.TotRect = pygame.rect.Rect(self.Pos, self.Fnt.size(self.Lbl))
class PressBtn(Button):
    def __init__(self, Lbl, ActFunc, Pos, Fnt, OffColor = (RED, WHITE), OnColor = (GREEN, WHITE)):
        self.Lbl = Lbl
        self.CurSt = False
        self.Pos = Pos
        self.Fnt = Fnt
        self.OffColor = OffColor
        self.OnColor = OnColor
        self.ActFunc = ActFunc
        self.TotRect = pygame.rect.Rect(Pos, Fnt.size(Lbl))
        self.PrevRect = self.TotRect
    def OnMDown(self, Evt):
        if Evt.button != 1: return False
        self.CurSt = True
        return True
    def OnMUp(self, Evt):
        if Evt.button != 1: return False
        if not self.CurSt: return False
        self.CurSt = False
        if self.ActFunc is not None: self.ActFunc(self, Evt.pos)
        return True
    def OnEvtGlobal(self, Evt):
        if self.CurSt and Evt.type == pygame.MOUSEBUTTONUP and Evt.button == 1:
            self.CurSt = False
            return True
        return False
    def PreDraw(self, Surf):
        return [Surf.fill(BKGR, self.PrevRect)]
    def Draw(self, Surf):
        CurColor = self.OffColor
        if self.CurSt: CurColor = self.OnColor
        return [Surf.blit(self.Fnt.render(self.Lbl, False, CurColor[1], CurColor[0]), self.Pos)]
    def RecalcRect(self):
        self.PrevRect = self.TotRect
        self.TotRect = pygame.rect.Rect(self.Pos, self.Fnt.size(self.Lbl))
class TpsMon(PygCtl):
    def __init__(self, Fnt, TxtColor, Pos):
        self.Fnt = Fnt
        self.Color = TxtColor
        self.Pos = Pos
        self.IsDisp = False
        self.Tps = 0
        self.Img = None
        self.PrevRect = None
        self.ActionKey = ord('t')
    def SetDisp(self, Set):
        self.IsDisp = Set
        if Set:
            if self.Img is None: self.Img = self.Fnt.render(str(self.Tps), False, self.Color)
            self.PrevRect = pygame.rect.Rect((self.Pos[0] - self.Img.get_width(), self.Pos[1]), self.Img.get_size())
            SetRedraw(self)
        else: self.Img = None
    def SetTps(self, Tps):
        if Tps != self.Tps:
            self.Tps = Tps
            if self.IsDisp:
                self.Img = self.Fnt.render(str(self.Tps), False, self.Color)
                SetRedraw(self)
            else: self.Img = None
    def PreDraw(self, Surf):
        if self.PrevRect is not None:
            TheRect = self.PrevRect
            if not self.IsDisp: self.PrevRect = None
            return [Surf.fill(BKGR, TheRect)]
        return []
    def Draw(self, Surf):
        if self.IsDisp:
            self.PrevRect = Surf.blit(self.Img, (self.Pos[0] - self.Img.get_width(), self.Pos[1]))
            return [self.PrevRect]
        return []
    def OnEvtGlobal(self, Evt):
        if Evt.type == pygame.KEYDOWN and Evt.key == self.ActionKey: self.SetDisp(not self.IsDisp)
        return False
Surf = None
def Init(Flags = 0):
    global Surf
    pygame.display.init()
    pygame.font.init()
    Surf = pygame.display.set_mode((640, 480), Flags)
LstCtl = []
LstRedraw = []
def SetRedraw(TheCtl):
    global LstRedraw
    if not(TheCtl in LstRedraw): LstRedraw.append(TheCtl)
CurPos = (0, 0)
def SetCtls(Lst):
    global LstCtl
    LstCtl = Lst
def MapCtls(Item):
    global LstCtl
    try:
        return LstCtl.index(Item)
    except:
        return Item
def MappedCmp(x, y):
    if isinstance(x, PygCtl): return -1
    elif isinstance(y, PygCtl): return 1
    else: return cmp(y, x)
#DctEvtFunc is a dictionary where k is the Evt.type, and v is a callable
#  the callable is called with 1 argument: Evt and returns True if
#  PygCtl should allow redraws from LstRedraw
DctEvtFunc = {}
UsedTime = 0
ChgdPos = False
def RunCtls(IsContFunc = None):
    global LstCtl
    global LstRedraw
    global CurPos
    global Surf
    global UsedTime
    global ChgdPos
    CurCtl = None
    def CalcCollide(CurCtl):
        global LstCtl
        global CurPos
        if CurCtl is None or not CurCtl.CollidePt(CurPos):
            if CurCtl is not None and CurCtl.OnMouseExit(): SetRedraw(CurCtl)
            CurCtl = None
            for Ctl in LstCtl:
                if Ctl.CollidePt(CurPos):
                    if Ctl.OnMouseEnter(): SetRedraw(Ctl)
                    CurCtl = Ctl
                    break
        elif CurCtl is not None:
            Pos = len(LstCtl)
            if CurCtl in LstCtl: Pos = LstCtl.index(CurCtl)
            for c in xrange(Pos):
                Ctl = LstCtl[c]
                if Ctl.CollidePt(CurPos):
                    if CurCtl.OnMouseExit(): SetRedraw(CurCtl)
                    if Ctl.OnMouseEnter(): SetRedraw(Ctl)
                    CurCtl = Ctl
                    break
            if not CurCtl in LstCtl: CurCtl = None
        return CurCtl
    Surf.fill(BKGR)
    for Ctl in LstCtl:
        Ctl.Draw(Surf)
    pygame.display.update()
    while IsContFunc is None or IsContFunc():
        Evt = pygame.event.wait()
        BegTime = pygame.time.get_ticks()
        if Evt.type == pygame.VIDEORESIZE:
            Surf = pygame.display.set_mode(Evt.size, pygame.RESIZABLE)
            Surf.fill(BKGR)
            for Ctl in LstCtl:
                Ctl.OnEvtGlobal(Evt)
                Ctl.Draw(Surf)
            pygame.display.update()
            continue
        CtlEvtAllow = True
        if Evt.type == pygame.QUIT: return -1
        elif ChgdPos:
            ChgdPos = False
            CurCtl = CalcCollide(CurCtl)
        elif Evt.type == pygame.MOUSEMOTION:
            CurPos = Evt.pos
            CurCtl = CalcCollide(CurCtl)
        elif DctEvtFunc.has_key(Evt.type):
            CtlEvtAllow = False
            if not DctEvtFunc[Evt.type](Evt): continue
        if CtlEvtAllow:
            if CurCtl is not None and CurCtl.OnEvt(Evt, CurPos): SetRedraw(CurCtl)
            for Ctl in LstCtl:
                if Ctl.OnEvtGlobal(Evt): SetRedraw(Ctl)
        if len(LstRedraw) == 0: continue
        LstCurDraw = map(MapCtls, LstRedraw)
        LstCurDraw.sort(MappedCmp)
        LstRects = []
        i = 0
        while i < len(LstCurDraw):
            if not isinstance(LstCurDraw[i], PygCtl): break
            LstRects.extend(LstCurDraw[i].PreDraw(Surf))
            i += 1
        for c in xrange(i, len(LstCurDraw)):
            Ctl = LstCtl[LstCurDraw[c]]
            LstRects.extend(Ctl.PreDraw(Surf))
        c = len(LstCtl)
        MatchPos = i
        LenCurDraw = len(LstCurDraw)
        while c > 0:
            c -= 1
            Ctl = LstCtl[c]
            if MatchPos < LenCurDraw and c == LstCurDraw[MatchPos]:
                MatchPos += 1
                LstRects.extend(Ctl.Draw(Surf))
            else:
                LstRects.extend(Ctl.DirtyRedraw(Surf, LstRects))
        LstRedraw = []
        pygame.display.update(LstRects)
        UsedTime += pygame.time.get_ticks() - BegTime

import pygame
import random

#return True: redraw, False: no-redraw
class PygCtl(object):
    def draw(self, Surf):
        return []
    def pre_draw(self, Surf):
        return []
    def on_evt(self, evt, pos):
        return False
    def on_evt_global(self, evt):
        return False
    def on_mouse_enter(self):
        return False
    def on_mouse_exit(self):
        return False
    def collide_pt(self, pt):
        return False
    def dirty_redraw(self, Surf, LstRects):
        Rtn = []
        try:
            if not isinstance(self.prev_rect, pygame.rect.RectType):
                raise AttributeError()
        except AttributeError:
            pass
        else:
            if self.prev_rect.collidelist(LstRects) != -1:
                Rtn.extend(self.draw(Surf))
            return Rtn
        try:
            if not isinstance(self.tot_rect, pygame.rect.RectType):
                raise AttributeError()
        except AttributeError:
            pass
        else:
            if self.tot_rect.collidelist(LstRects) != -1:
                Rtn.extend(self.draw(Surf))
            return Rtn
        return []
RED = (255,0,0)
GREEN = (0,255,0)
WHITE = (255,255,255)
BLACK = (0,0,0)
BKGR = BLACK
def collide_pt_circle(PtTest, PtCirc, Rad):
    OffX = PtTest[0] - PtCirc[0]
    OffY = PtTest[1] - PtCirc[1]
    return (OffX ** 2 + OffY ** 2) <= Rad ** 2
def collide_line_width(PtTest, Pt1, Pt2, Width):
    if collide_pt_circle(PtTest, Pt1, Width) or collide_pt_circle(PtTest, Pt2, Width):
        return True
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
    if Pt2[0] == Pt1[0]:
        TheRect = pygame.rect.Rect(Pt1[0] - Width, y1, Width * 2, y2 - y1)
    if Pt2[1] == Pt1[1]:
        TheRect = pygame.rect.Rect(x1, Pt1[1] - Width, x2 - x1, Width * 2)
    if TheRect is not None:
        return TheRect.collidepoint(PtTest)
    Slope = float(Pt2[1] - Pt1[1]) / (Pt2[0] - Pt1[0])
    m = Slope + 1 / Slope
    b1 = Pt1[1] - Pt1[0] * Slope
    b2 = PtTest[1] + PtTest[0] / Slope
    b = b1 - b2
    Cx = -b / m
    Cy = Slope * Cx + b1
    if Cx < x1 or Cx > x2 or Cy < y1 or Cy > y2:
        return False
    return collide_pt_circle(PtTest, (Cx, Cy), Width)
def get_euclid_dist(Pt1, Pt2):
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
        self.tot_rect = None
    def pre_draw(self, Surf):
        if self.PrevLstPts is not None:
            return [pygame.draw.lines(Surf, BKGR, False, self.PrevLstPts, self.PrevWidth)]
        return []
    def draw(self, Surf):
        if len(self.LstPts) < 2:
            return []
        self.PrevWidth = self.Width
        self.PrevLstPts = list(self.LstPts)
        self.tot_rect = pygame.draw.lines(Surf, self.Color, False, self.LstPts, self.Width)
        return [self.tot_rect]
    def dirty_redraw(self, Surf, LstRects):
        if self.tot_rect is not None and self.tot_rect.collidelist(LstRects) == -1:
            return []
        Rtn = []
        for c in range(len(self.LstPts) - 1):
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
                    if LstRects[Index].contains(NewRect):
                        break
                else:
                    Rtn.append(NewRect)
        return Rtn
    def on_mouse_enter(self):
        self.Width = 2
        return True
    def on_mouse_exit(self):
        self.Width = 1
        return True
    def collide_pt(self, pt):
        if len(self.LstPts) < 2:
            return False
        for c in range(len(self.LstPts) - 1):
            if collide_line_width(pt, self.LstPts[c], self.LstPts[c + 1], self.mWidth):
                return True
        return False
    def on_evt(self, evt, pos):
        if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
            Rtn = self.Cut(pos)
            if self.ActFunc is not None:
                self.ActFunc()
            return Rtn
        else:
            return False
    def Cut(self, pt):
        global LstCtl
        CurDist = 800
        CurPt = None
        CurPtPos = -1
        for c in range(len(self.LstPts)):
            FindPt = self.LstPts[c]
            TheDist = get_euclid_dist(FindPt, pt)
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
        set_redraw(NewWire)
        return True
class Timer(PygCtl):
    def __init__(self, Hr, Min, Sec, fnt, pos, ActFunc = None):
        self.Sec = Sec + Min * 60 + Hr * 3600
        self.Color = WHITE
        self.fnt = fnt
        self.pos = pos
        Width, Height = fnt.size("0")
        self.tot_rect = pygame.rect.Rect(pos, (Width * 8 + 1, Height))
        self.HrPos = pos
        self.ColonPos1 = pos[0] + Width * 2, pos[1]
        self.MinPos = pos[0] + Width * 3, pos[1]
        self.ColonPos2 = pos[0] + Width * 5, pos[1]
        self.SecPos = pos[0] + Width * 6, pos[1]
        self.ImgColon = fnt.render(":", False, self.Color)
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
    def pre_draw(self, Surf):
        return [Surf.fill(BKGR, self.tot_rect)]
    def draw(self, Surf):
        str_disp = []
        for Num in self.Disp:
            Str = str(Num)
            str_disp.append((2 - len(Str)) * "0" + Str)
        Surf.blit(self.fnt.render(str_disp[0], False, self.Color), self.HrPos)
        Surf.blit(self.ImgColon, self.ColonPos1)
        Surf.blit(self.fnt.render(str_disp[1], False, self.Color), self.MinPos)
        Surf.blit(self.ImgColon, self.ColonPos2)
        Surf.blit(self.fnt.render(str_disp[2], False, self.Color), self.SecPos)
        return [self.tot_rect]
    def collide_pt(self, pt):
        return self.tot_rect.collidepoint(pt)
    def on_evt_global(self, evt):
        if evt.type == pygame.USEREVENT:
            self.Sec -= 1
            if self.Sec <= 0:
                self.Disp = [0,0,0]
                pygame.time.set_timer(pygame.USEREVENT, 0)
                if self.ActFunc is not None:
                    self.ActFunc()
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
def CalcCenter(Sz, pos, CenterW = False, CenterH = False):
    PosX = pos[0] - (int(Sz[0] / 2) if CenterW else 0)
    PosY = pos[1] - (int(Sz[1] / 2) if CenterH else 0)
    return pygame.rect.Rect((PosX, PosY), Sz)
class Label(PygCtl):
    #Centered
    #  0: not centered
    #  1: x centered
    #  2: y centered
    #  3: x and y centered
    def __init__(self, lbl, pos, fnt, TxtColor = (BKGR, WHITE), Centered=0):
        self.lbl = lbl
        self.fnt = fnt
        self.pos = pos
        self.Color = TxtColor
        self.Centered = Centered
        self.tot_rect = CalcCenter(
            fnt.size(lbl), self.pos,
            bool(self.Centered&1), bool(self.Centered&2))
        self.prev_rect = None
    def collide_pt(self, pos):
        return self.tot_rect.collidepoint(pos)
    def pre_draw(self, Surf):
        if self.prev_rect is None:
            return [Surf.fill(BKGR, self.tot_rect)]
        else:
            Rtn = Surf.fill(BKGR, self.prev_rect)
            self.prev_rect = None
            return [Rtn]
    def draw(self, Surf):
        return [Surf.blit(self.fnt.render(self.lbl, 0, self.Color[1], self.Color[0]), self.tot_rect)]
    def set_lbl(self, lbl=None, Color=None, pos=None, Centered=None):
        NoChg = 0
        if lbl != None:
            self.lbl = lbl
        else:NoChg += 1
        if Color != None:
            self.Color = Color
        else:NoChg += 1
        if pos != None:
            self.pos = pos
        else:NoChg += 1
        if Centered != None:
            self.Centered = Centered
        else:NoChg += 1
        if NoChg >= 4:return
        if self.prev_rect is None:
            self.prev_rect = self.tot_rect
        else:
            self.prev_rect = self.prev_rect.union(self.tot_rect)
        self.tot_rect = CalcCenter(
            self.fnt.size(self.lbl), self.pos,
            bool(self.Centered&1), bool(self.Centered&2))
        set_redraw(self)
class Button(PygCtl):
    def __init__(self, lbl):
        self.lbl = lbl
        self.tot_rect = None
        self.glob_captures = {}
    def on_evt(self, evt, pos):
        if evt.type == pygame.MOUSEBUTTONDOWN:
            return self.on_mouse_down(evt)
        elif evt.type == pygame.MOUSEBUTTONUP:
            return self.on_mouse_up(evt)
        elif evt.type == pygame.KEYDOWN:
            return self.on_key_down(evt, pos)
        elif evt.type == pygame.KEYUP:
            return self.on_key_up(evt, pos)
        else:
            return False
    def AddGlobCapture(self, evt_type, Data):
        self.glob_captures[evt_type] = Data
    def RemGlobCapture(self, evt_type):
        if evt_type in self.glob_captures:
            del self.glob_captures[evt_type]
    def is_glob_capture(self, evt):
        if evt.type not in self.glob_captures:
            return False
        Data = self.glob_captures[evt.type]
        if isinstance(Data, dict):
            for k in Data:
                if getattr(evt, k) != Data[k]:
                    return False
            return True
        elif callable(Data):
            return Data(evt)
        elif isinstance(Data, (bool, int, long)):
            return bool(Data)
        else:
            return True
    def on_mouse_down(self, evt):
        return False
    def on_mouse_up(self, evt):
        return False
    def on_key_down(self, evt, pos):
        return False
    def on_key_up(self, evt, pos):
        return False
    def collide_pt(self, pt):
        return self.tot_rect is not None and self.tot_rect.collidepoint(pt)
    def recalc_rect(self):
        pass
    def set_lbl(self, lbl):
        global lst_redraw
        self.lbl = lbl
        self.recalc_rect()
        set_redraw(self)
class TogBtn(Button):
    def __init__(self, lbl, pos, fnt, LstColors = ((RED, WHITE), (GREEN, WHITE)), LstActions = (None, None), DefSt=0):
        super(TogBtn, self).__init__(lbl)
        self.LstColors = list(LstColors)
        self.LstActions = list(LstActions)
        self.CurSt = DefSt
        self.Pressed = False
        self.pos = pos
        self.fnt = fnt
        self.tot_rect = pygame.rect.Rect(pos, fnt.size(lbl))
        self.prev_rect = self.tot_rect
    def on_mouse_down(self, evt):
        if evt.button != 1:
            return False
        self.Pressed = True
        return False
    def on_mouse_up(self, evt):
        if evt.button != 1:
            return False
        if not self.Pressed:
            return False
        self.Pressed = False
        self.CurSt += 1
        self.CurSt %= len(self.LstColors)
        CurAct = self.LstActions[self.CurSt]
        if CurAct is not None:
            CurAct(self, evt.pos)
        return True
    def on_evt_global(self, evt):
        if self.is_glob_capture(evt):
            self.Pressed = False
            self.CurSt += 1
            self.CurSt %= len(self.LstColors)
            CurAct = self.LstActions[self.CurSt]
            if CurAct is not None:
                CurAct(self, self.pos)
            return True
    def pre_draw(self, Surf):
        return [Surf.fill(BKGR, self.prev_rect)]
    def draw(self, Surf):
        CurColor = self.LstColors[self.CurSt]
        return [Surf.blit(self.fnt.render(self.lbl, False, CurColor[1], CurColor[0]), self.pos)]
    def recalc_rect(self):
        self.prev_rect = self.tot_rect
        self.tot_rect = pygame.rect.Rect(self.pos, self.fnt.size(self.lbl))
class PressBtn(Button):
    def __init__(self, lbl, ActFunc, pos, fnt, OffColor = (RED, WHITE), OnColor = (GREEN, WHITE)):
        super(PressBtn, self).__init__(lbl)
        self.CurSt = False
        self.pos = pos
        self.fnt = fnt
        self.OffColor = OffColor
        self.OnColor = OnColor
        self.ActFunc = ActFunc
        self.tot_rect = pygame.rect.Rect(pos, fnt.size(lbl))
        self.prev_rect = self.tot_rect
    def on_mouse_down(self, evt):
        if evt.button != 1:
            return False
        self.CurSt = True
        return True
    def on_mouse_up(self, evt):
        if evt.button != 1:
            return False
        if not self.CurSt:
            return False
        self.CurSt = False
        if self.ActFunc is not None:
            self.ActFunc(self, evt.pos)
        return True
    def on_evt_global(self, evt):
        if self.CurSt and evt.type == pygame.MOUSEBUTTONUP and evt.button == 1:
            self.CurSt = False
            return True
        elif self.is_glob_capture(evt):
            self.CurSt = False
            if self.ActFunc is not None:
                self.ActFunc(self, self.pos)
            return True
        return False
    def pre_draw(self, Surf):
        return [Surf.fill(BKGR, self.prev_rect)]
    def draw(self, Surf):
        CurColor = self.OffColor
        if self.CurSt:
            CurColor = self.OnColor
        return [Surf.blit(self.fnt.render(self.lbl, False, CurColor[1], CurColor[0]), self.pos)]
    def recalc_rect(self):
        self.prev_rect = self.tot_rect
        self.tot_rect = pygame.rect.Rect(self.pos, self.fnt.size(self.lbl))
class TpsMon(PygCtl):
    def __init__(self, fnt, TxtColor, pos):
        self.fnt = fnt
        self.Color = TxtColor
        self.pos = pos
        self.IsDisp = False
        self.Tps = 0
        self.Img = None
        self.prev_rect = None
        self.ActionKey = ord('t')
    def SetDisp(self, Set):
        self.IsDisp = Set
        if Set:
            if self.Img is None:
                self.Img = self.fnt.render(str(self.Tps), False, self.Color)
            self.prev_rect = pygame.rect.Rect((self.pos[0] - self.Img.get_width(), self.pos[1]), self.Img.get_size())
            set_redraw(self)
        else:
            self.Img = None
    def SetTps(self, Tps):
        if Tps != self.Tps:
            self.Tps = Tps
            if self.IsDisp:
                self.Img = self.fnt.render(str(self.Tps), False, self.Color)
                set_redraw(self)
            else:
                self.Img = None
    def pre_draw(self, Surf):
        if self.prev_rect is not None:
            TheRect = self.prev_rect
            if not self.IsDisp:
                self.prev_rect = None
            return [Surf.fill(BKGR, TheRect)]
        return []
    def draw(self, Surf):
        if self.IsDisp:
            self.prev_rect = Surf.blit(self.Img, (self.pos[0] - self.Img.get_width(), self.pos[1]))
            return [self.prev_rect]
        return []
    def on_evt_global(self, evt):
        if evt.type == pygame.KEYDOWN and evt.key == self.ActionKey:
            self.SetDisp(not self.IsDisp)
        return False
Surf = None
def Init(Flags = 0):
    global Surf
    pygame.display.init()
    pygame.font.init()
    Surf = pygame.display.set_mode((640, 480), Flags)
LstCtl = []
lst_redraw = []
def set_redraw(TheCtl):
    global lst_redraw
    if not(TheCtl in lst_redraw):
        lst_redraw.append(TheCtl)
def set_list_redraw(LstRedrawCtl):
    global lst_redraw
    for TheCtl in LstRedrawCtl:
        if not (TheCtl in lst_redraw):
            lst_redraw.append(TheCtl)
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
    if isinstance(x, PygCtl):
        return -1
    elif isinstance(y, PygCtl):
        return 1
    else:
        return cmp(y, x)
#DctEvtFunc is a dictionary where k is the evt.type, and v is a callable
#  the callable is called with 1 argument: evt and returns True if
#  PygCtl should allow redraws from lst_redraw
DctEvtFunc = {}
UsedTime = 0
ChgdPos = False
def CalcCollide(CurCtl, LstCtl, CurPos):
    if CurCtl is None or not CurCtl.collide_pt(CurPos):
        if CurCtl is not None and CurCtl.on_mouse_exit():
            set_redraw(CurCtl)
        CurCtl = None
        for Ctl in LstCtl:
            if Ctl.collide_pt(CurPos):
                if Ctl.on_mouse_enter():
                    set_redraw(Ctl)
                CurCtl = Ctl
                break
    elif CurCtl is not None:
        pos = len(LstCtl)
        if CurCtl in LstCtl:
            pos = LstCtl.index(CurCtl)
        for c in range(pos):
            Ctl = LstCtl[c]
            if Ctl.collide_pt(CurPos):
                if CurCtl.on_mouse_exit():
                    set_redraw(CurCtl)
                if Ctl.on_mouse_enter():
                    set_redraw(Ctl)
                CurCtl = Ctl
                break
        if not CurCtl in LstCtl:
            CurCtl = None
    return CurCtl
def RunCtls(IsContFunc = None):
    global LstCtl
    global lst_redraw
    global CurPos
    global Surf
    global UsedTime
    global ChgdPos
    CurCtl = None
    Surf.fill(BKGR)
    for Ctl in LstCtl:
        Ctl.draw(Surf)
    pygame.display.update()
    while IsContFunc is None or IsContFunc():
        evt = pygame.event.wait()
        BegTime = pygame.time.get_ticks()
        if evt.type == pygame.VIDEORESIZE:
            if DctEvtFunc.has_key(evt.type):
                DctEvtFunc[evt.type](evt)
            Surf = pygame.display.set_mode(evt.size, pygame.RESIZABLE)
            Surf.fill(BKGR)
            for Ctl in LstCtl:
                Ctl.on_evt_global(evt)
                Ctl.draw(Surf)
            pygame.display.update()
            UsedTime += pygame.time.get_ticks() - BegTime
            continue
        CtlEvtAllow = True
        if evt.type == pygame.QUIT:
            return -1
        elif CurCtl is not None and CurCtl not in LstCtl:
            CurCtl = None
            ChgdPos = False
            CurCtl = CalcCollide(CurCtl, LstCtl, CurPos)
        elif ChgdPos:
            ChgdPos = False
            CurCtl = CalcCollide(CurCtl, LstCtl, CurPos)
        if evt.type == pygame.MOUSEMOTION:
            CurPos = evt.pos
            CurCtl = CalcCollide(CurCtl, LstCtl, CurPos)
        elif DctEvtFunc.has_key(evt.type):
            CtlEvtAllow = False
            if not DctEvtFunc[evt.type](evt):
                continue
        if CtlEvtAllow:
            if CurCtl is not None and CurCtl.on_evt(evt, CurPos):
                set_redraw(CurCtl)
            for Ctl in LstCtl:
                if Ctl.on_evt_global(evt):
                    set_redraw(Ctl)
        if len(lst_redraw) == 0:
            continue
        lst_cur_draw = map(MapCtls, lst_redraw)
        lst_cur_draw.sort(MappedCmp)
        LstRects = []
        i = 0
        while i < len(lst_cur_draw):
            if not isinstance(lst_cur_draw[i], PygCtl):
                break
            LstRects.extend(lst_cur_draw[i].pre_draw(Surf))
            i += 1
        for c in range(i, len(lst_cur_draw)):
            Ctl = LstCtl[lst_cur_draw[c]]
            LstRects.extend(Ctl.pre_draw(Surf))
        c = len(LstCtl)
        match_pos = i
        LenCurDraw = len(lst_cur_draw)
        while c > 0:
            c -= 1
            Ctl = LstCtl[c]
            if match_pos < LenCurDraw and c == lst_cur_draw[match_pos]:
                match_pos += 1
                LstRects.extend(Ctl.draw(Surf))
            else:
                LstRects.extend(Ctl.dirty_redraw(Surf, LstRects))
        lst_redraw = []
        pygame.display.update(LstRects)
        UsedTime += pygame.time.get_ticks() - BegTime
class WidgetGroup(object):
    def __init__(self):
        self.LstCtl = []
        self.lst_redraw = []
        self.CurCtl = None
        self.CurPos = (0,0)
        self.Surf = None
        self.UsedTime = None
        self.ChgdPos = False
        self.UpdateFunc = pygame.display.update
    def PygInit(self, Surf):
        self.Surf = Surf
    def ProcEvt(self, evt):
        Surf = self.Surf
        CurPos = self.CurPos
        CurCtl = self.CurCtl
        LstCtl = self.LstCtl
        lst_redraw = self.lst_redraw
        ChgdPos = self.ChgdPos
        UpdateFunc = self.UpdateFunc
        UsedTime = self.UsedTime
        try:
            BegTime = pygame.time.get_ticks()
            if evt.type == pygame.VIDEORESIZE:
                Surf = pygame.display.set_mode(evt.size, pygame.RESIZABLE)
                Surf.fill(BKGR)
                for Ctl in LstCtl:
                    Ctl.on_evt_global(evt)
                    Ctl.draw(Surf)
                UpdateFunc()
                return None
            CtlEvtAllow = True
            if evt.type == pygame.QUIT:
                return -1
            elif ChgdPos:
                ChgdPos = False
                CurCtl = CalcCollide(CurCtl, LstCtl, CurPos)
            elif evt.type == pygame.MOUSEMOTION:
                CurPos = evt.pos
                CurCtl = CalcCollide(CurCtl, LstCtl, CurPos)
            elif DctEvtFunc.has_key(evt.type):
                CtlEvtAllow = False
                if not DctEvtFunc[evt.type](evt):
                    return None
            if CtlEvtAllow:
                if CurCtl is not None and CurCtl.on_evt(evt, CurPos):
                    set_redraw(CurCtl)
                for Ctl in LstCtl:
                    if Ctl.on_evt_global(evt):
                        set_redraw(Ctl)
            if len(lst_redraw) == 0:
                return None
            lst_cur_draw = map(MapCtls, lst_redraw)
            lst_cur_draw.sort(MappedCmp)
            LstRects = []
            i = 0
            while i < len(lst_cur_draw):
                if not isinstance(lst_cur_draw[i], PygCtl):
                    break
                LstRects.extend(lst_cur_draw[i].pre_draw(Surf))
                i += 1
            for c in range(i, len(lst_cur_draw)):
                Ctl = LstCtl[lst_cur_draw[c]]
                LstRects.extend(Ctl.pre_draw(Surf))
            c = len(LstCtl)
            match_pos = i
            LenCurDraw = len(lst_cur_draw)
            while c > 0:
                c -= 1
                Ctl = LstCtl[c]
                if match_pos < LenCurDraw and c == lst_cur_draw[match_pos]:
                    match_pos += 1
                    LstRects.extend(Ctl.draw(Surf))
                else:
                    LstRects.extend(Ctl.dirty_redraw(Surf, LstRects))
            lst_redraw = []
            UpdateFunc(LstRects)
            UsedTime += pygame.time.get_ticks() - BegTime
        finally:
            self.Surf = Surf
            self.CurPos = CurPos
            self.CurCtl = CurCtl
            self.LstCtl = LstCtl
            self.lst_redraw = lst_redraw
            self.ChgdPos = ChgdPos
            self.UsedTime = UsedTime

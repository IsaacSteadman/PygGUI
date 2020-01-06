import PygCtl
from PygCtl import pygame
from ModuleHelper import *
from TextUtils import TextLineView, ClipboardHandler


class PygClipboard(ClipboardHandler):
    def __init__(self):
        pygame.scrap.init()

    def put(self, typ, data):
        Attrs = {"charset": "utf-16-le"}
        for attr in typ.split(";")[1:]:
            a = attr.split('=')
            if len(a) != 2:
                continue
            a, b = a
            Attrs[a] = b
        pygame.scrap.put(typ, data.encode(Attrs["charset"]))

    def get(self, typ):
        Attrs = {"charset": "utf-16-le"}
        for attr in typ.split(";")[1:]:
            a = attr.split('=')
            if len(a) != 2:
                continue
            a, b = a
            Attrs[a] = b
        return pygame.scrap.get(typ).decode(Attrs["charset"])


class PyperClipboard(ClipboardHandler):
    pyperclip = None

    def __init__(self):
        if self.pyperclip is None:
            import pyperclip
            self.pyperclip = pyperclip
            PyperClipboard.pyperclip = pyperclip

    def put(self, typ, data):
        assert typ == "UTF8_STRING" or typ.startswith("text/plain"), "PyperClipboard only works with text"
        self.pyperclip.copy(data)

    def get(self, typ):
        assert typ == "UTF8_STRING" or typ.startswith("text/plain"), "PyperClipboard only works with text"
        return self.pyperclip.paste()


# PygCtl = AttrWatcher(PygCtl)
cache_imgs = False
PygCtlAttrs = [
    "PygCtl",
    "RED",
    "GREEN",
    "WHITE",
    "BKGR",
    "PressBtn",
    "Init",
    "ctls",
    "set_redraw",
    "chgd_pos",
    "RunCtls"]
for attr in PygCtlAttrs:
    RequireAttr(PygCtl, attr)


def upd_pos():
    PygCtl.chgd_pos = True


def combine(a, b, Amt):
    return int(b[0] * Amt + a[0] * (1 - Amt)), int(b[1] * Amt + a[1] * (1 - Amt)), int(b[2] * Amt + a[2] * (1 - Amt))


def init_gradient(Lst, From, To):
    for c in range(len(Lst)):
        Lst[c] = combine(From, To, float(c) / len(Lst))


def mul_color(a, Amt):
    return tuple([int(x * Amt) for x in a])


def Hyperbola(y, b, a):
    return -a * (((y ** 2.0) / (b ** 2.0) + 1) ** .5)


class ListChild(PygCtl.PygCtl):
    def __init__(self, z_index):
        self.prev_rect = None
        self.pos = None
        self.z_index = z_index
        self.parent = None
        self.img = None
        self.is_show = True
        self.coll_rect = None

    def hide(self):
        self.is_show = False
        PygCtl.set_redraw(self)
        try:
            PygCtl.ctls.remove(self)
        except ValueError:
            pass

    def on_evt(self, app, evt, pos):
        if evt.type == pygame.MOUSEBUTTONDOWN:
            if evt.button == 5:
                self.parent.scroll_down()
            elif evt.button == 4:  # Wheel rolled up
                self.parent.scroll_up()
            elif evt.button == 1 or evt.button == 3:  # left click
                if self.rel_pos == 0:  # selected
                    return self.click(evt)
                elif self.rel_pos > 0:
                    # self.parent.scroll_down()
                    return self.click(evt)
                elif self.rel_pos < 0:
                    # self.parent.scroll_up()
                    return self.click(evt)
        return False

    def click(self, evt):
        return False

    def show(self):
        self.is_show = True
        if not (self in PygCtl.ctls):
            PygCtl.ctls.insert(self.z_index, self)
        PygCtl.set_redraw(self)

    def draw(self, app):
        if self.is_show and self.pos is not None:
            img = self.img
            if img is None:
                img = self.get_img()
            if cache_imgs:
                self.img = img
            else:
                self.img = None
            if img is None:
                return []
            self.prev_rect = surf.blit(img, self.pos)
            return [self.prev_rect]
        return []

    def pre_draw(self, app):
        if self.prev_rect is not None:
            rtn = surf.fill(PygCtl.BKGR, self.prev_rect)
            self.prev_rect = None
            return [rtn]
        return []

    def set_pos(self, pos, index):
        self.pos = pos
        if self.is_show:
            PygCtl.set_redraw(self)
        self.rel_pos = index - self.parent.cur_pos
        self.coll_rect = pygame.rect.Rect(self.pos, self.get_size())

    def collide_pt(self, pt):
        return self.coll_rect is not None and self.coll_rect.collidepoint(pt)

    def get_size(self):
        try:
            return self.img.get_size()
        except AttributeError:
            return 0, 0

    def get_img(self):
        return None


class ScrollBase(PygCtl.PygCtl):
    def __init__(self, lst_prn, n_disp, pos, spacing, anim=True):
        self.lst_prn = lst_prn
        for child in self.lst_prn:
            child.parent = self
        self.cur_pos = 0
        self.n_disp = n_disp
        self.real_pos = pos
        self.prev_rect = None
        self.tick_event_id = pygame.USEREVENT
        self.line_color = PygCtl.WHITE
        pygame.time.set_timer(self.tick_event_id, 1000 / 20)
        off = .5
        if self.n_disp % 2 == 1:
            off = 1
        self.center = (self.n_disp - off) * spacing
        self.spacing = spacing
        self.tick = 0
        self.max_tick = 10
        self.width = 0
        for elem in lst_prn:
            elem_w = elem.get_size()[0]
            if elem_w > self.width:
                self.width = elem_w
        self.x_off_pos = 0
        self.set_visual(n_disp, spacing)
        if anim:
            self.animate()

    def get_elem_x_off(self, y_off_center):
        return 0

    def set_visual(self, n_disp, spacing=None):
        self.n_disp = n_disp
        if spacing is not None:
            self.spacing = spacing
        start_off = (self.n_disp / 2) * self.spacing
        self.x_off_pos = self.get_elem_x_off(start_off - self.center)
        mid_off = self.get_elem_x_off(0)
        y_off_pos = (self.n_disp - self.n_disp % 2) * self.spacing / 2
        self.pos = (self.real_pos[0] - self.x_off_pos, self.real_pos[1] - y_off_pos)
        self.coll_rect = pygame.rect.Rect(self.real_pos[0], self.real_pos[1], self.width + (mid_off - self.x_off_pos),
                                          self.n_disp * self.spacing)
        # print self.x_off_pos, mid_off, self.width

    def pre_draw(self, app):
        if self.prev_rect is not None:
            surf.fill(PygCtl.BKGR, self.prev_rect)
            rtn = self.prev_rect
            self.prev_rect = None
            return [rtn]
        return []

    def draw(self, app):
        # Fixes a problem with antialiased alpha blending ListChild instances
        #  Only a Temporary fix
        surf.fill(PygCtl.BKGR, self.coll_rect)
        self.prev_rect = pygame.draw.rect(surf, self.line_color, self.coll_rect, 1)
        return [self.prev_rect]

    def on_evt_global(self, app, evt):
        if evt.type == self.tick_event_id:
            if self.tick == 0:
                return False
            elif self.tick > 0:
                self.tick -= 1
            elif self.tick < 0:
                self.tick += 1
            self.animate()
        return False

    def animate(self):
        start = self.cur_pos - self.n_disp / 2
        start_off = (self.n_disp / 2) * self.spacing + (self.tick * self.spacing / self.max_tick)
        if start < 0:
            start_off += -start * self.spacing
            start = 0
        end = self.cur_pos + (self.n_disp + 1) / 2
        if end > len(self.lst_prn):
            end = len(self.lst_prn)
        for c in range(max(0, start - self.n_disp), start):
            self.lst_prn[c].hide()
        for c in range(start, end):
            self.lst_prn[c].show()
            x_off_pos = self.get_elem_x_off(start_off - self.center)
            self.lst_prn[c].set_pos((self.pos[0] + x_off_pos, start_off + self.pos[1]), c)
            start_off += self.spacing
        for c in range(end, min(len(self.lst_prn), end + self.n_disp)):
            self.lst_prn[c].hide()
        upd_pos()

    def collide_pt(self, pt):
        return self.coll_rect.collidepoint(pt)

    def on_evt(self, app, evt, pos):
        if evt.type == pygame.MOUSEBUTTONDOWN:
            if evt.button == 5:
                self.scroll_down()
            elif evt.button == 4:  # Wheel rolled up
                self.scroll_up()
        return False

    def scroll_down(self):
        if self.cur_pos < len(self.lst_prn) - 1:
            self.cur_pos += 1
            self.tick = self.max_tick
            self.animate()

    def scroll_up(self):
        if self.cur_pos > 0:
            self.cur_pos -= 1
            self.tick = -self.max_tick
            self.animate()


class HyperScroll(ScrollBase):
    def __init__(self, lst_prn, n_disp, pos, spacing, hyperbola_a=50, hyperbola_b=60):
        self.hyperbola_a = hyperbola_a
        self.hyperbola_b = hyperbola_b
        super(HyperScroll, self).__init__(lst_prn, n_disp, pos, spacing)

    def get_elem_x_off(self, y_off_center):  # y = y_off_center
        return -self.hyperbola_a * (((y_off_center ** 2.0) / (self.hyperbola_b ** 2.0) + 1) ** .5)


class ClkLstElem(ListChild):
    def __init__(self, lbl, fnt, color=(PygCtl.WHITE, PygCtl.RED)):
        super(ClkLstElem, self).__init__(0)
        self.fnt = fnt
        self.lbl = lbl
        self.color = color
        self.img = self.get_img() if cache_imgs else None
        self.set_lbl(lbl, color)

    def set_lbl(self, lbl=None, color=None):
        global cache_imgs
        if color is not None:
            self.color = color
        if lbl is not None:
            self.lbl = lbl
        if cache_imgs:
            self.img = self.get_img()
        if self in PygCtl.ctls:
            PygCtl.set_redraw(self)

    def click(self, evt):
        return False

    def get_img(self):
        if self.color[1] is None:
            return self.fnt.render(self.lbl, False, self.color[0])
        return self.fnt.render(self.lbl, False, self.color[0], self.color[1])

    def get_size(self):
        global cache_imgs
        if cache_imgs:
            return super(ClkLstElem, self).get_size()
        else:
            return self.fnt.size(self.lbl)


class LblElem(ClkLstElem):
    def __init__(self, lbl, fnt, color=(PygCtl.WHITE, PygCtl.RED)):
        super(LblElem, self).__init__(lbl, fnt, color)
        self.selected = False
        self.queued = False

    def click(self, evt):
        if evt.button == 1:
            self.selected = not self.selected
        elif evt.button == 3:
            self.queued = not self.queued
        else:
            return False
        self.color = (PygCtl.WHITE, PygCtl.RED)
        if self.queued:
            self.color = (PygCtl.WHITE, (0, 0, 255))
        if self.selected:
            self.color = (PygCtl.WHITE, PygCtl.GREEN)
        self.set_lbl()


SymCh = "!@#$%^&*()[]{}:;<>,./?~`-+=\\|"


def get_pos_in_kern(fnt, Txt0, pos):
    cur_w = fnt.size(Txt0[:pos + 1])[0]
    ch_w = fnt.size(Txt0[pos:pos + 1])[0]
    return cur_w - ch_w


# Translated from C++ from TemplateUtils.h in KyleUtils
def binary_approx(List, Val):
    length = len(List)
    CurLen = length
    pos = length >> 1
    while CurLen > 0:
        if Val <= List[pos] and (pos == 0 or Val >= List[pos - 1]):
            return pos
        elif Val < List[pos]:
            CurLen >>= 1
            pos -= (CurLen + 1) >> 1
        else:
            CurLen = (CurLen - 1) >> 1
            pos += (CurLen >> 1) + 1
    return length


class FuncListView(object):
    def __init__(self, Func, length):
        self.Cache = [None] * length
        self.Func = Func

    def __len__(self):
        return len(self.Cache)

    def __getitem__(self, index):
        if self.Cache[index] is None:
            self.Cache[index] = self.Func(index)
        return self.Cache[index]


clipboard_types = ["text/plain;charset=utf-8", "UTF8_STRING", pygame.SCRAP_TEXT]
"""
EntryLine(fnt, pos, size, colors, pre_chg, post_chg, enter, default_text, censor)
    fnt: type FROM pygame.font: Font, SysFont
        Effect: Style of the text that the user types in the EntryLine
    size: indexable, 2 elements
        Example (list): [width, Height]
        Units: pixels
        Effect: size of the collision box of the EntryLine
    colors: type iterable, 1 or 2 3-tuples
        Effect:
            colors[0] is the color of the text
            colors[1] if 2 elements, is the background color
                else, background color is transparent
        Units: 3-tuples of (R, G, B) each is 0-255
    pre_chg: OPTIONAL, type (callable)(Inst, evt) -> bool(AllowEdit)
        Effect:
            called after an event is processed but before the text is changed,
            returning False will result in the edit not going through
            returning True will result in the edit going through
            NOTE: do not change the text in this function, do that in post_chg
    post_chg: OPTIONAL, type (callable)(Inst, evt)
        Effect:
            called after text is changed
            NOTE: you can change the text in this function
    enter: OPTIONAL, type (callable)(Inst)
        Effect:
            called after the return/enter key is pressed
    default_text: OPTIONAL, type iterable of characters ie: str, list (of len 1 str)
        Effect:
            Text that is already in the EntryLine box,
            This text is treated the same way as text entered by the user
                It does not disappear when the user types/clicks in the box
    censor: OPTIONAL, type (callable)(txt) -> (str/unicode)(CensoredTxt)
        Effect:
            called during drawing to get the text that will be displayed
            called for mouse clicks and moves to get the text for
                selection region and cursor positioning calculation
            NOTE: does not change the actual text in the box
Attributes for EntryLine:
    HiLtCol: type iterable, 1 or 2 3-tuples
        Effect: For highlighted text
            colors[0] is the color of the text
            colors[1] if 2 elements, is the background color
                else, background color is transparent
"""


class EntryLine(PygCtl.PygCtl):
    cursor_timer_event_id = pygame.USEREVENT + 1
    # cursor Threshhold, the fraction of character width
    #  that represents border between 2 char positions
    cursor_thresh = .3

    @staticmethod
    def next_word(lst_txt, txt_pos):
        cur_type = -1
        for c in range(txt_pos, len(lst_txt)):
            ch = lst_txt[c]
            if ch.isalnum() or ch == '_':
                if cur_type == -1:
                    cur_type = 0
                elif cur_type != 0:
                    return c
            elif ch in SymCh:
                if cur_type == -1:
                    cur_type = 1
                elif cur_type != 1:
                    return c
            elif ch.isspace():
                if cur_type != -1:
                    return c
            else:
                if cur_type == -1:
                    cur_type = 2
                elif cur_type != 2:
                    return c
        return len(lst_txt)

    @staticmethod
    def prev_word(lst_txt, txt_pos):
        cur_type = -1
        for c in range(txt_pos, 0, -1):
            ch = lst_txt[c - 1]
            if ch.isalnum() or ch == '_':
                if cur_type == -1:
                    cur_type = 0
                elif cur_type != 0:
                    return c
            elif ch in SymCh:
                if cur_type == -1:
                    cur_type = 1
                elif cur_type != 1:
                    return c
            elif ch.isspace():
                if cur_type != -1:
                    return c
            else:
                if cur_type == -1:
                    cur_type = 2
                elif cur_type != 2:
                    return c
        return 0

    @classmethod
    def init_timer(cls, evt_code=None):
        if evt_code is not None:
            cls.cursor_timer_event_id = evt_code
        pygame.time.set_timer(cls.cursor_timer_event_id, 500)
        cls.clipboard = PyperClipboard()

    def __init__(self, fnt, pos, size, colors, pre_chg=None, post_chg=None, enter=None, default_text="", censor=None):
        self.colors = colors
        self.highlight_colors = [(255, 255, 255), (0, 0, 255)]
        self.pos = pos
        self.size = size
        self.pre_chg = pre_chg
        self.post_chg = post_chg
        self.enter = enter
        self.censor = censor
        self.is_selected = False
        self.highlight = False
        self.highlight_pos = 0
        self.txt = list(default_text)
        self.ch_pos = 0
        self.ch_off = 0  # x offset in pixels
        self.cur_key = None
        self.coll_rect = pygame.rect.Rect(self.pos, self.size)
        self.prev_rect = self.coll_rect
        self.fnt = fnt
        self.old_cursor = None
        self.cursor_state = True

    def on_evt(self, app, evt, pos):
        if evt.type == pygame.MOUSEBUTTONDOWN:
            draw_txt = u"".join(self.txt)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            self.highlight = True
            self.is_selected = True
            pos = (pos[0] - self.pos[0], pos[1] - self.pos[1])
            cursor_thresh = EntryLine.cursor_thresh
            get_size_text = lambda x: \
                self.fnt.size(draw_txt[:x])[0]
            lst_v = FuncListView(get_size_text, len(draw_txt))
            # since lst_v[0] == 0 and pos[0] >= 0 is True, result->ch_pos >= 1
            ch_pos = binary_approx(lst_v, pos[0])
            if ch_pos < len(lst_v):
                off_x = lst_v[ch_pos - 1]
                ch_w = lst_v[ch_pos] - off_x
                if pos[0] - off_x <= cursor_thresh * ch_w:
                    ch_pos -= 1
            self.ch_pos = ch_pos
            self.highlight_pos = ch_pos
            return True
        return False

    def on_mouse_enter(self):
        if pygame.mouse.get_cursor() != self.cursor:
            self.old_cursor = pygame.mouse.get_cursor()
            pygame.mouse.set_cursor(*self.cursor)
        return super(EntryLine, self).on_mouse_enter()

    def on_mouse_exit(self):
        if self.old_cursor is not None:
            pygame.mouse.set_cursor(*self.old_cursor)
            self.old_cursor = None
        return super(EntryLine, self).on_mouse_exit()

    def on_pre_chg(self, evt):
        return self.pre_chg is None or self.pre_chg(self, evt)

    def on_evt_global(self, app, evt):
        if evt.type == pygame.MOUSEBUTTONDOWN:
            if self.coll_rect.collidepoint(evt.pos):
                return False
            if self.highlight or self.is_selected:
                self.highlight = False
                self.is_selected = False
        elif evt.type == pygame.MOUSEBUTTONUP:
            if self.highlight:
                self.highlight = False
        elif evt.type == pygame.MOUSEMOTION and self.highlight:
            draw_txt = u"".join(self.txt)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            pos = evt.pos
            pos = [pos[0] - self.pos[0], pos[1] - self.pos[1]]
            if pos[0] < 0:
                pos[0] = 0
            cursor_thresh = EntryLine.cursor_thresh
            get_size_text = lambda x: \
                self.fnt.size(draw_txt[:x])[0]
            lst_v = FuncListView(get_size_text, len(draw_txt))
            # since lst_v[0] == 0 and pos[0] >= 0 is True, result->ch_pos >= 1
            ch_pos = binary_approx(lst_v, pos[0])
            if ch_pos < len(lst_v):
                off_x = lst_v[ch_pos - 1]
                ch_w = lst_v[ch_pos] - off_x
                if pos[0] - off_x <= cursor_thresh * ch_w:
                    ch_pos -= 1
            self.ch_pos = ch_pos
            return True
        elif evt.type == pygame.KEYDOWN and self.is_selected:
            is_chg = False
            if evt.key == pygame.K_BACKSPACE:
                if not ((self.ch_pos > 0 or self.ch_pos != self.highlight_pos) and self.on_pre_chg(evt)):
                    return False
                elif evt.mod & pygame.KMOD_CTRL > 0:
                    start = EntryLine.prev_word(self.txt, self.ch_pos)
                    self.txt[start:self.ch_pos] = []
                    off = self.ch_pos - start
                    DoOff = 0  # Default make highlight_pos = ch_pos
                    if self.highlight_pos > self.ch_pos:
                        DoOff = 1  # Offset highlight_pos same amount as ch_pos
                    elif self.highlight_pos < self.ch_pos - start:
                        DoOff = 2  # Leave highlight_pos Alone
                    self.ch_pos = start
                    if DoOff == 1:
                        self.highlight_pos -= off
                    elif DoOff == 0:
                        self.highlight_pos = self.ch_pos
                    is_chg = True
                else:
                    if self.ch_pos != self.highlight_pos:
                        start, end = sorted((self.ch_pos, self.highlight_pos))
                        self.txt[start:end] = []
                        self.ch_pos = start
                    else:
                        self.ch_pos -= 1
                        self.txt.pop(self.ch_pos)
                    is_chg = True
                    self.highlight_pos = self.ch_pos
            elif evt.key == pygame.K_DELETE:
                if not ((self.ch_pos < len(self.txt) or self.ch_pos != self.highlight_pos) and self.on_pre_chg(evt)):
                    return False
                elif evt.mod & pygame.KMOD_CTRL > 0:
                    end = EntryLine.next_word(self.txt, self.ch_pos)
                    self.txt[self.ch_pos:end] = []
                    off = end - self.ch_pos
                    if self.highlight_pos > self.ch_pos:
                        self.highlight_pos -= off
                    is_chg = True
                else:
                    if self.ch_pos != self.highlight_pos:
                        start, end = sorted((self.ch_pos, self.highlight_pos))
                        self.txt[start:end] = []
                        self.ch_pos = start
                        self.highlight_pos = start
                    else:
                        self.txt.pop(self.ch_pos)
                    is_chg = True
                    self.highlight_pos = self.ch_pos
            elif evt.key == pygame.K_HOME:
                self.ch_pos = 0
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = self.ch_pos
            elif evt.key == pygame.K_END:
                self.ch_pos = len(self.txt)
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = self.ch_pos
            elif evt.key == pygame.K_RETURN:
                if self.enter is not None:
                    self.enter(self)
            elif evt.key == pygame.K_LEFT:
                if evt.mod & pygame.KMOD_CTRL > 0:
                    self.ch_pos = EntryLine.prev_word(self.txt, self.ch_pos)
                elif self.ch_pos > 0:
                    if evt.mod & pygame.KMOD_SHIFT == 0 and self.ch_pos != self.highlight_pos:
                        start, end = sorted((self.ch_pos, self.highlight_pos))
                        self.ch_pos = start
                    else:
                        self.ch_pos -= 1
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = self.ch_pos
            elif evt.key == pygame.K_RIGHT:
                if evt.mod & pygame.KMOD_CTRL > 0:
                    self.ch_pos = EntryLine.next_word(self.txt, self.ch_pos)
                elif self.ch_pos < len(self.txt):
                    if evt.mod & pygame.KMOD_SHIFT == 0 and self.ch_pos != self.highlight_pos:
                        start, end = sorted((self.ch_pos, self.highlight_pos))
                        self.ch_pos = end
                    else:
                        self.ch_pos += 1
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = self.ch_pos
            elif evt.mod & pygame.KMOD_CTRL > 0:
                start, end = sorted((self.ch_pos, self.highlight_pos))
                if evt.key == pygame.K_v:
                    data = None
                    for Item in clipboard_types:
                        data = self.clipboard.get(Item)
                        if data is not None:
                            break
                    if data is None or not self.on_pre_chg(evt):
                        return False
                    self.txt[start:end] = data
                    self.ch_pos = start + len(data)
                    self.highlight_pos = self.ch_pos
                    is_chg = True
                elif evt.key == pygame.K_c:
                    self.clipboard.put(pygame.SCRAP_TEXT, u"".join(self.txt[start:end]))
                elif evt.key == pygame.K_x:
                    if start == end or not self.on_pre_chg(evt):
                        return False
                    self.clipboard.put(pygame.SCRAP_TEXT, u"".join(self.txt[start:end]))
                    self.txt[start:end] = []
                    self.ch_pos = start
                    self.highlight_pos = start
                    is_chg = True
            elif len(evt.unicode) > 0:
                if not self.on_pre_chg(evt):
                    return False
                start, end = sorted((self.ch_pos, self.highlight_pos))
                self.txt[start:end] = evt.unicode
                self.ch_pos = start + 1
                self.highlight_pos = self.ch_pos
                is_chg = True
            if is_chg and self.post_chg is not None:
                self.post_chg(self, evt)
            return True
        elif evt.type == EntryLine.cursor_timer_event_id:
            if self.is_selected:
                self.cursor_state = not self.cursor_state
                return True
        return False

    def draw(self, app):
        draw_txt = u"".join(self.txt)
        if self.censor is not None:
            draw_txt = self.censor(draw_txt)
        img = None
        if self.ch_pos != self.highlight_pos:
            start, end = sorted((self.ch_pos, self.highlight_pos))
            begin_w = get_pos_in_kern(self.fnt, draw_txt, start)
            end_w = get_pos_in_kern(self.fnt, draw_txt, end)
            img = pygame.Surface(self.fnt.size(draw_txt), pygame.SRCALPHA)
            img.blit(self.fnt.render(draw_txt[:start], True, self.colors[0]), (0, 0))
            img.blit(self.fnt.render(draw_txt[start:end], True, *self.highlight_colors), (begin_w, 0))
            img.blit(self.fnt.render(draw_txt[end:], True, self.colors[0]), (end_w, 0))
        else:
            img = self.fnt.render(draw_txt, True, self.colors[0])
        rtn = []
        if len(self.colors) > 1:
            rtn.append(surf.fill(self.colors[1], self.coll_rect))
        rtn.append(surf.blit(img, self.pos))
        if self.cursor_state:
            cursor_x = self.fnt.size(draw_txt[:self.ch_pos])[0] + self.pos[0] - 1
            rtn.append(surf.fill(self.colors[0], pygame.Rect(cursor_x, self.pos[1], 2, img.get_height())))
        self.prev_rect = rtn[-1].unionall(rtn[:-1])
        return rtn

    """def draw(self, app):
        draw_txt = u"".join(self.txt)
        img = self.fnt.render(draw_txt, True, self.colors[0])
        rtn = []
        if len(self.colors) > 1:
        rtn.append(surf.fill(self.colors[1], self.coll_rect))
        rtn.append(surf.blit(img, self.pos))
        if self.cursor_state:
            cursor_x = self.fnt.size(draw_txt[:self.ch_pos])[0] + self.pos[0] - 1
            rtn.append(surf.fill(self.colors[0], pygame.Rect(cursor_x, self.pos[1], 2, img.get_height())))
        self.prev_rect = rtn[-1].unionall(rtn[:-1])
        return rtn"""

    def pre_draw(self, app):
        if self.prev_rect is not None:
            rtn = surf.fill(PygCtl.BKGR, self.prev_rect)
            self.prev_rect = None
            return [rtn]
        return []

    def collide_pt(self, pt):
        return self.coll_rect.collidepoint(pt)


class EntryBox(PygCtl.PygCtl):
    cursor_timer_event_id = pygame.USEREVENT + 1
    # cursor Threshhold, the fraction of character width, height
    #  that represents border between 2 char positions
    cursor_thresh = (.5, 0.0)
    cursor = ((16, 24), (8, 12)) + pygame.cursors.compile((
        "                ",
        "                ",
        "                ",
        "   XXXX XXXX    ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "       X        ",
        "   XXXX XXXX    ",
        "                ",
        "                ",
        "                "),
        black='.', white='O', xor='X')

    @staticmethod
    def next_word(lst_txt, txt_pos):
        cur_type = -1
        for c in range(txt_pos, len(lst_txt)):
            ch = lst_txt[c]
            if ch.isalnum() or ch == '_':
                if cur_type == -1:
                    cur_type = 0
                elif cur_type != 0:
                    return c
            elif ch in SymCh:
                if cur_type == -1:
                    cur_type = 1
                elif cur_type != 1:
                    return c
            elif ch.isspace():
                if cur_type != -1:
                    return c
            else:
                if cur_type == -1:
                    cur_type = 2
                elif cur_type != 2:
                    return c
        return len(lst_txt)

    @staticmethod
    def prev_word(lst_txt, txt_pos):
        cur_type = -1
        for c in range(txt_pos, 0, -1):
            ch = lst_txt[c - 1]
            if ch.isalnum() or ch == '_':
                if cur_type == -1:
                    cur_type = 0
                elif cur_type != 0:
                    return c
            elif ch in SymCh:
                if cur_type == -1:
                    cur_type = 1
                elif cur_type != 1:
                    return c
            elif ch.isspace():
                if cur_type != -1:
                    return c
            else:
                if cur_type == -1:
                    cur_type = 2
                elif cur_type != 2:
                    return c
        return 0

    @classmethod
    def init_timer(cls, evt_code=None):
        if evt_code is not None:
            cls.cursor_timer_event_id = evt_code
        pygame.time.set_timer(cls.cursor_timer_event_id, 500)
        cls.clipboard = PyperClipboard()  # PygClipboard()

    def __init__(self, fnt, pos, size, colors, pre_chg=None, post_chg=None, enter=None, default_text="", censor=None):
        self.line_sep = "\n"
        self.colors = colors
        self.highlight_colors = [(255, 255, 255), (51, 143, 255)]
        self.pos = pos
        self.size = size
        self.pre_chg = pre_chg
        self.post_chg = post_chg
        self.enter = enter
        self.censor = censor
        self.is_selected = False
        self.highlight = False
        self.highlight_pos = [0, 0]
        self.txt = TextLineView(default_text, self.line_sep)
        self.ch_pos = [0, 0]
        self.ch_off = 0  # x offset in pixels
        self.cur_key = None
        self.coll_rect = pygame.rect.Rect(self.pos, self.size)
        self.prev_rect = self.coll_rect
        self.fnt = fnt
        self.cursor_state = True
        self.cursor_col = None
        self.line_h = fnt.get_linesize()
        self.old_cursor = None

    def set_size(self, size):
        self.size = size
        self.coll_rect = pygame.rect.Rect(self.pos, self.size)

    def set_pos(self, pos):
        self.pos = pos
        self.coll_rect = pygame.rect.Rect(self.pos, self.size)

    def set_pos_size(self, pos, size):
        self.pos = pos
        self.size = size
        self.coll_rect = pygame.rect.Rect(self.pos, self.size)

    def on_evt(self, app, evt, pos):
        if evt.type == pygame.MOUSEBUTTONDOWN:
            self.highlight = True
            self.is_selected = True
            pos = [pos[0] - self.pos[0], pos[1] - self.pos[1]]
            if pos[0] < 0:
                pos[0] = 0
            if pos[1] < 0:
                pos[1] = 0
            cursor_thresh_x, cursor_thresh_y = EntryBox.cursor_thresh
            ch_row = max(0, min(int(pos[1] / self.line_h + cursor_thresh_y), len(self.txt.Lines) - 1))
            draw_txt = self.txt.get_draw_row(ch_row)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            get_size_text = lambda x: \
                self.fnt.size(draw_txt[:x])[0]
            lst_v = FuncListView(get_size_text, len(draw_txt))
            # since lst_v[0] == 0 and pos[0] >= 0 is True, result->ch_pos >= 1
            ch_col = binary_approx(lst_v, pos[0])
            if ch_col < len(lst_v):
                off_x = lst_v[ch_col - 1]
                ch_w = lst_v[ch_col] - off_x
                if pos[0] - off_x <= cursor_thresh_x * ch_w:
                    ch_col -= 1
            self.ch_pos = [ch_col, ch_row]
            self.highlight_pos = [ch_col, ch_row]
            return True
        return False

    def on_pre_chg(self, evt):
        return self.pre_chg is None or self.pre_chg(self, evt)

    def on_mouse_enter(self):
        if pygame.mouse.get_cursor() != self.cursor:
            self.old_cursor = pygame.mouse.get_cursor()
            pygame.mouse.set_cursor(*self.cursor)
        return super(EntryBox, self).on_mouse_enter()

    def on_mouse_exit(self):
        if self.old_cursor is not None:
            pygame.mouse.set_cursor(*self.old_cursor)
            self.old_cursor = None
        return super(EntryBox, self).on_mouse_exit()

    def on_evt_global(self, app, evt):
        if evt.type == pygame.MOUSEBUTTONDOWN:
            if self.coll_rect.collidepoint(evt.pos):
                return False
            if self.highlight or self.is_selected:
                self.highlight = False
                self.is_selected = False
        elif evt.type == pygame.MOUSEBUTTONUP:
            if self.highlight:
                self.highlight = False
        elif evt.type == pygame.MOUSEMOTION and self.highlight:
            pos = evt.pos
            pos = [pos[0] - self.pos[0], pos[1] - self.pos[1]]
            if pos[0] < 0:
                pos[0] = 0
            if pos[1] < 0:
                pos[1] = 0
            cursor_thresh_x, cursor_thresh_y = EntryBox.cursor_thresh
            ch_row = max(0, min(int(pos[1] / self.line_h + cursor_thresh_y), len(self.txt.Lines) - 1))
            draw_txt = self.txt.get_draw_row(ch_row)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            get_size_text = lambda x: \
                self.fnt.size(draw_txt[:x])[0]
            lst_v = FuncListView(get_size_text, len(draw_txt))
            # since lst_v[0] == 0 and pos[0] >= 0 is True, result->ch_pos >= 1
            ch_col = binary_approx(lst_v, pos[0])
            if ch_col < len(lst_v):
                off_x = lst_v[ch_col - 1]
                ch_w = lst_v[ch_col] - off_x
                if pos[0] - off_x <= cursor_thresh_x * ch_w:
                    ch_col -= 1
            self.ch_pos = [ch_col, ch_row]
            return True
        elif evt.type == pygame.KEYDOWN and self.is_selected:
            is_chg = False
            ch_pos = self.txt.row_col_to_pos(*self.ch_pos)
            col_chg = True
            if evt.key == pygame.K_BACKSPACE:
                if ch_pos == 0 and self.ch_pos == self.highlight_pos or not self.on_pre_chg(evt):
                    return False
                elif evt.mod & pygame.KMOD_CTRL > 0:
                    start = EntryLine.prev_word(self.txt.Str, ch_pos)
                    off = ch_pos - start
                    highlight_pos = self.txt.row_col_to_pos(*self.highlight_pos)
                    self.txt.Delete(start, ch_pos)
                    if highlight_pos >= ch_pos:
                        highlight_pos -= off
                    elif highlight_pos > ch_pos - off:
                        highlight_pos = ch_pos
                    ch_pos = start
                    self.ch_pos = self.txt.pos_to_row_col(ch_pos)
                    self.highlight_pos = self.txt.pos_to_row_col(highlight_pos)
                    is_chg = True
                else:
                    if self.ch_pos != self.highlight_pos:
                        start, end = sorted((ch_pos, self.txt.row_col_to_pos(*self.highlight_pos)))
                        self.txt.Delete(start, end)
                        self.ch_pos = self.txt.pos_to_row_col(start)
                        is_chg = True
                    else:
                        if ch_pos > 0:
                            self.txt.Delete(ch_pos - 1, ch_pos)
                            self.ch_pos = self.txt.pos_to_row_col(ch_pos - 1)
                            is_chg = True
                    self.highlight_pos = list(self.ch_pos)
            elif evt.key == pygame.K_DELETE:
                if (ch_pos >= len(self.txt.Str) and self.ch_pos == self.highlight_pos) or not self.on_pre_chg(evt):
                    return False
                elif evt.mod & pygame.KMOD_CTRL > 0:
                    end = EntryLine.next_word(self.txt.Str, ch_pos)
                    off = end - ch_pos
                    highlight_pos = self.txt.row_col_to_pos(*self.highlight_pos)
                    self.txt.Delete(ch_pos, end)
                    if highlight_pos > ch_pos:
                        self.highlight_pos = self.txt.pos_to_row_col(max(highlight_pos - off, ch_pos))
                    is_chg = True
                else:
                    if self.ch_pos != self.highlight_pos:
                        start, end = sorted((ch_pos, self.txt.row_col_to_pos(*self.highlight_pos)))
                        self.txt.Delete(start, end)
                        self.ch_pos = self.txt.pos_to_row_col(start)
                        is_chg = True
                    else:
                        if ch_pos < len(self.txt.Str):
                            self.txt.Delete(ch_pos, ch_pos + 1)
                            is_chg = True
                    self.highlight_pos = list(self.ch_pos)
            elif evt.key == pygame.K_HOME:
                if evt.mod & pygame.KMOD_CTRL > 0:
                    self.ch_pos[1] = 0
                self.ch_pos[0] = 0
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = list(self.ch_pos)
            elif evt.key == pygame.K_END:
                if evt.mod & pygame.KMOD_CTRL > 0:
                    self.ch_pos[1] = len(self.txt.Lines) - 1
                self.ch_pos[0] = self.txt.get_draw_row_len(self.ch_pos[1])
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = list(self.ch_pos)
            elif evt.key == pygame.K_RETURN:
                # if self.enter is not None:
                # self.enter(self)
                self.txt.replace(self.line_sep, *sorted([ch_pos, self.txt.t_row_col_to_pos(self.highlight_pos)]))
                self.ch_pos[0] = 0
                self.ch_pos[1] += 1
                is_chg = True
                self.highlight_pos = list(self.ch_pos)
            elif evt.key == pygame.K_LEFT:
                if evt.mod & pygame.KMOD_CTRL > 0:
                    self.ch_pos = self.txt.pos_to_row_col(EntryLine.prev_word(self.txt.Str, ch_pos))
                elif ch_pos > 0:
                    if evt.mod & pygame.KMOD_SHIFT == 0 and self.ch_pos != self.highlight_pos:
                        start, end = sorted((ch_pos, self.txt.row_col_to_pos(*self.highlight_pos)))
                        self.ch_pos = self.txt.pos_to_row_col(start)
                    else:
                        self.ch_pos = self.txt.pos_to_row_col(ch_pos - 1)
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = list(self.ch_pos)
            elif evt.key == pygame.K_RIGHT:
                if evt.mod & pygame.KMOD_CTRL > 0:
                    self.ch_pos = self.txt.pos_to_row_col(EntryLine.next_word(self.txt.Str, ch_pos))
                elif ch_pos < len(self.txt.Str):
                    if evt.mod & pygame.KMOD_SHIFT == 0 and self.ch_pos != self.highlight_pos:
                        start, end = sorted((ch_pos, self.txt.row_col_to_pos(*self.highlight_pos)))
                        self.ch_pos = self.txt.pos_to_row_col(end)
                    else:
                        self.ch_pos = self.txt.pos_to_row_col(ch_pos + 1)
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = list(self.ch_pos)
            elif evt.key == pygame.K_UP:
                if self.ch_pos[1] > 0:
                    self.ch_pos[1] -= 1
                if self.cursor_col is not None:
                    self.ch_pos[0] = self.cursor_col
                else:
                    self.cursor_col = self.ch_pos[0]
                if self.ch_pos[0] > self.txt.get_draw_row_len(self.ch_pos[1]):
                    self.ch_pos[0] = self.txt.get_draw_row_len(self.ch_pos[1])
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = list(self.ch_pos)
                col_chg = False
            elif evt.key == pygame.K_DOWN:
                if self.ch_pos[1] + 1 < len(self.txt.Lines):
                    self.ch_pos[1] += 1
                if self.cursor_col is not None:
                    self.ch_pos[0] = self.cursor_col
                else:
                    self.cursor_col = self.ch_pos[0]
                if self.ch_pos[0] > self.txt.get_draw_row_len(self.ch_pos[1]):
                    self.ch_pos[0] = self.txt.get_draw_row_len(self.ch_pos[1])
                if evt.mod & pygame.KMOD_SHIFT == 0:
                    self.highlight_pos = list(self.ch_pos)
                col_chg = False
            elif evt.mod & pygame.KMOD_CTRL > 0:
                start, end = sorted((ch_pos, self.txt.row_col_to_pos(*self.highlight_pos)))
                if evt.key == pygame.K_v:
                    data = None
                    for Item in clipboard_types:
                        data = self.clipboard.get(Item)
                        if data is not None:
                            break
                    if data is None or not self.on_pre_chg(evt):
                        return False
                    self.txt.replace(data, start, end)
                    self.ch_pos = self.txt.pos_to_row_col(start + len(data))
                    self.highlight_pos = list(self.ch_pos)
                    is_chg = True
                elif evt.key == pygame.K_c:
                    self.clipboard.put(pygame.SCRAP_TEXT, self.txt.GetStr(start, end))
                elif evt.key == pygame.K_x:
                    if start == end or not self.on_pre_chg(evt):
                        return False
                    self.clipboard.put(pygame.SCRAP_TEXT, self.txt.GetStr(start, end))
                    self.txt.Delete(start, end)
                    self.ch_pos = self.txt.pos_to_row_col(start)
                    self.highlight_pos = self.txt.pos_to_row_col(start)
                    is_chg = True
            elif len(evt.unicode) > 0:
                if not self.on_pre_chg(evt):
                    return False
                start, end = sorted((ch_pos, self.txt.row_col_to_pos(*self.highlight_pos)))
                self.txt.replace(evt.unicode, start, end)
                self.ch_pos = self.txt.pos_to_row_col(start + 1)
                self.highlight_pos = list(self.ch_pos)
                is_chg = True
            if col_chg:
                self.cursor_col = None
            if is_chg and self.post_chg is not None:
                self.post_chg(self, evt)
            return True
        elif evt.type == EntryBox.cursor_timer_event_id:
            if self.is_selected:
                self.cursor_state = not self.cursor_state
                return True
        return False

    def draw(self, app):
        start, end = map(self.txt.pos_to_row_col,
                         sorted(map(self.txt.t_row_col_to_pos, [self.ch_pos, self.highlight_pos])))
        rtn = [None] * len(self.txt.Lines)
        if len(self.colors) > 1:
            rtn.append(surf.fill(self.colors[1], self.coll_rect))
        for c in range(0, start[1]):
            draw_txt = self.txt.get_draw_row(c)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            img = self.fnt.render(draw_txt, True, self.colors[0])
            rtn[c] = surf.blit(img, (self.pos[0], self.pos[1] + self.line_h * c))
        if start == end:
            c = start[1]
            draw_txt = self.txt.get_draw_row(c)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            img = self.fnt.render(draw_txt, True, self.colors[0])
            rtn[c] = surf.blit(img, (self.pos[0], self.pos[1] + self.line_h * c))
        elif start[1] == end[1]:
            c = start[1]
            draw_txt = self.txt.get_draw_row(c)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            begin_w = get_pos_in_kern(self.fnt, draw_txt, start[0])
            end_w = get_pos_in_kern(self.fnt, draw_txt, end[0])
            img = pygame.Surface(self.fnt.size(draw_txt), pygame.SRCALPHA)
            img.blit(self.fnt.render(draw_txt[:start[0]], True, self.colors[0]), (0, 0))
            img.blit(self.fnt.render(draw_txt[start[0]:end[0]], True, *self.highlight_colors), (begin_w, 0))
            img.blit(self.fnt.render(draw_txt[end[0]:], True, self.colors[0]), (end_w, 0))
            rtn[c] = surf.blit(img, (self.pos[0], self.pos[1] + self.line_h * c))
        else:
            c = start[1]
            draw_txt = self.txt.get_draw_row(c)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            begin_w = get_pos_in_kern(self.fnt, draw_txt, start[0])
            img = pygame.Surface(self.fnt.size(draw_txt), pygame.SRCALPHA)
            img.blit(self.fnt.render(draw_txt[:start[0]], True, self.colors[0]), (0, 0))
            img.blit(self.fnt.render(draw_txt[start[0]:], True, *self.highlight_colors), (begin_w, 0))
            rtn[c] = surf.blit(img, (self.pos[0], self.pos[1] + self.line_h * c))
            c = end[1]
            draw_txt = self.txt.get_draw_row(c)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            end_w = get_pos_in_kern(self.fnt, draw_txt, end[0])
            img = pygame.Surface(self.fnt.size(draw_txt), pygame.SRCALPHA)
            img.blit(self.fnt.render(draw_txt[:end[0]], True, *self.highlight_colors), (0, 0))
            img.blit(self.fnt.render(draw_txt[end[0]:], True, self.colors[0]), (end_w, 0))
            rtn[c] = surf.blit(img, (self.pos[0], self.pos[1] + self.line_h * c))
        for c in range(start[1] + 1, end[1]):
            draw_txt = self.txt.get_draw_row(c)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            img = self.fnt.render(draw_txt, True, *self.highlight_colors)
            rtn[c] = surf.blit(img, (self.pos[0], self.pos[1] + self.line_h * c))
        for c in range(end[1] + 1, len(self.txt.Lines)):
            draw_txt = self.txt.get_draw_row(c)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            img = self.fnt.render(draw_txt, True, self.colors[0])
            rtn[c] = surf.blit(img, (self.pos[0], self.pos[1] + self.line_h * c))
        if self.cursor_state:
            c = self.ch_pos[1]
            draw_txt = self.txt.get_draw_row(c)
            if self.censor is not None:
                draw_txt = self.censor(draw_txt)
            CursPos = (
                self.fnt.size(draw_txt[:self.ch_pos[0]])[0] + self.pos[0] - 1,
                self.pos[1] + self.line_h * self.ch_pos[1])
            rtn.append(surf.fill(self.colors[0], pygame.Rect(CursPos, (2, self.line_h))))
        self.prev_rect = rtn[-1].unionall(rtn[:-1])
        return [self.prev_rect]

    """def draw(self, app):
        draw_txt = u"".join(self.txt)
        img = self.fnt.render(draw_txt, True, self.colors[0])
        rtn = []
        if len(self.colors) > 1:
        rtn.append(surf.fill(self.colors[1], self.coll_rect))
        rtn.append(surf.blit(img, self.pos))
        if self.cursor_state:
            cursor_x = self.fnt.size(draw_txt[:self.ch_pos])[0] + self.pos[0] - 1
            rtn.append(surf.fill(self.colors[0], pygame.Rect(cursor_x, self.pos[1], 2, img.get_height())))
        self.prev_rect = rtn[-1].unionall(rtn[:-1])
        return rtn"""

    def pre_draw(self, app):
        if self.prev_rect is not None:
            rtn = surf.fill(PygCtl.BKGR, self.prev_rect)
            self.prev_rect = None
            return [rtn]
        return []

    def collide_pt(self, pt):
        return self.coll_rect.collidepoint(pt)


class Drawable(object):
    def draw(self, surf, pos):
        return []

    def get_size(self):
        return 0, 0

    def rotate(self, is_clk_wise):
        pass


class YGradient(Drawable):
    def __init__(self, size, start_color, end_color):
        self.size = size
        self.grad_dir = True  # False: up, True: down
        self.lst_grad = [0] * self.size[1]
        init_gradient(self.lst_grad, start_color, end_color)
        self.img = pygame.Surface(self.size)
        for y in range(self.size[1]):
            self.img.fill(self.lst_grad[y], pygame.rect.Rect((0, y), (self.size[0], 1)))

    def draw(self, surf, pos):
        return [surf.blit(self.img, pos)]

    def get_size(self):
        return self.img.get_size()

    def rotate(self, is_clk_wise):
        angle = 90
        if is_clk_wise:
            angle = -angle
        self.img = pygame.transform.rotate(self.img, angle)

    def set_grad_dir(self, down=True):
        if self.grad_dir != down:
            if down:
                for y in range(self.size[1]):
                    self.img.fill(self.lst_grad[y], pygame.rect.Rect((0, y), (self.size[0], 1)))
            else:
                for y in range(1, self.size[1] + 1):
                    self.img.fill(self.lst_grad[-y], pygame.rect.Rect((0, y), (self.size[0], 1)))
            self.grad_dir = down


def_grad_btn = {"n-from": (0xF7, 0xF7, 0xF7), "n-to": (0xDC, 0xDC, 0xDC),
                "border": (1, (0x99, 0x99, 0x99), (0x77, 0x77, 0x77)), "txt-color": (0, 0, 0)}
my_grad_btn = dict(def_grad_btn)
# my_grad_btn["n-from"] = combine(def_grad_btn["n-from"], (0, 0, 255), .23)
# my_grad_btn["n-to"] = combine(def_grad_btn["n-to"], (0, 255, 0), .23)
# my_grad_btn["border"] = def_grad_btn["border"][0:1] + (mul_color(0, 255, 255), 9/15.0), mul_color((0, 255, 255), 7/15.0))
my_grad_btn["border"] = def_grad_btn["border"][0:1] + ((128, 0, 0), (255, 0, 0))


class GradBtn(PygCtl.PressBtn):
    def __init__(self, lbl, act_func, pos, fnt, padding=None, colors=def_grad_btn):
        self.pos = pos
        self.act_func = act_func
        if padding is None:
            padding = (2, 2)
        self.box_size = colors["border"][0]
        self.box_color = colors["border"][1]
        self.box_colors = colors["border"][1:3]
        self.txt_color = colors["txt-color"]
        self.padding = padding
        self.lbl = lbl
        self.fnt = fnt
        self.cur_state = False
        self.tot_rect = None
        self.RecalcRect()
        self.draw_obj = YGradient(self.size, colors["n-from"], colors["n-to"])
        # self.BrdRect = pygame.rect.Rect(self.pos[0] + self.box_size, self.pos[1] + self.box_size, self.size[0] - self.box_size, self.size[1] - self.box_size)
        self.BrdRect = self.tot_rect

    def on_mouse_enter(self):
        if not self.cur_state:
            self.box_color = self.box_colors[1]
        return True

    def on_mouse_exit(self):
        self.box_color = self.box_colors[0]
        return True

    def on_mouse_down(self, evt):
        if evt.button != 1:
            return False
        self.cur_state = True
        self.draw_obj.set_grad_dir(False)
        self.box_color = self.box_colors[0]
        return True

    def on_mouse_up(self, evt):
        if evt.button != 1:
            return False
        if not self.cur_state:
            return False
        self.cur_state = False
        self.box_color = self.box_colors[1]
        self.draw_obj.set_grad_dir(True)
        if self.act_func is not None:
            self.act_func(self, evt.pos)
        return True

    def on_evt_global(self, app, evt):
        if self.cur_state and evt.type == pygame.MOUSEBUTTONUP and evt.button == 1:
            self.cur_state = False
            self.draw_obj.set_grad_dir(True)
            return True
        return False

    def draw(self, app):
        rtn = []
        rtn.extend(self.draw_obj.draw(surf, self.pos))
        rtn.append(pygame.draw.rect(surf, self.box_color, self.BrdRect, self.box_size))
        rtn.append(surf.blit(self.txt_img, (self.pos[0] + self.txt_off[0], self.pos[1] + self.txt_off[1])))
        self.prev_rect = self.tot_rect
        return rtn

    def RecalcRect(self):
        txt_size = self.fnt.size(self.lbl)
        padding = self.padding[0] + self.box_size + 1, self.padding[1] + self.box_size + 1
        size = txt_size[0] + padding[0] * 2, txt_size[1] + padding[1] * 2
        self.txt_off = (size[0] - txt_size[0]) / 2, (size[1] - txt_size[1]) / 2
        self.size = size
        self.txt_img = self.fnt.render(self.lbl, 1, self.txt_color)
        self.prev_rect = self.tot_rect
        self.tot_rect = pygame.rect.Rect(self.pos, self.size)


def Main():
    PygCtl.Init()
    my_fnt = pygame.font.SysFont("Courier New", 20)
    MyLst = [
        LblElem("hello", my_fnt),
        LblElem("Not Really", my_fnt),
        LblElem("Of Course", my_fnt),
        LblElem("But Maybe", my_fnt),
        LblElem("Who Are You?", my_fnt),
        LblElem("This is a Text", my_fnt),
        LblElem("There are no", my_fnt),
        LblElem("swear words", my_fnt),
        LblElem("in this Test", my_fnt)]
    PygCtl.ctls.extend(MyLst)
    PygCtl.ctls.append(HyperScroll(MyLst, 6, (200, 100), my_fnt.size("h")[1] + 8))
    PygCtl.ctls[-1].animate()
    PygCtl.RunCtls()
    PygCtl.ctls = list()
    pygame.quit()


def FindLstWord(txt, Lst, *args):
    rtn = -1
    CurLen = 0
    for Word in Lst:
        pos = txt.find(Word, *args)
        if pos != -1:
            if pos < rtn or rtn == -1:
                CurLen = len(Word)
                rtn = pos
    return (rtn, CurLen)


def Main1():
    PygCtl.BKGR = (192, 192, 192)
    PygCtl.Init()
    dct_shared = {"Done": False}
    BanWords = ["ban", "bomb", "weird", "stupid"]

    def on_pre_chg(Ln, evt):
        return True

    def on_post_chg(Ln, evt):
        txt = u"".join(Ln.txt).lower()
        for Word in BanWords:
            if Word in txt:
                print("found banned word: " + Word)

    def OnEnter(Ln):
        dct_shared["Done"] = True

    def on_censor(draw_txt):
        low_txt = draw_txt.lower()
        pos, length = FindLstWord(low_txt, BanWords)
        while pos != -1:
            draw_txt = draw_txt[:pos] + u"\u2022" * length + draw_txt[pos + length:]
            pos, length = FindLstWord(low_txt, BanWords, pos + 1)
        return draw_txt

    is_done = lambda: not dct_shared["Done"]
    fnt_name = "Courier New"
    if pygame.font.match_font(fnt_name) is None:
        fnt_name = "liberation sans"
    my_fnt = pygame.font.SysFont(fnt_name, 16)
    my_line = EntryLine(
        my_fnt, (25, 25), (200, my_fnt.size("M")[1] + 4),
        ((0, 0, 0), (128, 192, 192)), on_pre_chg, on_post_chg, OnEnter,
        "BOMB you", on_censor)
    PygCtl.ctls = [my_line]
    pygame.key.set_repeat(250, 1000 / 30)
    EntryLine.init_timer()
    PygCtl.RunCtls(is_done)
    pygame.quit()


def prn_func(Btn, pos):
    print("hello: " + str(pos))


def Main2():
    PygCtl.Init()
    PygCtl.BKGR = (0xD0, 0xD0, 0xD0)
    fnt_name = "Arial"
    if pygame.font.match_font(fnt_name) is None:
        fnt_name = "liberation sans"
    my_fnt = pygame.font.SysFont(fnt_name, 12)
    PygCtl.ctls.append(GradBtn("hello there", prn_func, (10, 10), my_fnt, (6, 2)))
    PygCtl.ctls.append(GradBtn("hello there", prn_func, (10, 35), my_fnt, (6, 2), my_grad_btn))
    PygCtl.run_ctls()
    PygCtl.ctls = list()
    pygame.quit()


def Main3():
    PygCtl.BKGR = (192, 192, 192)
    PygCtl.Init()
    dct_shared = {"Done": False}
    BanWords = ["ban", "bomb", "weird", "stupid"]

    def on_pre_chg(Ln, evt):
        return True

    def on_post_chg(Ln, evt):
        txt = u"".join(Ln.txt.Str).lower()
        for Word in BanWords:
            if Word in txt:
                print("found banned word: " + Word)
        if "clipboard" in txt: print(pygame.scrap.get_types())

    def OnEnter(Ln):
        dct_shared["Done"] = True

    def on_censor(draw_txt):
        low_txt = draw_txt.lower()
        pos, length = FindLstWord(low_txt, BanWords)
        while pos != -1:
            draw_txt = draw_txt[:pos] + u"\u2022" * length + draw_txt[pos + length:]
            pos, length = FindLstWord(low_txt, BanWords, pos + 1)
        return draw_txt

    is_done = lambda: not dct_shared["Done"]
    fnt_name = "Arial"
    if pygame.font.match_font(fnt_name) is None:
        fnt_name = "liberation sans"
    my_fnt = pygame.font.SysFont(fnt_name, 16)
    my_line = EntryBox(
        my_fnt, (25, 25), (200, my_fnt.get_linesize() * 10 + 4),
        ((0, 0, 0), (255, 255, 255)), on_pre_chg, on_post_chg, OnEnter,
        "BOMB you", on_censor)
    PygCtl.ctls = [my_line]
    pygame.key.set_repeat(250, 1000 / 30)
    EntryBox.init_timer()
    PygCtl.run_ctls(is_done)
    pygame.quit()


class ErrLabel(PygCtl.Label):
    def on_evt_global(self, app, evt):
        if evt.type == pygame.MOUSEBUTTONDOWN:
            try:
                PygCtl.ctls.remove(self)
            except ValueError:
                pass
            return True
        super(ErrLabel, self).on_evt_global(evt)


def Main4():
    PygCtl.BKGR = (192, 192, 192)
    PygCtl.Init()
    fnt_name = "Arial"
    if pygame.font.match_font(fnt_name) is None:
        fnt_name = "liberation sans"
    my_fnt = pygame.font.SysFont(fnt_name, 16)
    MyFnt1 = pygame.font.SysFont("Courier New", 16)
    MyBox = EntryBox(
        MyFnt1, (20, 76), (600, MyFnt1.get_linesize() * 20 + 4),
        ((0, 0, 0), (255, 255, 255)))
    my_line = EntryLine(
        MyFnt1, (190, 25), (400, MyFnt1.get_linesize() + 4),
        ((0, 0, 0), (128, 192, 192)))

    def load(Btn, pos):
        fName = u"".join(my_line.txt)
        try:
            with open(fName, "rb") as Fl:
                MyBox.txt.SetStr(Fl.read().decode("utf-8"), "\n")
        except IOError as Exc:
            PygCtl.ctls.append(ErrLabel(str(Exc), (20, 52), MyFnt1, (PygCtl.BKGR, PygCtl.RED)))
            PygCtl.set_redraw(PygCtl.ctls[-1])
            return
        except UnicodeDecodeError as Exc:
            PygCtl.ctls.append(ErrLabel(str(Exc), (20, 52), MyFnt1, (PygCtl.BKGR, PygCtl.RED)))
            PygCtl.set_redraw(PygCtl.ctls[-1])
            return
        MyBox.ch_pos = [0, 0]
        MyBox.highlight_pos = [0, 0]
        PygCtl.set_redraw(MyBox)

    def Save(Btn, pos):
        fName = u"".join(my_line.txt)
        with open(fName, "wb") as Fl:
            Fl.write(MyBox.txt.GetStr(0, len(MyBox.txt.Str)).encode("utf-8"))

    def OnResize(evt):
        MyBox.set_size((evt.size[0] - 40, MyBox.line_h * ((evt.size[1] - 104) // MyBox.line_h) + 4))

    PygCtl.DctEvtFunc[pygame.VIDEORESIZE] = OnResize
    LoadBtn = GradBtn("load File", load, (10, 25), my_fnt, (6, 2))
    SaveBtn = GradBtn("Save File", Save, (100, 25), my_fnt, (6, 2))
    PygCtl.ctls = [LoadBtn, SaveBtn, MyBox, my_line]
    pygame.key.set_repeat(250, 1000 / 30)
    EntryBox.init_timer()
    EntryLine.init_timer()
    PygCtl.run_ctls()
    pygame.quit()


if __name__ == "__main__": Main4()

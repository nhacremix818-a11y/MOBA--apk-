# -*- coding: utf-8 -*-
"""
DAU TRUONG ANH HUNG 3D HD - MOBA offline 5v5 (do hoa chi tiet: ban do, tuong, cong trinh)
Ban do 3 duong (Tren / Giua / Duoi), song, rung, Rong Co, Bao Chua, tru, nha chinh.
Chay:  pip install pygame   roi   python moba_offline.py

Dieu khien (PC):  WASD/phim mui ten = di chuyen | SPACE = danh thuong
Q E R = ky nang | F = hoi mau | G = toc bien | B = ve thanh | 1-4 = mua do (khi o can cu)
Co the dung chuot bam vao cac nut tren man hinh va can analog ben trai (nhu ban mobile).
"""
import math
import os
import random
import sys
import pygame

try:
    import android  # chi co tren Android
except ImportError:
    android = None

W, H, FPS = 1280, 720, 60
WORLD = 3600
BLUE, RED, NEUTRAL = 0, 1, 2
TEAM_COL = {0: (70, 140, 255), 1: (235, 80, 80), 2: (210, 170, 60)}
BASE_POS = {BLUE: (400, 3200), RED: (3200, 400)}

LANES = {
    "top": [(400, 3200), (400, 400), (3200, 400)],
    "mid": [(400, 3200), (1800, 1800), (3200, 400)],
    "bot": [(400, 3200), (3200, 3200), (3200, 400)],
}
LANE_NAME = {"top": "Đường Trên", "mid": "Đường Giữa", "bot": "Đường Dưới"}

TOWER_POS = {
    BLUE: [(400, 2600), (400, 1900), (400, 1200),
           (900, 2700), (1250, 2350), (1550, 2050),
           (1000, 3200), (1700, 3200), (2400, 3200)],
    RED: [(1000, 400), (1700, 400), (2400, 400),
          (2700, 900), (2350, 1250), (2050, 1550),
          (3200, 2400), (3200, 1700), (3200, 1000)],
}
CAMPS = [(900, 2300), (1300, 2950), (1000, 1400), (1700, 2800)]

ITEMS = [("Kiếm Cuồng Phong", "atk", 25, 600),
         ("Gậy Thần", "ap", 45, 600),
         ("Giáp Hộ Mệnh", "hp", 350, 600),
         ("Giày Tốc Hành", "spd", 25, 450)]
ITEM_LABEL = {"atk": "Công", "ap": "Phép", "hp": "Máu", "spd": "Tốc"}

TYPE_VI = {"shot": "Phóng chiêu", "aoe": "Vùng quanh người", "dash": "Lướt",
           "ground": "Chỉ định vùng", "heal": "Hồi máu", "shield": "Khiên",
           "buff": "Cường hóa"}


def S(n, t, cd, dmg=0, **k):
    d = dict(n=n, t=t, cd=cd, dmg=dmg)
    d.update(k)
    return d


def Hh(name, role, hp, atk, ap, rng, spd, itv, col, sc, sk):
    return dict(name=name, role=role, hp=hp, atk=atk, ap=ap, rng=rng, spd=spd,
                itv=itv, col=col, sc=sc, sk=sk)


# Danh sach tuong (ten theo nhan vat lich su / than thoai; ky nang la ky nang goc cua game nay).
# Muon them tuong: chi can them mot dong Hh(...) vao danh sach nay.
HEROES = [
    Hh("Lữ Bố", "Đấu sĩ", 2300, 85, 20, 90, 250, 0.9, (200, 50, 50), 'a', [
        S("Họa Kích Xoay", "aoe", 5, 200, r=170),
        S("Xung Phong", "dash", 7, 180, d=330, st=0.6),
        S("Chiến Thần", "aoe", 14, 380, r=260, st=1.2)]),
    Hh("Quan Vũ", "Đấu sĩ", 2200, 80, 20, 90, 265, 0.9, (40, 160, 80), 'a', [
        S("Thanh Long Trảm", "dash", 6, 180, d=300),
        S("Uy Phong", "aoe", 8, 200, r=200, sl=1.5),
        S("Chiến Ý", "buff", 16, 0, dur=5)]),
    Hh("Triệu Vân", "Đấu sĩ", 2100, 78, 30, 90, 275, 0.85, (230, 230, 240), 'a', [
        S("Long Thương", "shot", 5, 200, r=520, p=True),
        S("Hồi Mã Thương", "dash", 8, 180, d=340),
        S("Bạch Long", "aoe", 12, 380, r=230, st=0.8)]),
    Hh("Hạng Vũ", "Đấu sĩ", 2500, 82, 20, 90, 255, 0.95, (150, 60, 160), 'a', [
        S("Bá Vương Chém", "aoe", 6, 200, r=190),
        S("Giáp Sắt", "shield", 10, 500),
        S("Phá Thiên", "ground", 13, 400, r=230, rg=400, st=1.0)]),
    Hh("Hoa Mộc Lan", "Đấu sĩ", 2150, 80, 30, 90, 270, 0.85, (240, 120, 170), 'a', [
        S("Kiếm Lướt", "dash", 5, 180, d=300),
        S("Xoay Kiếm", "aoe", 7, 200, r=190),
        S("Nữ Tướng", "buff", 12, 0, dur=6)]),
    Hh("Lý Bạch", "Sát thủ", 1800, 90, 40, 95, 285, 0.8, (90, 200, 220), 'a', [
        S("Kiếm Khí", "dash", 5, 190, d=320),
        S("Thi Tiên", "dash", 7, 200, d=300),
        S("Nhất Kiếm Tây Lai", "aoe", 14, 450, r=260)]),
    Hh("Hàn Tín", "Sát thủ", 1850, 88, 20, 95, 290, 0.8, (60, 90, 200), 'a', [
        S("Phi Thương", "shot", 4, 150, r=450),
        S("Lướt Gió", "dash", 8, 220, d=340),
        S("Quân Lệnh", "aoe", 14, 400, r=220, st=0.9)]),
    Hh("Kinh Kha", "Sát thủ", 1750, 92, 30, 95, 295, 0.75, (70, 70, 80), 'a', [
        S("Ám Kích", "aoe", 4, 140, r=150),
        S("Ẩn Thân Lướt", "dash", 7, 170, d=360),
        S("Cuồng Sát", "buff", 12, 0, dur=5)]),
    Hh("Tôn Ngộ Không", "Sát thủ", 1950, 86, 30, 95, 280, 0.85, (235, 190, 40), 'a', [
        S("Gậy Như Ý", "aoe", 4, 150, r=170),
        S("Cân Đẩu Vân", "dash", 7, 180, d=330, st=0.4),
        S("Đại Náo", "aoe", 13, 420, r=260, st=1.0)]),
    Hh("Gia Cát Lượng", "Pháp sư", 1650, 55, 120, 520, 250, 1.1, (120, 90, 230), 'p', [
        S("Quạt Lửa", "shot", 4, 190, r=650),
        S("Bát Quái", "ground", 7, 240, r=200, rg=560, st=0.5),
        S("Hỏa Công", "ground", 14, 480, r=280, rg=600, st=1.0)]),
    Hh("Điêu Thuyền", "Pháp sư", 1600, 55, 130, 500, 260, 1.0, (230, 90, 200), 'p', [
        S("Hoa Hồng Bay", "shot", 4, 170, r=600, p=True),
        S("Vũ Điệu", "aoe", 7, 210, r=230),
        S("Mỹ Nhân Kế", "aoe", 14, 450, r=300, sl=2.0)]),
    Hh("Đát Kỷ", "Pháp sư", 1550, 52, 140, 520, 250, 1.05, (250, 130, 90), 'p', [
        S("Cầu Hồ Ly", "shot", 3.5, 170, r=700),
        S("Mị Hoặc", "ground", 8, 220, r=210, rg=550, st=0.7),
        S("Hồ Hỏa", "shot", 13, 450, r=800, p=True, st=1.0)]),
    Hh("Hậu Nghệ", "Xạ thủ", 1600, 100, 20, 560, 255, 0.7, (240, 200, 90), 'a', [
        S("Tên Xuyên", "shot", 5, 180, r=700, p=True),
        S("Lùi Bước", "dash", 8, 0, d=280, back=True),
        S("Cửu Nhật", "ground", 14, 500, r=260, rg=700)]),
    Hh("Lỗ Ban", "Xạ thủ", 1700, 95, 30, 520, 250, 0.75, (180, 140, 90), 'a', [
        S("Đạn Máy", "shot", 5, 200, r=600),
        S("Pháo Cơ Quan", "ground", 8, 200, r=200, rg=500, st=0.5),
        S("Cuồng Hỏa", "buff", 14, 0, dur=5)]),
    Hh("Trương Phi", "Đỡ đòn", 2800, 70, 20, 90, 245, 1.0, (60, 60, 140), 'a', [
        S("Gầm Thét", "aoe", 6, 150, r=200),
        S("Giáp Thép", "shield", 10, 700),
        S("Trấn Địa", "aoe", 14, 300, r=300, st=1.5)]),
    Hh("Điển Vi", "Đỡ đòn", 2700, 74, 20, 90, 250, 1.0, (130, 100, 70), 'a', [
        S("Húc Mạnh", "dash", 6, 150, d=280, st=0.5),
        S("Song Kích", "aoe", 8, 180, r=220, sl=1.5),
        S("Ác Lai", "aoe", 14, 320, r=280, st=1.2)]),
    Hh("Thái Ất Chân Nhân", "Hỗ trợ", 2000, 55, 100, 500, 250, 1.0, (120, 220, 170), 'p', [
        S("Phù Chú", "shot", 5, 150, r=600, st=0.4),
        S("Cam Lộ", "heal", 9, 350, r=350),
        S("Đại Phục Hồi", "heal", 16, 700, r=450)]),
    Hh("Khương Tử Nha", "Hỗ trợ", 1800, 55, 110, 520, 250, 1.0, (230, 230, 120), 'p', [
        S("Đả Thần Tiên", "ground", 5, 180, r=190, rg=550),
        S("Thần Chú", "heal", 9, 300, r=300),
        S("Phong Thần", "ground", 14, 420, r=280, rg=600, st=1.1)]),
]


# ----------------------------------------------------------------------------
# Tien ich
# ----------------------------------------------------------------------------
def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def lane_path(lane, team):
    return LANES[lane] if team == BLUE else LANES[lane][::-1]


FONTS, TC = {}, {}


FONT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DejaVuSans.ttf")


def font(sz, bold=False):
    k = (sz, bold)
    if k not in FONTS:
        if os.path.exists(FONT_FILE):  # font di kem (hien thi dung tieng Viet tren Android)
            f = pygame.font.Font(FONT_FILE, sz)
            f.set_bold(bold)
            FONTS[k] = f
        else:
            FONTS[k] = pygame.font.SysFont("arial,dejavusans,notosans,segoeui,tahoma", sz, bold=bold)
    return FONTS[k]


def text(scr, s, sz, col, pos, center=False, bold=False):
    key = (s, sz, col, bold)
    img = TC.get(key)
    if img is None:
        if len(TC) > 1500:
            TC.clear()
        img = font(sz, bold).render(s, True, col)
        TC[key] = img
    r = img.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    scr.blit(img, r)


def bar(scr, x, y, w, h, ratio, col):
    pygame.draw.rect(scr, (15, 15, 15), (x - 1, y - 1, w + 2, h + 2))
    pygame.draw.rect(scr, col, (x, y, int(w * max(0, min(1, ratio))), h))


def cc(e, st=0, sl=0):
    if e.kind in ("hero", "minion", "monster"):
        if st:
            e.stun = max(e.stun, st)
        if sl:
            e.slow = max(e.slow, sl)


# ----------------------------------------------------------------------------
# Don vi
# ----------------------------------------------------------------------------
class Unit:
    kind = "unit"

    def __init__(s, team, x, y, hp, r, armor=0):
        s.team, s.x, s.y = team, x, y
        s.maxhp = s.hp = hp
        s.r, s.armor = r, armor
        s.alive = True
        s.stun = s.slow = 0
        s.shield = s.shield_t = 0
        s.atk_cd = 0

    def take(s, dmg, src, game):
        if not s.alive:
            return
        dmg = dmg * 100 / (100 + max(0, s.armor))
        if s.shield > 0:
            ab = min(s.shield, dmg)
            s.shield -= ab
            dmg -= ab
        if dmg >= 1 and (s.kind == 'hero' or getattr(src, 'is_player', False)):
            game.pop(s.x, s.y, int(dmg), (255, 90, 90) if s.kind == 'hero' else (255, 235, 140))
        s.hp -= dmg
        s.on_hit(src)
        if s.hp <= 0:
            s.hp = 0
            s.alive = False
            game.on_death(s, src)

    def on_hit(s, src):
        pass

    def heal(s, a):
        s.hp = min(s.maxhp, s.hp + a)

    def step(s, tx, ty, dt, spd):
        dx, dy = tx - s.x, ty - s.y
        l = math.hypot(dx, dy)
        if l < 1:
            return
        m = min(l, spd * dt)
        s.x += dx / l * m
        s.y += dy / l * m


class Minion(Unit):
    kind = "minion"

    def __init__(s, team, lane, ranged, wave):
        path = lane_path(lane, team)
        x, y = path[0]
        super().__init__(team, x + random.randint(-60, 60), y + random.randint(-60, 60),
                         (300 if ranged else 480) + wave * 14, 14)
        s.lane, s.ranged, s.idx = lane, ranged, 1
        s.atk = (32 if ranged else 24) + wave * 1.5
        s.rng = 190 if ranged else 36
        s.spd = 95

    def update(s, dt, game):
        s.atk_cd -= dt
        s.stun = max(0, s.stun - dt)
        s.slow = max(0, s.slow - dt)
        if s.stun > 0:
            return
        sp = s.spd * (0.5 if s.slow > 0 else 1)
        t = game.find_target(s, 240, False)
        if t:
            d = math.hypot(t.x - s.x, t.y - s.y) - t.r - s.r
            if d <= s.rng:
                if s.atk_cd <= 0:
                    t.take(s.atk, s, game)
                    s.atk_cd = 1.1
                    if s.ranged:
                        game.line(s.x, s.y, t.x, t.y, TEAM_COL[s.team], 0.1)
            else:
                s.step(t.x, t.y, dt, sp)
        else:
            path = lane_path(s.lane, s.team)
            wx, wy = path[min(s.idx, len(path) - 1)]
            if math.hypot(wx - s.x, wy - s.y) < 60 and s.idx < len(path) - 1:
                s.idx += 1
                wx, wy = path[s.idx]
            s.step(wx, wy, dt, sp)


class Tower(Unit):
    kind = "tower"

    def __init__(s, team, x, y, base=False):
        super().__init__(team, x, y, 6000 if base else 2800, 55 if base else 36,
                         armor=50 if base else 40)
        s.base = base
        s.range = 420 if base else 380
        s.dmg = 150 if base else 115

    def update(s, dt, game):
        s.atk_cd -= dt
        if s.atk_cd > 0:
            return
        c = [e for e in game.en[s.team] if e.alive and e.kind in ("hero", "minion")
             and math.hypot(e.x - s.x, e.y - s.y) <= s.range + e.r]
        if not c:
            return
        m = [e for e in c if e.kind == "minion"]
        pool = m or c
        t = min(pool, key=lambda e: math.hypot(e.x - s.x, e.y - s.y))
        t.take(s.dmg, s, game)
        s.atk_cd = 1.2
        game.line(s.x, s.y - 20, t.x, t.y, (255, 240, 120), 0.12)


class Monster(Unit):
    kind = "monster"

    def __init__(s, x, y, name="Quái rừng"):
        if name == "Rồng Cổ":
            hp, atk, r = 6500, 95, 48
        elif name == "Bạo Chúa":
            hp, atk, r = 8000, 110, 52
        else:
            hp, atk, r = 1500, 48, 24
        super().__init__(NEUTRAL, x, y, hp, r, armor=20)
        s.name, s.atk, s.home = name, atk, (x, y)
        s.boss = name != "Quái rừng"
        s.spd = 140
        s.tgt, s.aggro, s.ret, s.rt = None, 0, False, 0

    def on_hit(s, src):
        if src is not None and src.alive:
            s.tgt, s.aggro = src, 6

    def update(s, dt, game):
        if not s.alive:
            s.rt -= dt
            if s.rt <= 0:
                s.alive, s.hp = True, s.maxhp
                s.x, s.y = s.home
                s.tgt, s.aggro, s.ret = None, 0, False
            return
        s.atk_cd -= dt
        s.aggro -= dt
        s.stun = max(0, s.stun - dt)
        s.slow = max(0, s.slow - dt)
        if s.stun > 0:
            return
        hx, hy = s.home
        if s.ret:
            s.step(hx, hy, dt, s.spd * 1.5)
            s.heal(s.maxhp * 0.3 * dt)
            if math.hypot(s.x - hx, s.y - hy) < 20:
                s.ret = False
            return
        t = s.tgt if (s.tgt and s.tgt.alive and s.aggro > 0) else None
        if t is None:
            t = game.nearest(s, 230, ("hero",))
        if t and math.hypot(s.x - hx, s.y - hy) > 520:
            s.ret, s.tgt, s.aggro = True, None, 0
            return
        if t:
            d = math.hypot(t.x - s.x, t.y - s.y) - t.r - s.r
            if d <= 20:
                if s.atk_cd <= 0:
                    t.take(s.atk, s, game)
                    s.atk_cd = 1.2
            else:
                s.step(t.x, t.y, dt, s.spd * (0.5 if s.slow > 0 else 1))
        elif s.hp < s.maxhp:
            s.heal(s.maxhp * 0.1 * dt)


class Hero(Unit):
    kind = "hero"

    def __init__(s, team, d, is_player, lane):
        bx, by = BASE_POS[team]
        super().__init__(team, bx + random.randint(-120, 120), by + random.randint(-120, 120),
                         d['hp'], 22)
        s.d, s.name, s.is_player, s.lane = d, d['name'], is_player, lane
        s.level, s.xp, s.gold = 1, 0, 500.0
        s.kills = s.deaths = 0
        s.b_hp = s.b_atk = s.b_ap = s.b_spd = 0
        s.items = [0, 0, 0, 0]
        s.cd = [0, 0, 0]
        s.heal_cd = s.flash_cd = 0
        s.recall = s.respawn = 0
        s.abuff = s.sbuff = 0
        s.idx = 1
        s.range = d['rng']
        s.walk = s.swing = s.mov = 0
        s.fx, s.fy = (0.707, -0.707) if team == BLUE else (-0.707, 0.707)
        s.recalc()
        s.hp = s.maxhp

    # --- chi so -------------------------------------------------------------
    def recalc(s):
        d, L = s.d, s.level - 1
        nm = d['hp'] + L * 140 + s.b_hp
        s.hp += nm - s.maxhp
        s.maxhp = nm
        s.atk_v = d['atk'] + L * 6 + s.b_atk
        s.ap_v = d['ap'] + L * 8 + s.b_ap
        s.armor = 30 + L * 4

    def power(s, game):
        return (1.2 if game.buff[s.team] > 0 else 1.0) * (1.3 if s.abuff > 0 else 1.0)

    def speed(s):
        v = s.d['spd'] + s.b_spd
        if s.slow > 0:
            v *= 0.55
        if s.sbuff > 0:
            v *= 1.3
        return v

    def add_xp(s, x):
        s.xp += x
        while s.level < 15 and s.xp >= 120 + 70 * s.level:
            s.xp -= 120 + 70 * s.level
            s.level += 1
            s.recalc()

    def in_base(s):
        bx, by = BASE_POS[s.team]
        return math.hypot(s.x - bx, s.y - by) < 340

    def on_hit(s, src):
        s.recall = 0

    # --- mua do -------------------------------------------------------------
    def cost(s, i):
        return int(ITEMS[i][3] * (1 + 0.25 * s.items[i]))

    def buy(s, i):
        if not s.in_base() or not s.alive:
            return False
        c = s.cost(i)
        if s.gold < c:
            return False
        s.gold -= c
        s.items[i] += 1
        st, v = ITEMS[i][1], ITEMS[i][2]
        setattr(s, 'b_' + st, getattr(s, 'b_' + st) + v)
        s.recalc()
        return True

    def auto_buy(s):
        order = [0, 2, 3] if s.d['sc'] == 'a' else [1, 2, 3]
        for _ in range(4):
            if not s.buy(random.choice(order)):
                break

    # --- hanh dong -----------------------------------------------------------
    def move(s, dx, dy, dt):
        l = math.hypot(dx, dy)
        if l < 1e-3:
            return
        dx, dy = dx / l, dy / l
        sp = s.speed()
        s.x = min(WORLD - 40, max(40, s.x + dx * sp * dt))
        s.y = min(WORLD - 40, max(40, s.y + dy * sp * dt))
        s.fx, s.fy = dx, dy
        s.recall = 0
        s.walk += dt * sp * 0.03
        s.mov = 0.15

    def attack(s, game):
        if s.atk_cd > 0 or not s.alive:
            return False
        t = game.find_target(s, s.range, True)
        if not t:
            return False
        dmg = s.atk_v * s.power(game)
        s.fx, s.fy = (t.x - s.x), (t.y - s.y)
        l = math.hypot(s.fx, s.fy) or 1
        s.fx, s.fy = s.fx / l, s.fy / l
        t.take(dmg, s, game)
        s.atk_cd = s.d['itv'] / (1.3 if s.abuff > 0 else 1)
        s.swing = 0.3
        s.recall = 0
        if s.range > 150:
            game.line(s.x, s.y, t.x, t.y, s.d['col'], 0.1)
        return True

    def aim(s, game, rng=800):
        t = game.find_target(s, rng, True)
        if t:
            dx, dy = t.x - s.x, t.y - s.y
            l = math.hypot(dx, dy) or 1
            return dx / l, dy / l, t
        return s.fx, s.fy, None

    def skill_dmg(s, sk, game):
        base = sk['dmg'] * (1 + 0.15 * (s.level - 1))
        ratio = 0.5 * (s.ap_v if s.d['sc'] == 'p' else s.atk_v) if sk['dmg'] > 0 else 0
        return (base + ratio) * s.power(game)

    def cast(s, i, game):
        sk = s.d['sk'][i]
        if not s.alive or s.cd[i] > 0 or s.stun > 0:
            return False
        ax, ay, t = s.aim(game)
        dmg = s.skill_dmg(sk, game)
        ty = sk['t']
        s.recall = 0
        if ty == 'shot':
            game.projs.append(Proj(s, ax, ay, sk, dmg))
        elif ty == 'aoe':
            game.area(s, s.x, s.y, sk['r'], dmg, sk.get('st', 0), sk.get('sl', 0))
        elif ty == 'ground':
            rg = sk.get('rg', 500)
            if t:
                d = min(rg, math.hypot(t.x - s.x, t.y - s.y))
                cx, cy = s.x + ax * d, s.y + ay * d
            else:
                cx, cy = s.x + ax * rg * 0.6, s.y + ay * rg * 0.6
            game.area(s, cx, cy, sk['r'], dmg, sk.get('st', 0), sk.get('sl', 0))
        elif ty == 'dash':
            back = sk.get('back')
            if back:
                ax, ay = -ax, -ay
            x0, y0 = s.x, s.y
            x1 = min(WORLD - 40, max(40, x0 + ax * sk['d']))
            y1 = min(WORLD - 40, max(40, y0 + ay * sk['d']))
            if dmg > 0:
                for e in game.en[s.team]:
                    if e.alive and seg_dist(e.x, e.y, x0, y0, x1, y1) < 70 + e.r:
                        e.take(dmg, s, game)
                        cc(e, sk.get('st', 0), sk.get('sl', 0))
            s.x, s.y = x1, y1
            if not back:
                s.fx, s.fy = ax, ay
            game.line(x0, y0, x1, y1, s.d['col'], 0.25)
        elif ty == 'heal':
            for h in game.heroes:
                if h.alive and h.team == s.team and math.hypot(h.x - s.x, h.y - s.y) <= sk['r']:
                    h.heal(dmg)
            game.ring(s.x, s.y, sk['r'], (90, 255, 130), 0.4)
        elif ty == 'shield':
            s.shield += dmg
            s.shield_t = 4
            game.ring(s.x, s.y, 50, (120, 220, 255), 0.4)
        elif ty == 'buff':
            s.abuff = s.sbuff = sk.get('dur', 5)
            game.ring(s.x, s.y, 60, (255, 220, 80), 0.4)
        s.cd[i] = sk['cd']
        s.swing = 0.4
        return True

    def heal_spell(s, game):
        if not s.alive or s.heal_cd > 0:
            return
        s.heal(s.maxhp * 0.15 + 200)
        s.heal_cd = 60
        game.ring(s.x, s.y, 70, (90, 255, 130), 0.4)

    def flash(s, game):
        if not s.alive or s.flash_cd > 0:
            return
        x0, y0 = s.x, s.y
        s.x = min(WORLD - 40, max(40, s.x + s.fx * 300))
        s.y = min(WORLD - 40, max(40, s.y + s.fy * 300))
        s.flash_cd = 90
        s.recall = 0
        game.line(x0, y0, s.x, s.y, (255, 255, 255), 0.25)

    def start_recall(s):
        if s.alive and not s.in_base():
            s.recall = 4.0

    def revive(s):
        s.alive = True
        s.hp = s.maxhp
        bx, by = BASE_POS[s.team]
        s.x, s.y = bx + random.randint(-100, 100), by + random.randint(-100, 100)
        s.idx, s.recall, s.stun = 1, 0, 0

    # --- cap nhat --------------------------------------------------------------
    def update(s, dt, game):
        if not s.alive:
            s.respawn -= dt
            if s.respawn <= 0:
                s.revive()
            return
        for i in range(3):
            s.cd[i] = max(0, s.cd[i] - dt)
        s.heal_cd = max(0, s.heal_cd - dt)
        s.flash_cd = max(0, s.flash_cd - dt)
        s.atk_cd -= dt
        s.stun = max(0, s.stun - dt)
        s.slow = max(0, s.slow - dt)
        s.abuff = max(0, s.abuff - dt)
        s.sbuff = max(0, s.sbuff - dt)
        s.swing = max(0, s.swing - dt)
        s.mov = max(0, s.mov - dt)
        if s.shield_t > 0:
            s.shield_t -= dt
            if s.shield_t <= 0:
                s.shield = 0
        s.gold += 3 * dt
        if s.in_base():
            s.heal(s.maxhp * 0.12 * dt)
        if s.recall > 0:
            s.recall -= dt
            if s.recall <= 0:
                s.recall = 0
                s.x, s.y = BASE_POS[s.team]
                game.ring(s.x, s.y, 80, (120, 200, 255), 0.5)
            if not s.is_player:
                return
        if s.stun > 0:
            return
        if s.is_player:
            game.player_control(s, dt)
        else:
            s.ai(dt, game)

    # --- AI bot ------------------------------------------------------------------
    def skill_ok(s, i, d):
        sk = s.d['sk'][i]
        ty = sk['t']
        if ty == 'shot':
            return d <= sk['r'] * 0.9
        if ty == 'aoe':
            return d <= sk['r'] * 0.8
        if ty == 'dash':
            if sk.get('back'):
                return d < 250 and s.hp < s.maxhp * 0.6
            return 120 < d <= sk['d']
        if ty == 'ground':
            return d <= sk.get('rg', 500)
        if ty == 'heal':
            return s.hp < s.maxhp * 0.55
        if ty in ('shield', 'buff'):
            return d < 450
        return False

    def near_enemy_tower(s, game, extra):
        for e in game.en[s.team]:
            if e.kind == "tower" and e.alive and math.hypot(e.x - s.x, e.y - s.y) < e.range + extra:
                return True
        return False

    def ai(s, dt, game):
        mb = BASE_POS[s.team]
        if s.in_base():
            s.idx = 1
            s.auto_buy()
            if s.hp < s.maxhp * 0.9:
                return
        foe = game.find_target(s, 700, True)
        if s.hp < s.maxhp * 0.3:
            if foe:
                if s.heal_cd <= 0:
                    s.heal_spell(game)
                s.move(mb[0] - s.x, mb[1] - s.y, dt)
            elif not s.in_base():
                s.recall = 4.0
            return
        if s.gold >= 1400 and not foe and not s.in_base():
            s.recall = 4.0
            return
        if foe:
            if s.near_enemy_tower(game, 50) and not game.ally_minion_near(s, 350):
                s.move(mb[0] - s.x, mb[1] - s.y, dt)
                return
            d = math.hypot(foe.x - s.x, foe.y - s.y) - foe.r - s.r
            for i in range(3):
                if s.cd[i] <= 0 and s.skill_ok(i, d):
                    s.cast(i, game)
                    break
            if d <= s.range:
                s.attack(game)
            else:
                s.move(foe.x - s.x, foe.y - s.y, dt)
            return
        path = lane_path(s.lane, s.team)
        s.idx = min(s.idx, len(path) - 1)
        wx, wy = path[s.idx]
        if math.hypot(wx - s.x, wy - s.y) < 140 and s.idx < len(path) - 1:
            s.idx += 1
            wx, wy = path[s.idx]
        if s.near_enemy_tower(game, 130) and not game.ally_minion_near(s, 400):
            return
        s.move(wx - s.x, wy - s.y, dt)


class Proj:
    def __init__(s, owner, ax, ay, sk, dmg):
        s.o, s.x, s.y = owner, owner.x, owner.y
        sp = sk.get('sp', 750)
        s.vx, s.vy = ax * sp, ay * sp
        s.left = sk.get('r', 600)
        s.dmg, s.pierce, s.st = dmg, sk.get('p', False), sk.get('st', 0)
        s.hit = set()
        s.alive = True
        s.col = owner.d['col']

    def update(s, dt, game):
        s.x += s.vx * dt
        s.y += s.vy * dt
        s.left -= math.hypot(s.vx, s.vy) * dt
        for e in game.en[s.o.team]:
            if e.alive and id(e) not in s.hit and math.hypot(e.x - s.x, e.y - s.y) < 26 + e.r:
                s.hit.add(id(e))
                e.take(s.dmg, s.o, game)
                cc(e, s.st)
                if not s.pierce:
                    s.alive = False
                    break
        if s.left <= 0:
            s.alive = False


# ----------------------------------------------------------------------------
# Tran dau
# ----------------------------------------------------------------------------
PITCH = math.radians(58)          # goc nghieng camera (giong Lien Quan)
SP, CP = math.sin(PITCH), math.cos(PITCH)
CAM_DIST, FOC, NEAR = 1100.0, 900.0, 60.0
SCY = H / 2 + 30
LOW = "ANDROID_ARGUMENT" in os.environ   # che do nhe cho dien thoai
VR, VR2 = (1100, 1000) if LOW else (1500, 1400)


def cam_space(t, x, y, z=0.0):
    vy = (y - t[1]) - CP * CAM_DIST
    vz = z - SP * CAM_DIST
    return x - t[0], -SP * vy + CP * vz, -CP * vy - SP * vz


def circle_pts(x, y, r, n=20):
    return [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def quad(x1, y1, x2, y2, hw):
    dx, dy = x2 - x1, y2 - y1
    l = math.hypot(dx, dy) or 1
    nx, ny = -dy / l * hw, dx / l * hw
    return [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def pg(scr, pts, col, ol=(25, 20, 28)):
    pygame.draw.polygon(scr, col, pts)
    if ol:
        pygame.draw.polygon(scr, ol, pts, 1)


SKINS = [(245, 214, 176), (232, 190, 150), (210, 160, 120), (180, 130, 95)]
HAIRS = [(40, 30, 30), (220, 200, 120), (180, 60, 50), (240, 240, 250), (60, 40, 90)]
GLOW = {}
VIG = [None]


def glow(scr, x, y, r, col):
    r = max(4, int(r / 4) * 4)
    col = (int(col[0]), int(col[1]), int(col[2]))
    sp = GLOW.get((col, r))
    if sp is None:
        sp = pygame.Surface((2 * r, 2 * r))
        sp.fill((0, 0, 0))
        for i in range(r, 0, -2):
            a = (1 - i / r) ** 2
            pygame.draw.circle(sp, (int(col[0] * a), int(col[1] * a), int(col[2] * a)), (r, r), i)
        GLOW[(col, r)] = sp
    scr.blit(sp, (int(x - r), int(y - r)), special_flags=pygame.BLEND_RGB_ADD)


def vignette():
    if VIG[0] is None:
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(40):
            a = int(130 * (1 - i / 40) ** 2)
            pygame.draw.rect(v, (0, 0, 0, a), (i * 6, i * 4, W - 12 * i, H - 8 * i), 8)
        VIG[0] = v
    return VIG[0]


def hpbar(scr, x, y, w, ratio, col, maxhp):
    bar(scr, int(x - w / 2), int(y), int(w), 7, ratio, col)
    for i in range(1, int(maxhp // 300) + 1):
        xx = int(x - w / 2 + w * i * 300 / maxhp)
        if xx < x + w / 2 - 2:
            pygame.draw.line(scr, (15, 15, 15), (xx, int(y)), (xx, int(y) + 6), 1)


class Game:
    def __init__(s, hero_idx):
        s.units, s.projs, s.fxs, s.feed = [], [], [], []
        s.t, s.wave_t, s.wave_n = 0.0, 8.0, 0
        s.buff, s.score, s.over = [0, 0], [0, 0], None
        s.inp = {'move': (0, 0), 'atk': False, 'stick': None}
        s.en = {0: [], 1: [], 2: []}
        s.cam = (0, 0)
        s.ct = (0, 0)
        for team in (BLUE, RED):
            s.units.append(Tower(team, *BASE_POS[team], base=True))
            for p in TOWER_POS[team]:
                s.units.append(Tower(team, *p))
        for p in CAMPS:
            s.units.append(Monster(*p))
            s.units.append(Monster(WORLD - p[0], WORLD - p[1]))
        s.units.append(Monster(2400, 2400, "Rồng Cổ"))
        s.units.append(Monster(1200, 1200, "Bạo Chúa"))
        pool = [i for i in range(len(HEROES)) if i != hero_idx]
        random.shuffle(pool)
        s.player = Hero(BLUE, HEROES[hero_idx], True, "mid")
        s.heroes = [s.player]
        for lane in ["top", "bot", "mid", "top"]:
            s.heroes.append(Hero(BLUE, HEROES[pool.pop()], False, lane))
        for lane in ["top", "mid", "bot", "bot", "mid"]:
            s.heroes.append(Hero(RED, HEROES[pool.pop()], False, lane))
        s.units += s.heroes
        rnd = random.Random(7)
        s.bushes = []
        while len(s.bushes) < 150:
            x, y = rnd.randint(100, WORLD - 100), rnd.randint(100, WORLD - 100)
            if all(min(seg_dist(x, y, *p[i], *p[i + 1]) for i in range(len(p) - 1)) > 150
                   for p in LANES.values()):
                s.bushes.append((x, y, rnd.randint(30, 60)))

    # --- truy van -----------------------------------------------------------
    def find_target(s, u, rng, prefer_hero=False):
        best, bd, bh, bhd = None, 1e9, None, 1e9
        for e in s.en[u.team]:
            if not e.alive:
                continue
            d = math.hypot(e.x - u.x, e.y - u.y) - e.r - u.r
            if d > rng:
                continue
            if prefer_hero and e.kind == "hero":
                if d < bhd:
                    bh, bhd = e, d
            elif d < bd:
                best, bd = e, d
        return bh or best

    def nearest(s, u, rng, kinds):
        best, bd = None, 1e9
        for e in s.en[u.team]:
            if e.alive and e.kind in kinds:
                d = math.hypot(e.x - u.x, e.y - u.y) - e.r - u.r
                if d <= rng and d < bd:
                    best, bd = e, d
        return best

    def ally_minion_near(s, u, rng):
        for e in s.units:
            if e.kind == "minion" and e.alive and e.team == u.team and \
                    math.hypot(e.x - u.x, e.y - u.y) < rng:
                return True
        return False

    def area(s, src, cx, cy, r, dmg, st=0, sl=0):
        for e in s.en[src.team]:
            if e.alive and math.hypot(e.x - cx, e.y - cy) <= r + e.r:
                e.take(dmg, src, s)
                cc(e, st, sl)
        s.ring(cx, cy, r, src.d['col'] if hasattr(src, 'd') else (255, 255, 255), 0.35)

    def ring(s, x, y, r, col, t=0.35):
        s.fxs.append({'k': 'ring', 'x': x, 'y': y, 'r': r, 'c': col, 't': t, 'm': t})

    def line(s, x1, y1, x2, y2, col, t=0.12):
        s.fxs.append({'k': 'line', 'a': (x1, y1), 'b': (x2, y2), 'c': col, 't': t, 'm': t})

    def say(s, msg):
        s.feed.append([msg, 6.0])
        s.feed = s.feed[-6:]

    # --- su kien ------------------------------------------------------------
    def on_death(s, v, src):
        killer = src if (src is not None and src.kind == "hero") else None
        near_foes = [h for h in s.heroes if h.alive and h.team != v.team
                     and math.hypot(h.x - v.x, h.y - v.y) < 700]
        if v.kind == "hero":
            v.deaths += 1
            v.respawn = 4 + 2 * v.level
            s.score[1 - v.team] += 1
            who = src.name if (src is not None and hasattr(src, 'name')) else "Trụ/Lính"
            s.say("%s hạ gục %s" % (who, v.name))
            if killer:
                killer.kills += 1
                killer.gold += 300
                killer.add_xp(180)
            for h in near_foes:
                if h is not killer:
                    h.add_xp(60)
        elif v.kind == "minion":
            if killer:
                killer.gold += 25
                killer.add_xp(40)
            for h in near_foes:
                if h is not killer:
                    h.add_xp(25)
        elif v.kind == "monster":
            v.rt = 150 if v.boss else 60
            if killer:
                killer.gold += 90
                killer.add_xp(120)
                if v.boss:
                    s.buff[killer.team] = 60
                    for h in s.heroes:
                        if h.team == killer.team:
                            h.gold += 150
                    s.say("%s tiêu diệt %s - cả đội được cường hóa!" % (killer.name, v.name))
        elif v.kind == "tower":
            for h in s.heroes:
                if h.team != v.team and h.alive:
                    h.gold += 150
            if v.base:
                s.over = 1 - v.team
            else:
                s.say("Một trụ của phe %s đã bị phá!" % ("Xanh" if v.team == BLUE else "Đỏ"))

    # --- cap nhat -------------------------------------------------------------
    def player_control(s, h, dt):
        mx, my = s.inp['move']
        if mx or my:
            h.move(mx, my, dt)
        if s.inp['atk']:
            h.attack(s)

    def update(s, dt):
        if s.over is not None:
            return
        s.t += dt
        for i in (0, 1, 2):
            s.en[i] = [u for u in s.units if u.alive and u.team != i]
        s.buff = [max(0, b - dt) for b in s.buff]
        s.wave_t -= dt
        if s.wave_t <= 0:
            s.wave_t = 28
            s.wave_n += 1
            for team in (BLUE, RED):
                for lane in LANES:
                    for k in range(4):
                        s.units.append(Minion(team, lane, k == 3, s.wave_n))
        for u in list(s.units):
            u.update(dt, s) if hasattr(u, 'update') else None
        for p in s.projs:
            p.update(dt, s)
        s.projs = [p for p in s.projs if p.alive]
        s.units = [u for u in s.units if u.alive or u.kind in ("hero", "monster")]
        for f in s.fxs:
            f['t'] -= dt
        s.fxs = [f for f in s.fxs if f['t'] > 0]
        for f in s.feed:
            f[1] -= dt
        s.feed = [f for f in s.feed if f[1] > 0]

    # --- ve 3D chi tiet (HD) ------------------------------------------------------
    def P(s, x, y, z=0.0):
        xc, yc, zc = cam_space(s.ct, x, y, z)
        if zc < NEAR:
            return None
        k = FOC / zc
        return W / 2 + xc * k, SCY - yc * k, k

    def draw_poly(s, scr, pts, col, z=0.0, width=0):
        cp = [cam_space(s.ct, x, y, z) for x, y in pts]
        out, n = [], len(cp)
        for i in range(n):
            a, b = cp[i], cp[(i + 1) % n]
            ain, bin_ = a[2] >= NEAR, b[2] >= NEAR
            if ain:
                out.append(a)
            if ain != bin_:
                t = (NEAR - a[2]) / (b[2] - a[2])
                out.append(tuple(a[j] + (b[j] - a[j]) * t for j in range(3)))
        if len(out) < 3:
            return
        sp = [(int(W / 2 + c[0] * FOC / c[2]), int(SCY - c[1] * FOC / c[2])) for c in out]
        pygame.draw.polygon(scr, col, sp, width)

    def cyl(s, scr, x, y, r, h, col, z0=0.0):
        b, t = s.P(x, y, z0), s.P(x, y, z0 + h)
        if not b or not t:
            return
        rx = max(2, int(r * b[2]))
        ry = max(1, int(rx * SP))
        dark = shade(col, 0.7)
        light = shade(col, 1.2)
        bx, by, tx, ty = int(b[0]), int(b[1]), int(t[0]), int(t[1])
        pygame.draw.ellipse(scr, dark, (bx - rx, by - ry, 2 * rx, 2 * ry))
        pygame.draw.rect(scr, col, (bx - rx, ty, 2 * rx, max(1, by - ty)))
        pygame.draw.rect(scr, shade(col, 0.82), (bx + rx // 3, ty, rx - rx // 3, max(1, by - ty)))
        pygame.draw.line(scr, dark, (bx - rx, ty), (bx - rx, by), 1)
        pygame.draw.line(scr, dark, (bx + rx, ty), (bx + rx, by), 1)
        pygame.draw.ellipse(scr, light, (tx - rx, ty - ry, 2 * rx, 2 * ry))

    @staticmethod
    def frame(bx, by, hs, vs, m, bob=0.0):
        def pt(X, Z):
            return (int(bx + X * hs), int(by - (Z + bob) * vs))

        def pm(X, Z):
            return pt(X * m, Z)
        return pt, pm

    def pop(s, x, y, v, col):
        if len(s.fxs) < 260:
            s.fxs.append({'k': 'num', 'x': x + random.randint(-14, 14), 'y': y, 'v': v, 'c': col,
                          't': 0.8, 'm': 0.8})

    def build_scenery(s):
        rnd = random.Random(11)
        s.camps = []
        for p in CAMPS:
            s.camps += [p, (WORLD - p[0], WORLD - p[1])]
        s.camps += [(2400, 2400), (1200, 1200)]

        def lane_d(x, y):
            return min(seg_dist(x, y, *p[i], *p[i + 1]) for p in LANES.values() for i in range(len(p) - 1))

        def free(x, y, lane_r, river_r):
            if lane_d(x, y) < lane_r or abs(x - y) / 1.414 < river_r:
                return False
            if any(math.hypot(x - bx, y - by) < 440 for bx, by in BASE_POS.values()):
                return False
            if any(math.hypot(x - cx, y - cy) < 190 for cx, cy in s.camps):
                return False
            for tw in TOWER_POS[BLUE] + TOWER_POS[RED]:
                if math.hypot(x - tw[0], y - tw[1]) < 120:
                    return False
            return True

        s.trees, s.rocks, s.tufts, s.patches, s.ripples = [], [], [], [], []
        n = 0
        while len(s.trees) < 230 and n < 8000:
            n += 1
            x, y = rnd.randint(80, WORLD - 80), rnd.randint(80, WORLD - 80)
            if free(x, y, 200, 160):
                s.trees.append((x, y, rnd.randint(80, 125), rnd.randint(0, 1)))
        for i in range(-60, WORLD + 120, 105):
            for (x, y) in ((i, 20 + rnd.randint(0, 50)), (i, WORLD - 20 - rnd.randint(0, 50)),
                           (20 + rnd.randint(0, 50), i), (WORLD - 20 - rnd.randint(0, 50), i)):
                s.trees.append((x, y, rnd.randint(120, 170), rnd.randint(0, 1)))
        n = 0
        while len(s.rocks) < 80 and n < 6000:
            n += 1
            x, y = rnd.randint(80, WORLD - 80), rnd.randint(80, WORLD - 80)
            if free(x, y, 160, 130):
                s.rocks.append((x, y, rnd.randint(30, 70), rnd.randint(1, 9)))
        for _ in range(3200):
            s.tufts.append((rnd.randint(0, WORLD), rnd.randint(0, WORLD), rnd.randint(0, 3)))
        for _ in range(240):
            f = rnd.choice([0.86, 0.92, 1.08, 1.14])
            s.patches.append((rnd.randint(0, WORLD), rnd.randint(0, WORLD), rnd.randint(90, 240),
                              shade((52, 112, 60), f)))
        for i in range(260):
            tt = rnd.randint(0, WORLD)
            o = rnd.randint(-70, 70)
            s.ripples.append((tt + o, tt - o, rnd.random() * 6.28))

    # --- vat the -----------------------------------------------------------------
    def draw_tree(s, scr, x, y, sz, tp):
        p = s.P(x, y)
        if not p or not (-200 < p[0] < W + 200 and -150 < p[1] < H + 300):
            return
        bx, by, k = int(p[0]), int(p[1]), p[2]
        h = sz * k
        sway = math.sin(s.t * 1.5 + x) * 2 * k
        rx = int(h * 0.5)
        pygame.draw.ellipse(scr, (30, 72, 42), (bx - rx + int(h * 0.15), by - int(rx * 0.3), 2 * rx, int(rx * 0.75)))
        pygame.draw.rect(scr, (92, 62, 40), (bx - int(h * 0.07), by - int(h * 0.5), int(h * 0.14), int(h * 0.5)))
        if tp == 0:
            for i in range(3):
                w = (0.62 - 0.14 * i) * h
                base = by - (0.28 + 0.34 * i) * h
                apex = base - 0.62 * h
                c = (28 + i * 10, 92 + i * 12, 52 + i * 6)
                pts = [(int(bx - w), int(base)), (int(bx + w), int(base)), (int(bx + sway * (i + 1) / 2), int(apex))]
                pygame.draw.polygon(scr, c, pts)
                pygame.draw.polygon(scr, shade(c, 1.35),
                                    [(int(bx), int(base)), (int(bx + w), int(base)), (int(bx + sway * (i + 1) / 2), int(apex))])
                pygame.draw.polygon(scr, shade(c, 0.6), pts, 1)
        else:
            for ox, oy, rr, c in ((-0.28, 0.72, 0.4, (40, 112, 55)), (0.28, 0.76, 0.38, (46, 122, 60)),
                                  (0.0, 1.0, 0.44, (56, 138, 68)), (-0.05, 0.78, 0.4, (50, 128, 62))):
                cx, cy = int(bx + ox * h + sway), int(by - oy * h)
                pygame.draw.circle(scr, c, (cx, cy), int(rr * h))
                pygame.draw.circle(scr, shade(c, 1.35), (cx - int(rr * h * 0.3), cy - int(rr * h * 0.3)), int(rr * h * 0.45))

    def draw_rock(s, scr, x, y, sz, seed):
        p = s.P(x, y)
        if not p or not (-100 < p[0] < W + 100 and -100 < p[1] < H + 200):
            return
        bx, by, k = p
        h = sz * k
        pts, top = [], []
        for i in range(7):
            a = i * 2 * math.pi / 7
            f = 0.75 + 0.35 * (((seed * (i + 3)) % 7) / 7)
            pts.append((int(bx + math.cos(a) * h * f), int(by + math.sin(a) * h * f * 0.45)))
            top.append((int(bx + math.cos(a) * h * f * 0.7), int(by - h * 0.55 + math.sin(a) * h * f * 0.3)))
        pygame.draw.polygon(scr, (96, 98, 108), pts + top[::-1])
        pygame.draw.polygon(scr, (60, 62, 70), pts, 2)
        pygame.draw.polygon(scr, (150, 152, 160), top)
        pygame.draw.polygon(scr, (70, 72, 80), top, 1)

    def draw_bush(s, scr, x, y, r):
        p = s.P(x, y)
        if not p or not (-100 < p[0] < W + 100 and -100 < p[1] < H + 200):
            return
        bx, by, k = p
        for i in range(5):
            a = i * 1.26
            cx, cy = int(bx + math.cos(a) * r * 0.5 * k), int(by - r * 0.35 * k + math.sin(a) * r * 0.25 * k)
            rr = max(3, int(r * 0.55 * k))
            pygame.draw.circle(scr, (30, 96, 46), (cx, cy), rr)
            pygame.draw.circle(scr, (62, 150, 72), (cx - rr // 3, cy - rr // 3), max(2, rr // 2))

    # --- cong trinh --------------------------------------------------------------
    def diamond(s, scr, cx, cy, w, h, col):
        pts = [(int(cx), int(cy - h)), (int(cx + w), int(cy)), (int(cx), int(cy + h)), (int(cx - w), int(cy))]
        pygame.draw.polygon(scr, col, pts)
        pygame.draw.polygon(scr, shade(col, 1.5), [pts[0], pts[1], (int(cx), int(cy))])
        pygame.draw.polygon(scr, shade(col, 0.55), pts, 2)

    def draw_tower(s, scr, u, bx, by, k):
        tc = TEAM_COL[u.team]
        t = s.t
        flash = max(0.0, (u.atk_cd - 0.9) / 0.3)
        if not u.base:
            rx = int(52 * k)
            pygame.draw.ellipse(scr, (26, 60, 34), (bx - rx + 8, by - int(rx * SP * 0.8), 2 * rx, int(2 * rx * SP * 0.9)))
            s.cyl(scr, u.x, u.y, 46, 14, (125, 122, 135))
            s.cyl(scr, u.x, u.y, 34, 104, (152, 148, 162), 10)
            s.cyl(scr, u.x, u.y, 35, 5, (98, 95, 108), 30)
            s.cyl(scr, u.x, u.y, 35, 8, tc, 58)
            s.cyl(scr, u.x, u.y, 36, 8, (98, 95, 108), 84)
            s.cyl(scr, u.x, u.y, 40, 10, (135, 130, 146), 104)
            s.cyl(scr, u.x, u.y, 28, 26, (112, 110, 124), 112)
            c = s.P(u.x, u.y, 168 + math.sin(t * 2 + u.x) * 4)
            if c:
                glow(scr, c[0], c[1], (30 + 22 * flash) * c[2] * 1.6, shade(tc, 0.55 + 0.45 * flash))
                s.diamond(scr, c[0], c[1], 8 * c[2] * (0.4 + abs(math.cos(t * 1.6))), 15 * c[2], shade(tc, 1.1))
            top = s.P(u.x, u.y, 215)
            if top:
                hpbar(scr, top[0], top[1], 56, u.hp / u.maxhp, (70, 200, 90) if u.team == s.player.team else (220, 60, 60), u.maxhp)
        else:
            rx = int(135 * k)
            pygame.draw.ellipse(scr, (26, 60, 34), (bx - rx + 10, by - int(rx * SP * 0.8), 2 * rx, int(2 * rx * SP * 0.9)))
            s.cyl(scr, u.x, u.y, 130, 18, (125, 122, 135))
            s.cyl(scr, u.x, u.y, 108, 10, tc, 18)
            s.cyl(scr, u.x, u.y, 96, 8, (100, 98, 112), 28)
            pil = []
            for i in range(6):
                a = i * math.pi / 3 + 0.5
                pil.append((math.sin(a), u.x + math.cos(a) * 90, u.y + math.sin(a) * 90))
            pil.sort()

            def pillars(sel):
                for sn, px, py in pil:
                    if sel(sn):
                        s.cyl(scr, px, py, 9, 80, (150, 146, 160), 30)
                        o = s.P(px, py, 118)
                        if o:
                            glow(scr, o[0], o[1], 16 * o[2] * 1.5, shade(tc, 0.7))
            pillars(lambda sn: sn < 0)
            c = s.P(u.x, u.y, 200 + math.sin(t * 1.5) * 8)
            if c:
                glow(scr, c[0], c[1], (95 + 40 * flash) * c[2], shade(tc, 0.6))
                s.diamond(scr, c[0], c[1], 34 * c[2] * (0.45 + abs(math.cos(t * 1.1))), 74 * c[2], shade(tc, 1.1))
                for i in range(3):
                    a = t * 1.3 + i * 2.1
                    sp_ = s.P(u.x + math.cos(a) * 62, u.y + math.sin(a) * 62, 205 + math.sin(t * 2 + i) * 12)
                    if sp_:
                        s.diamond(scr, sp_[0], sp_[1], 7 * sp_[2], 14 * sp_[2], shade(tc, 1.2))
            pillars(lambda sn: sn >= 0)
            top = s.P(u.x, u.y, 320)
            if top:
                hpbar(scr, top[0], top[1], 120, u.hp / u.maxhp, (70, 200, 90) if u.team == s.player.team else (220, 60, 60), u.maxhp)
                text(scr, "Nhà chính", 13, (255, 255, 255), (int(top[0]), int(top[1]) - 12), True, True)

    # --- tuong -------------------------------------------------------------------
    def draw_hero(s, scr, u, bx, by, k):
        d, col, role, name = u.d, u.d['col'], u.d['role'], u.name
        hsh = sum(ord(c) for c in name)
        skin, hair = SKINS[hsh % 4], HAIRS[hsh % 5]
        m = 1 if u.fx >= 0 else -1
        back = u.fy < -0.6
        hs, vs, t = k * 1.15, k * 1.05, s.t
        moving = u.mov > 0
        wph = u.walk * 3.0
        bob = abs(math.sin(wph)) * 2.5 if moving else math.sin(t * 3 + hsh) * 1.0
        pt, pm = s.frame(bx, by, hs, vs, m, bob)
        tc = TEAM_COL[u.team]
        rx = int(20 * hs)
        pygame.draw.ellipse(scr, (22, 52, 30), (bx - rx + int(5 * hs), by - int(rx * 0.3), 2 * rx, int(rx * 0.8)))
        glow(scr, bx, by, 38 * hs, shade(tc, 0.42 + 0.1 * math.sin(t * 3)))
        rr = int(27 * hs)
        pygame.draw.ellipse(scr, tc, (bx - rr, by - int(rr * SP), 2 * rr, int(2 * rr * SP)), 2)
        capec = shade((col[2], col[0], col[1]), 0.75)
        sway = math.sin(t * 4 + wph) * 3 - (4 if moving else 0)
        cape = role in ("Đấu sĩ", "Sát thủ", "Pháp sư", "Hỗ trợ")
        capepts = [pm(-11, 55), pm(11, 55), pm(14 + sway, 10), pm(-14 + sway, 8)]
        if cape and not back:
            pg(scr, capepts, capec)
        for sd in (-1, 1):
            lift = max(0.0, math.sin(wph + (0 if sd > 0 else math.pi))) * 6 if moving else 0
            x = sd * 5
            pg(scr, [pt(x - 3.5, lift + 6), pt(x + 3.5, lift + 6), pt(x + 3, lift + 25), pt(x - 3, lift + 25)], (72, 64, 84))
            pg(scr, [pt(x - 4.5, lift), pt(x + 5, lift), pt(x + 4.5, lift + 7), pt(x - 4, lift + 7)], shade(col, 0.45))
        sl = shade(col, 0.9)
        pygame.draw.line(scr, sl, pm(-12, 52), pm(-15, 37), max(3, int(5 * hs)))
        if role == "Xạ thủ" and not back:
            pg(scr, [pm(-9, 38), pm(-5, 38), pm(-5, 62), pm(-9, 62)], (110, 74, 44))
        pg(scr, [pt(-12, 14), pt(12, 14), pt(10, 25), pt(-10, 25)], shade(col, 0.8))
        pg(scr, [pt(-10, 24), pt(10, 24), pt(13, 54), pt(-13, 54)], col)
        pg(scr, [pt(-8, 30), pt(8, 30), pt(10, 50), pt(-10, 50)], shade(col, 1.2), None)
        pg(scr, [pt(-10, 24), pt(10, 24), pt(10, 29), pt(-10, 29)], (205, 170, 70))
        pygame.draw.circle(scr, tc, pt(0, 41), max(2, int(3.6 * hs)))
        for sd in (-1, 1):
            pygame.draw.circle(scr, shade(col, 1.25), pt(sd * 13, 54), max(3, int(6 * hs)))
            pygame.draw.circle(scr, shade(col, 0.5), pt(sd * 13, 54), max(3, int(6 * hs)), 1)
        hr = max(4, int(10 * hs))
        hc = pt(0, 67)
        if role == "Hỗ trợ":
            pg(scr, [pt(-10, 72), pt(10, 72), pt(11, 48), pt(-11, 48)], hair, None)
        if role == "Sát thủ":
            pygame.draw.circle(scr, shade(col, 0.45), hc, hr + 2)
        pygame.draw.circle(scr, skin, hc, hr)
        pygame.draw.circle(scr, (70, 46, 34), hc, hr, 1)
        arc = [pt(10 * math.cos(a * math.pi / 6), 67 + 10 * math.sin(a * math.pi / 6)) for a in range(0, 7)]
        if back:
            pygame.draw.circle(scr, hair if role in ("Hỗ trợ", "Xạ thủ") else shade(col, 0.6), hc, hr)
        else:
            e = max(1, int(1.6 * hs))
            pygame.draw.circle(scr, (20, 20, 20), pm(2.5, 66), e)
            pygame.draw.circle(scr, (20, 20, 20), pm(7, 66), e)
        if role == "Đấu sĩ":
            pg(scr, arc, shade(col, 0.7))
            pg(scr, [pm(-4, 76), pm(-17, 82), pm(-15, 66)], (220, 50, 50))
        elif role == "Sát thủ":
            pg(scr, [pt(-8, 62), pt(8, 62), pt(6, 56), pt(-6, 56)], shade(col, 0.4))
            pg(scr, arc, shade(col, 0.5))
        elif role == "Pháp sư":
            pg(scr, [pt(-13, 72), pt(13, 72), pt(2, 102)], shade(col, 0.6))
            pygame.draw.line(scr, (240, 210, 90), pt(-13, 72), pt(13, 72), max(2, int(3 * hs)))
        elif role == "Xạ thủ":
            pg(scr, arc, shade(col, 0.6))
            pygame.draw.line(scr, shade(col, 0.45), pm(4, 71), pm(15, 69), max(2, int(3 * hs)))
            pygame.draw.circle(scr, (140, 220, 255), pm(5, 68), max(2, int(2.5 * hs)))
        elif role == "Đỡ đòn":
            pg(scr, arc, (150, 150, 165))
            for sd in (-1, 1):
                pg(scr, [pt(sd * 9, 72), pt(sd * 18, 88), pt(sd * 12, 70)], (235, 230, 215))
        else:
            gp = pt(0, 86)
            glow(scr, gp[0], gp[1], 14 * hs, (120, 110, 40))
            pygame.draw.ellipse(scr, (255, 230, 120), (gp[0] - int(9 * hs), gp[1] - int(3 * hs), int(18 * hs), int(6 * hs)), 2)
        if cape and back:
            pg(scr, capepts, capec)
        # vu khi
        sw = max(0.0, u.swing / 0.35)
        p_ = 1 - sw
        a = math.radians(130 - 190 * p_) if sw > 0 else math.radians(72) + 0.1 * math.sin(t * 2)
        hx, hz = (14 + 10 * math.sin(p_ * math.pi), 46 - 8 * p_) if sw > 0 else (15, 40)
        hand = pm(hx, hz)
        pygame.draw.line(scr, sl, pm(12, 52), hand, max(3, int(5 * hs)))
        pygame.draw.circle(scr, skin, hand, max(2, int(3.5 * hs)))
        L = 30 + hsh % 12
        tip = pm(hx + L * math.cos(a), hz + L * math.sin(a))
        if role in ("Đấu sĩ", "Sát thủ"):
            if role == "Sát thủ":
                L = 17
                tip = pm(hx + L * math.cos(a), hz + L * math.sin(a))
                t2 = pm(-15 + 14 * math.cos(a + 0.9), 36 + 14 * math.sin(a + 0.9))
                pygame.draw.line(scr, (205, 210, 225), pm(-15, 36), t2, max(2, int(3 * hs)))
            pygame.draw.line(scr, (205, 210, 225), hand, tip, max(3, int(4.5 * hs)))
            pygame.draw.line(scr, (255, 255, 255), hand, tip, 1)
            g1 = pm(hx - math.sin(a) * 5, hz + math.cos(a) * 5)
            g2 = pm(hx + math.sin(a) * 5, hz - math.cos(a) * 5)
            pygame.draw.line(scr, (225, 185, 70), g1, g2, max(2, int(3 * hs)))
            if sw > 0:
                glow(scr, tip[0], tip[1], 22 * hs, shade(col, 0.8))
        elif role in ("Pháp sư", "Hỗ trợ"):
            tip = pm(hx + 46 * math.cos(a), hz + 46 * math.sin(a))
            pygame.draw.line(scr, (125, 88, 52), pm(hx - 8 * math.cos(a), hz - 8 * math.sin(a)), tip, max(2, int(3.2 * hs)))
            glow(scr, tip[0], tip[1], (13 + 14 * sw) * hs, shade(col, 1.1))
            pygame.draw.circle(scr, shade(col, 1.5), tip, max(3, int(5 * hs)))
            pygame.draw.circle(scr, (255, 255, 255), tip, max(1, int(2 * hs)))
        elif role == "Xạ thủ":
            pts = [pm(hx + 7 * (1 - (j / 4) ** 2), hz + j * 5) for j in range(-4, 5)]
            pygame.draw.lines(scr, (135, 92, 52), False, pts, max(2, int(3 * hs)))
            pygame.draw.line(scr, (235, 235, 235), pts[0], pts[-1], 1)
            if sw > 0:
                end = pm(hx + 34, hz)
                pygame.draw.line(scr, (255, 255, 255), pm(hx, hz), end, 2)
                glow(scr, end[0], end[1], 14 * hs, shade(col, 0.9))
        else:
            pygame.draw.line(scr, (118, 82, 50), hand, tip, max(3, int(4 * hs)))
            pygame.draw.circle(scr, (165, 165, 178), tip, max(3, int(7 * hs)))
            pygame.draw.circle(scr, (60, 60, 70), tip, max(3, int(7 * hs)), 1)
            sc_ = pm(-15, 38)
            pygame.draw.circle(scr, shade(col, 1.1), sc_, max(4, int(12 * hs)))
            pygame.draw.circle(scr, (235, 200, 90), sc_, max(4, int(12 * hs)), 2)
            pygame.draw.circle(scr, (235, 235, 235), sc_, max(2, int(3.5 * hs)))
        if role in ("Pháp sư", "Hỗ trợ") and u.d['sc'] == 'p':
            op = pt(-18 * m, 76 + math.sin(t * 3) * 3)
            glow(scr, op[0], op[1], 9 * hs, shade(tc, 0.7))

    def draw_minion(s, scr, u, bx, by, k):
        hs = vs = k * 0.95
        m = 1 if u.team == BLUE else -1
        tc = TEAM_COL[u.team]
        ph = s.t * 7 + (id(u) % 10)
        bob = abs(math.sin(ph)) * 1.5
        pt, pm = s.frame(bx, by, hs, vs, m, bob)
        rx = int(13 * hs)
        pygame.draw.ellipse(scr, (22, 52, 30), (bx - rx + 3, by - int(rx * 0.3), 2 * rx, int(rx * 0.8)))
        for sd in (-1, 1):
            lift = max(0.0, math.sin(ph + (0 if sd > 0 else math.pi))) * 3
            pg(scr, [pt(sd * 3 - 2, lift), pt(sd * 3 + 2, lift), pt(sd * 3 + 2, lift + 11), pt(sd * 3 - 2, lift + 11)], (70, 60, 50), None)
        pg(scr, [pt(-7, 10), pt(7, 10), pt(8, 28), pt(-8, 28)], shade(tc, 0.85))
        pg(scr, [pt(-7, 10), pt(7, 10), pt(7, 14), pt(-7, 14)], (180, 150, 70), None)
        hc = pt(0, 33)
        r = max(3, int(6.5 * hs))
        pygame.draw.circle(scr, (235, 205, 170), hc, r)
        pg(scr, [pt(6.5 * math.cos(a * math.pi / 6), 33 + 6.5 * math.sin(a * math.pi / 6)) for a in range(0, 7)], tc)
        pygame.draw.circle(scr, (20, 20, 20), pm(2.5, 32), 1)
        sw = max(0.0, (u.atk_cd - 0.85) / 0.25)
        a = math.radians(125 - 170 * (1 - sw)) if sw > 0 else math.radians(70)
        hand = pm(9, 20)
        if u.ranged:
            tip = pm(9 + 26 * math.cos(a), 20 + 26 * math.sin(a))
            pygame.draw.line(scr, (120, 85, 50), hand, tip, 2)
            glow(scr, tip[0], tip[1], 10 * hs, shade(tc, 0.9))
            pygame.draw.circle(scr, (255, 255, 255), tip, max(2, int(3 * hs)))
        else:
            tip = pm(9 + 16 * math.cos(a), 20 + 16 * math.sin(a))
            pygame.draw.line(scr, (205, 210, 225), hand, tip, max(2, int(3 * hs)))
            sc_ = pm(-9, 20)
            pygame.draw.circle(scr, tc, sc_, max(3, int(6 * hs)))
            pygame.draw.circle(scr, (240, 240, 240), sc_, max(3, int(6 * hs)), 1)

    def draw_monster(s, scr, u, bx, by, k):
        sz = u.r / 24.0
        hs = vs = k * sz
        m = 1 if math.sin(s.t * 0.4 + u.x) >= 0 else -1
        t = s.t
        pt, pm = s.frame(bx, by, hs, vs, m, math.sin(t * 2 + u.x) * 1.5)
        rx = int(24 * hs)
        pygame.draw.ellipse(scr, (22, 52, 30), (bx - rx + 4, by - int(rx * 0.3), 2 * rx, int(rx * 0.8)))
        if u.name == "Rồng Cổ" or u.name == "Bạo Chúa":
            dr = u.name == "Rồng Cổ"
            body = (40, 150, 120) if dr else (130, 50, 160)
            belly = (150, 220, 170) if dr else (210, 130, 190)
            flap = math.sin(t * 4) * 10
            wing = shade(body, 0.7)
            pg(scr, [pm(-4, 42), pm(-30, 78 + flap), pm(-22, 56), pm(-40, 66 + flap), pm(-12, 38)], wing)
            pg(scr, [pm(4, 42), pm(24, 80 + flap), pm(14, 58), pm(34, 70 + flap), pm(10, 38)], shade(wing, 1.2))
            pg(scr, [pm(-14, 14), pm(-48, 10 + math.sin(t * 2) * 6), pm(-14, 28)], shade(body, 0.8))
            for sd in (-1, 1):
                pg(scr, [pt(sd * 10 - 5, 0), pt(sd * 10 + 5, 0), pt(sd * 10 + 4, 20), pt(sd * 10 - 4, 20)], shade(body, 0.7))
            bc = pt(0, 30)
            pygame.draw.ellipse(scr, body, (bc[0] - int(30 * hs), bc[1] - int(22 * vs), int(60 * hs), int(44 * vs)))
            pygame.draw.ellipse(scr, belly, (bc[0] - int(18 * hs) + m * int(8 * hs), bc[1] - int(4 * vs), int(30 * hs), int(24 * vs)))
            pg(scr, [pm(14, 40), pm(32, 62), pm(40, 58), pm(24, 36)], body)
            hd = pm(34, 62)
            pygame.draw.ellipse(scr, shade(body, 1.1), (hd[0] - int(13 * hs), hd[1] - int(9 * vs), int(26 * hs), int(18 * vs)))
            for sd in (0, 1):
                pg(scr, [pm(30 + sd * 6, 68), pm(26 + sd * 10, 86), pm(36 + sd * 6, 70)], (235, 230, 200))
            ey = pm(38, 65)
            glow(scr, ey[0], ey[1], 10 * hs, (180, 160, 30))
            pygame.draw.circle(scr, (255, 240, 90), ey, max(2, int(3 * hs)))
            if u.atk_cd > 0.8:
                fp = pm(50, 60)
                glow(scr, fp[0], fp[1], 34 * hs, (230, 110, 30))
            for i in range(5):
                sx_ = -16 + i * 8
                pg(scr, [pm(sx_ - 3, 50 - abs(sx_) * 0.2), pm(sx_, 60 - abs(sx_) * 0.2), pm(sx_ + 3, 50 - abs(sx_) * 0.2)], shade(body, 0.6), None)
            top = pt(0, 100)
            hpbar(scr, top[0], top[1], 70, u.hp / u.maxhp, (230, 170, 50), u.maxhp)
            text(scr, u.name, 15, (255, 255, 255), (top[0], top[1] - 12), True, True)
            return
        for sd in (-1, 1):
            pg(scr, [pt(sd * 9 - 3, 0), pt(sd * 9 + 3, 0), pt(sd * 9 + 3, 9), pt(sd * 9 - 3, 9)], (80, 52, 34), None)
        pg(scr, [pm(-14, 14), pm(-26, 20 + math.sin(t * 5) * 4), pm(-13, 20)], (130, 90, 56))
        bc = pt(0, 17)
        pygame.draw.ellipse(scr, (150, 100, 62), (bc[0] - int(19 * hs), bc[1] - int(13 * vs), int(38 * hs), int(26 * vs)))
        pygame.draw.ellipse(scr, (200, 160, 110), (bc[0] - int(10 * hs), bc[1] - int(2 * vs), int(22 * hs), int(13 * vs)))
        hd = pm(14, 25)
        pygame.draw.circle(scr, (165, 112, 70), hd, max(3, int(9 * hs)))
        pg(scr, [pm(10, 31), pm(8, 40), pm(14, 33)], (235, 230, 210), None)
        pg(scr, [pm(17, 31), pm(21, 41), pm(20, 32)], (235, 230, 210), None)
        pg(scr, [pm(20, 22), pm(25, 15), pm(22, 24)], (245, 245, 235), None)
        ey = pm(17, 27)
        glow(scr, ey[0], ey[1], 6 * hs, (150, 30, 30))
        pygame.draw.circle(scr, (255, 70, 60), ey, max(1, int(2 * hs)))
        top = pt(0, 46)
        hpbar(scr, top[0], top[1], 50, u.hp / u.maxhp, (230, 170, 50), u.maxhp)

    def draw_unit3(s, scr, u):
        p = s.P(u.x, u.y)
        if not p or not (-250 < p[0] < W + 250 and -200 < p[1] < H + 350):
            return
        bx, by, k = int(p[0]), int(p[1]), p[2]
        ally = u.team == s.player.team
        hpcol = (70, 200, 90) if ally else (220, 60, 60)
        if u.kind == "hero":
            s.draw_hero(scr, u, bx, by, k)
            top = s.P(u.x, u.y, 118)
            if top:
                tx, ty = int(top[0]), int(top[1])
                hpbar(scr, tx, ty, 66, u.hp / u.maxhp, hpcol, u.maxhp)
                if u.shield > 0:
                    pygame.draw.rect(scr, (140, 230, 255), (tx - 33, ty - 3, int(66 * min(1, u.shield / u.maxhp)), 3))
                pygame.draw.circle(scr, (20, 24, 44), (tx - 41, ty + 3), 10)
                pygame.draw.circle(scr, TEAM_COL[u.team], (tx - 41, ty + 3), 10, 2)
                text(scr, str(u.level), 12, (255, 255, 255), (tx - 41, ty + 3), True, True)
                text(scr, u.name, 12, (255, 255, 255), (tx, ty - 11), True)
                if u.stun > 0:
                    text(scr, "CHOÁNG", 12, (255, 230, 80), (tx, ty - 25), True, True)
            if u.recall > 0:
                glow(scr, bx, by, 60 * k, (60, 120, 200))
                text(scr, "Hồi thành %.1f" % u.recall, 12, (150, 220, 255), (bx, by + 30), True)
        elif u.kind == "minion":
            s.draw_minion(scr, u, bx, by, k)
            top = s.P(u.x, u.y, 48)
            if top:
                bar(scr, int(top[0] - 16), int(top[1]), 32, 4, u.hp / u.maxhp, hpcol)
        elif u.kind == "tower":
            s.draw_tower(scr, u, bx, by, k)
        else:
            s.draw_monster(scr, u, bx, by, k)

    # --- ve toan canh -------------------------------------------------------------
    def draw_world(s, scr):
        if not hasattr(s, 'trees'):
            s.build_scenery()
        Pl = s.player
        s.ct = (max(300, min(WORLD - 300, Pl.x)), max(300, min(WORLD - 300, Pl.y)))
        s.cam = (Pl.x - W / 2, Pl.y - H / 2)
        t = s.t
        tx, ty = s.ct
        scr.fill((12, 24, 18))
        s.draw_poly(scr, [(0, 0), (WORLD, 0), (WORLD, WORLD), (0, WORLD)], (52, 112, 60))
        for x, y, r, c in s.patches:
            if abs(x - tx) < 1800 and abs(y - ty) < 1800:
                s.draw_poly(scr, circle_pts(x, y, r, 9), c)
        for x, y in s.camps:
            if abs(x - tx) < 1800 and abs(y - ty) < 1800:
                s.draw_poly(scr, circle_pts(x, y, 150, 14), (104, 88, 58))
                s.draw_poly(scr, circle_pts(x, y, 150, 14), (84, 70, 46), 0, 3)
        for x, y, c in ([] if LOW else s.tufts):
            if abs(x - tx) < 1300 and abs(y - ty) < 1200:
                p = s.P(x, y)
                if p and 0 < p[0] < W and 0 < p[1] < H:
                    h = (5 + c * 2) * p[2]
                    col = (70 + c * 12, 150 + c * 10, 78)
                    pygame.draw.line(scr, col, (int(p[0]), int(p[1])), (int(p[0] - 2 * p[2]), int(p[1] - h)), 1)
                    pygame.draw.line(scr, col, (int(p[0]), int(p[1])), (int(p[0] + 2 * p[2]), int(p[1] - h * 0.8)), 1)
        s.draw_poly(scr, quad(150, 150, 3450, 3450, 120), (150, 160, 130))
        s.draw_poly(scr, quad(150, 150, 3450, 3450, 98), (66, 128, 196))
        s.draw_poly(scr, quad(150, 150, 3450, 3450, 52), (52, 108, 180))
        for x, y, ph in ([] if LOW else s.ripples):
            if abs(x - tx) < 1400 and abs(y - ty) < 1300:
                dx = math.sin(t * 1.4 + ph) * 12
                a, b = s.P(x + dx - 20, y), s.P(x + dx + 20, y)
                if a and b:
                    pygame.draw.line(scr, (170, 215, 240), (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 2)
        for team, col in ((BLUE, (54, 76, 140)), (RED, (130, 58, 58))):
            bx, by = BASE_POS[team]
            if abs(bx - tx) < 2000 and abs(by - ty) < 1900:
                tc = TEAM_COL[team]
                s.draw_poly(scr, circle_pts(bx, by, 340, 40), col)
                s.draw_poly(scr, circle_pts(bx, by, 330, 40), shade(tc, 0.7), 0, 4)
                s.draw_poly(scr, circle_pts(bx, by, 250, 36), shade(tc, 0.5), 0, 3)
                for i in range(12):
                    a = i * math.pi / 6
                    s.draw_poly(scr, circle_pts(bx + math.cos(a) * 290, by + math.sin(a) * 290, 12, 8), shade(tc, 1.0))
                for i in range(3):
                    r = 70 + (t * 45 + i * 55) % 165
                    s.draw_poly(scr, circle_pts(bx, by, r, 30), shade((150, 210, 255), 1 - r / 260), 1, 2)
        for pts in LANES.values():
            for i in range(len(pts) - 1):
                x1, y1 = pts[i]
                x2, y2 = pts[i + 1]
                L = math.hypot(x2 - x1, y2 - y1)
                nx, ny = -(y2 - y1) / L, (x2 - x1) / L
                s.draw_poly(scr, quad(x1, y1, x2, y2, 62), (140, 118, 82))
                s.draw_poly(scr, quad(x1, y1, x2, y2, 52), (176, 154, 108))
                s.draw_poly(scr, quad(x1, y1, x2, y2, 24), (186, 166, 120))
                for sg in (-1, 1):
                    s.draw_poly(scr, quad(x1 + nx * 58 * sg, y1 + ny * 58 * sg, x2 + nx * 58 * sg, y2 + ny * 58 * sg, 5), (108, 90, 64))
                d = 0
                while d < L:
                    px, py = x1 + (x2 - x1) * d / L, y1 + (y2 - y1) * d / L
                    if abs(px - tx) < 1500 and abs(py - ty) < 1300:
                        a, b = s.P(px - nx * 52, py - ny * 52), s.P(px + nx * 52, py + ny * 52)
                        if a and b:
                            pygame.draw.line(scr, (150, 128, 90), (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1)
                    d += 130
            for q in pts:
                s.draw_poly(scr, circle_pts(q[0], q[1], 62, 16), (176, 154, 108))
        for f in s.fxs:
            if f['k'] == 'ring':
                a = f['t'] / f['m']
                col = tuple(int(c * (0.4 + 0.6 * a)) for c in f['c'])
                s.draw_poly(scr, circle_pts(f['x'], f['y'], max(5, f['r']), 28), shade(col, 0.5), 3, 0)
                s.draw_poly(scr, circle_pts(f['x'], f['y'], max(5, f['r']), 28), col, 3, 4)
        items = []
        for x, y, sz, tp in s.trees:
            if abs(x - tx) < VR and abs(y - ty) < VR2:
                items.append((y, 0, (x, y, sz, tp)))
        for x, y, sz, sd in s.rocks:
            if abs(x - tx) < VR and abs(y - ty) < VR2:
                items.append((y, 1, (x, y, sz, sd)))
        for x, y, r in s.bushes:
            if abs(x - tx) < VR and abs(y - ty) < VR2:
                items.append((y, 2, (x, y, r)))
        for u in s.units:
            if u.alive:
                items.append((u.y + 0.5, 3, u))
        items.sort(key=lambda i: i[0])
        for _, kd, o in items:
            if kd == 0:
                s.draw_tree(scr, *o)
            elif kd == 1:
                s.draw_rock(scr, *o)
            elif kd == 2:
                s.draw_bush(scr, *o)
            else:
                s.draw_unit3(scr, o)
        for p in s.projs:
            a, b = s.P(p.x, p.y, 0), s.P(p.x, p.y, 48)
            if a and b:
                pygame.draw.ellipse(scr, (22, 52, 30), (int(a[0] - 8 * a[2]), int(a[1] - 4 * a[2]),
                                                        int(16 * a[2]), max(2, int(8 * a[2]))))
                tr = s.P(p.x - p.vx * 0.05, p.y - p.vy * 0.05, 48)
                if tr:
                    pygame.draw.line(scr, shade(p.col, 0.8), (int(tr[0]), int(tr[1])), (int(b[0]), int(b[1])), max(3, int(8 * b[2])))
                glow(scr, b[0], b[1], 30 * b[2], p.col)
                pygame.draw.circle(scr, (255, 255, 255), (int(b[0]), int(b[1])), max(3, int(7 * b[2])))
        for f in s.fxs:
            if f['k'] == 'line':
                a, b = s.P(f['a'][0], f['a'][1], 45), s.P(f['b'][0], f['b'][1], 45)
                if a and b:
                    al = f['t'] / f['m']
                    pygame.draw.line(scr, shade(f['c'], 0.5 * al + 0.2), (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 9)
                    pygame.draw.line(scr, (255, 255, 255), (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 3)
            elif f['k'] == 'num':
                al = f['t'] / f['m']
                p = s.P(f['x'], f['y'], 90 + (1 - al) * 70)
                if p:
                    text(scr, str(f['v']), 20, f['c'], (int(p[0]), int(p[1])), True, True)
        if not LOW:
            scr.blit(vignette(), (0, 0))

    def draw_minimap(self, scr):
        k = 200 / WORLD
        ox, oy = W - 210, 10
        pygame.draw.rect(scr, (30, 70, 40), (ox, oy, 200, 200))
        pygame.draw.line(scr, (70, 130, 195), (ox, oy), (ox + 200, oy + 200), 8)
        for pts in LANES.values():
            pygame.draw.lines(scr, (172, 150, 104), False,
                              [(ox + x * k, oy + y * k) for x, y in pts], 6)
        for u in self.units:
            if not u.alive or u.kind == "monster" and not u.boss:
                continue
            x, y = ox + u.x * k, oy + u.y * k
            col = TEAM_COL[u.team]
            if u.kind == "hero":
                pygame.draw.circle(scr, col, (int(x), int(y)), 5)
                if u is self.player:
                    pygame.draw.circle(scr, (255, 255, 255), (int(x), int(y)), 7, 2)
            elif u.kind == "tower":
                pygame.draw.rect(scr, col, (x - 4, y - 4, 8, 8))
            elif u.kind == "minion":
                pygame.draw.circle(scr, col, (int(x), int(y)), 1)
            else:
                pygame.draw.circle(scr, (255, 230, 100), (int(x), int(y)), 4)
        cx, cy = self.cam
        pygame.draw.rect(scr, (255, 255, 255), (ox + cx * k, oy + cy * k, W * k, H * k), 1)
        pygame.draw.rect(scr, (255, 255, 255), (ox, oy, 200, 200), 2)

    def draw_hud(s, scr):
        P = s.player
        s.draw_minimap(scr)
        mm, ss = divmod(int(s.t), 60)
        pygame.draw.rect(scr, (20, 20, 30), (W // 2 - 130, 6, 260, 34), border_radius=8)
        text(scr, str(s.score[0]), 22, TEAM_COL[BLUE], (W // 2 - 90, 23), True, True)
        text(scr, "%02d:%02d" % (mm, ss), 20, (255, 255, 255), (W // 2, 23), True, True)
        text(scr, str(s.score[1]), 22, TEAM_COL[RED], (W // 2 + 90, 23), True, True)
        if s.buff[BLUE] > 0:
            text(scr, "Cường hóa phe Xanh: %ds" % s.buff[BLUE], 14, (140, 190, 255), (W // 2, 46), True)
        if s.buff[RED] > 0:
            text(scr, "Cường hóa phe Đỏ: %ds" % s.buff[RED], 14, (255, 150, 150), (W // 2, 62), True)
        for i, (m, _) in enumerate(s.feed):
            text(scr, m, 15, (255, 255, 255), (16, 14 + i * 20))
        # thanh trang thai
        bar(scr, 330, 676, 520, 18, P.hp / P.maxhp, (70, 200, 90))
        text(scr, "%d / %d" % (P.hp, P.maxhp), 13, (255, 255, 255), (590, 685), True, True)
        bar(scr, 330, 698, 520, 6, P.xp / (120 + 70 * P.level), (120, 140, 255))
        text(scr, "%s  Lv %d" % (P.name, P.level), 16, (255, 255, 255), (330, 650), False, True)
        text(scr, "Vàng: %d   Hạ: %d/%d" % (P.gold, P.kills, P.deaths), 16, (255, 220, 90), (560, 650))
        it = "  ".join("%s x%d" % (ITEM_LABEL[ITEMS[i][1]], P.items[i]) for i in range(4) if P.items[i])
        text(scr, it, 13, (200, 220, 255), (330, 628))
        if P.shield > 0:
            text(scr, "Khiên %d" % P.shield, 13, (140, 230, 255), (760, 650))
        if P.in_base() and P.alive:
            pygame.draw.rect(scr, (20, 20, 30), (16, 230, 300, 136), border_radius=8)
            text(scr, "CỬA HÀNG (phím 1-4)", 15, (255, 220, 90), (28, 238), False, True)
            for i, (n, st, v, c) in enumerate(ITEMS):
                text(scr, "%d. %s +%d %s  -  %d vàng" % (i + 1, n, v, ITEM_LABEL[st], P.cost(i)),
                     14, (230, 230, 230) if P.gold >= P.cost(i) else (140, 140, 140),
                     (28, 266 + i * 24))
        text(scr, "WASD di chuyển | SPACE đánh | Q E R kỹ năng | F hồi máu | G tốc biến | B về thành | ESC thoát",
             12, (230, 230, 230), (330, 708))
        # can analog
        pygame.draw.circle(scr, (255, 255, 255), JC, 95, 3)
        st = s.inp['stick']
        kx, ky = (JC[0] + st[0], JC[1] + st[1]) if st else JC
        pygame.draw.circle(scr, (255, 255, 255), (int(kx), int(ky)), 34)
        # nut bam
        cds = {"s1": P.cd[0], "s2": P.cd[1], "s3": P.cd[2], "heal": P.heal_cd, "flash": P.flash_cd,
               "recall": 0, "atk": 0}
        lab = {"atk": "ĐÁNH", "s1": "Q", "s2": "E", "s3": "R", "heal": "F", "flash": "G", "recall": "B"}
        for k, (bx, by, br) in BTN.items():
            c = cds[k]
            if k == "recall" and P.recall > 0:
                c = P.recall
            pygame.draw.circle(scr, (25, 25, 35) if c > 0 else P.d['col'], (bx, by), br)
            pygame.draw.circle(scr, (255, 255, 255), (bx, by), br, 3)
            text(scr, lab[k], 18 if br > 30 else 14, (255, 255, 255), (bx, by), True, True)
            if c > 0:
                text(scr, str(int(math.ceil(c))), 18, (255, 220, 90), (bx, by - br - 12), True, True)
        if not P.alive:
            pygame.draw.rect(scr, (0, 0, 0), (W // 2 - 190, H // 2 - 40, 380, 80), border_radius=10)
            text(scr, "Hồi sinh sau %d giây" % math.ceil(max(0, P.respawn)), 26,
                 (255, 255, 255), (W // 2, H // 2), True, True)
        if s.over is not None:
            pygame.draw.rect(scr, (0, 0, 0), (W // 2 - 300, H // 2 - 90, 600, 180), border_radius=14)
            win = s.over == s.player.team
            text(scr, "CHIẾN THẮNG!" if win else "THẤT BẠI", 56,
                 (120, 255, 150) if win else (255, 110, 110), (W // 2, H // 2 - 30), True, True)
            text(scr, "R: chơi lại   |   ESC: về màn hình chọn tướng", 20, (255, 255, 255),
                 (W // 2, H // 2 + 40), True)


JC = (150, 570)
BTN = {"atk": (1150, 590, 56), "s1": (1030, 640, 38), "s2": (1050, 545, 38),
       "s3": (1120, 470, 38), "heal": (960, 675, 26), "flash": (1230, 490, 26),
       "recall": (1230, 430, 26)}


def btn_at(pos):
    for k, (x, y, r) in BTN.items():
        if math.hypot(pos[0] - x, pos[1] - y) <= r + 6:
            return k
    return None


# ----------------------------------------------------------------------------
# Man hinh chon tuong
# ----------------------------------------------------------------------------
CARD_W, CARD_H = 195, 88
CARDS = [pygame.Rect(25 + (i % 6) * 205, 110 + (i // 6) * 98, CARD_W, CARD_H)
         for i in range(len(HEROES))]
START = pygame.Rect(540, 650, 200, 52)


def draw_menu(scr, sel):
    scr.fill((18, 24, 40))
    text(scr, "ĐẤU TRƯỜNG ANH HÙNG", 40, (255, 220, 90), (W // 2, 40), True, True)
    text(scr, "MOBA 5v5 offline - chọn tướng của bạn", 18, (200, 210, 230), (W // 2, 84), True)
    for i, r in enumerate(CARDS):
        h = HEROES[i]
        pygame.draw.rect(scr, (34, 42, 66), r, border_radius=10)
        pygame.draw.circle(scr, h['col'], (r.x + 38, r.y + 44), 26)
        text(scr, h['name'][0], 24, (255, 255, 255), (r.x + 38, r.y + 44), True, True)
        text(scr, h['name'], 15, (255, 255, 255), (r.x + 74, r.y + 24), False, True)
        text(scr, h['role'], 14, (170, 190, 230), (r.x + 74, r.y + 50))
        if i == sel:
            pygame.draw.rect(scr, (255, 220, 90), r, 4, border_radius=10)
    h = HEROES[sel]
    pygame.draw.rect(scr, (28, 34, 54), (25, 420, 1230, 215), border_radius=12)
    text(scr, "%s  -  %s" % (h['name'], h['role']), 26, (255, 255, 255), (50, 436), False, True)
    text(scr, "Máu %d | Công %d | Phép %d | Tầm đánh %d | Tốc độ %d" %
         (h['hp'], h['atk'], h['ap'], h['rng'], h['spd']), 16, (200, 220, 255), (50, 474))
    for i, sk in enumerate(h['sk']):
        text(scr, "%s: %s  [%s, hồi %ss]" % ("QWE"[i], sk['n'], TYPE_VI[sk['t']], sk['cd']),
             17, (255, 235, 170), (50, 510 + i * 32))
    pygame.draw.rect(scr, (60, 150, 80), START, border_radius=12)
    text(scr, "BẮT ĐẦU", 22, (255, 255, 255), START.center, True, True)


# ----------------------------------------------------------------------------
def main():
    # Mac dinh xoay ngang tu dong (Android/iOS chi cho phep 2 huong ngang), tu chinh sang toan man hinh tren di dong
    os.environ.setdefault("SDL_IOS_ORIENTATIONS", "LandscapeLeft LandscapeRight")
    os.environ.setdefault("SDL_HINT_ORIENTATIONS", "LandscapeLeft LandscapeRight")
    pygame.init()
    mobile = "ANDROID_ARGUMENT" in os.environ or hasattr(sys, "getandroidapilevel")
    flags = pygame.SCALED | pygame.RESIZABLE | (pygame.FULLSCREEN if mobile else 0)
    scr = pygame.display.set_mode((W, H), flags)  # SCALED: giu ti le 16:9 ngang, tu co gian/letterbox
    pygame.display.set_caption("Đấu Trường Anh Hùng 3D HD - MOBA offline")
    clock = pygame.time.Clock()
    state, sel, game = "menu", 0, None
    fingers, touch_mode = {}, False
    while True:
        if android is not None and hasattr(android, "check_pause") and android.check_pause():
            android.wait_for_resume()
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # --- DA CHAM: moi ngon tay co mot finger_id rieng ---
            if ev.type == pygame.FINGERDOWN:
                touch_mode = True
                pos = (ev.x * W, ev.y * H)
                fingers[ev.finger_id] = pos
                ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)
            elif ev.type == pygame.FINGERMOTION:
                fingers[ev.finger_id] = (ev.x * W, ev.y * H)
                continue
            elif ev.type == pygame.FINGERUP:
                fingers.pop(ev.finger_id, None)
                continue
            elif touch_mode and ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                continue
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
                continue
            if state == "menu":
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    for i, r in enumerate(CARDS):
                        if r.collidepoint(ev.pos):
                            sel = i
                    if START.collidepoint(ev.pos):
                        game, state = Game(sel), "play"
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_RETURN:
                        game, state = Game(sel), "play"
                    elif ev.key == pygame.K_RIGHT:
                        sel = (sel + 1) % len(HEROES)
                    elif ev.key == pygame.K_LEFT:
                        sel = (sel - 1) % len(HEROES)
                    elif ev.key == pygame.K_DOWN:
                        sel = (sel + 6) % len(HEROES)
                    elif ev.key == pygame.K_UP:
                        sel = (sel - 6) % len(HEROES)
                    elif ev.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            else:
                P = game.player
                if ev.type == pygame.KEYDOWN:
                    k = ev.key
                    if k == pygame.K_ESCAPE:
                        state = "menu"
                    elif k == pygame.K_r and game.over is not None:
                        game = Game(sel)
                    elif k == pygame.K_q:
                        P.cast(0, game)
                    elif k == pygame.K_e:
                        P.cast(1, game)
                    elif k == pygame.K_r:
                        P.cast(2, game)
                    elif k == pygame.K_f:
                        P.heal_spell(game)
                    elif k == pygame.K_g:
                        P.flash(game)
                    elif k == pygame.K_b:
                        P.start_recall()
                    elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        P.buy(k - pygame.K_1)
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    b = btn_at(ev.pos)
                    if b == "s1":
                        P.cast(0, game)
                    elif b == "s2":
                        P.cast(1, game)
                    elif b == "s3":
                        P.cast(2, game)
                    elif b == "heal":
                        P.heal_spell(game)
                    elif b == "flash":
                        P.flash(game)
                    elif b == "recall":
                        P.start_recall()
        if state == "menu":
            draw_menu(scr, sel)
        else:
            keys = pygame.key.get_pressed()
            mx = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
            my = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
            if touch_mode:
                pts = list(fingers.values())
            else:
                mp, mb = pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]
                pts = [mp] if mb else []
            stick = None
            ax, ay, ar = BTN["atk"]
            atk = bool(keys[pygame.K_SPACE])
            got_stick = False
            for p in pts:  # dong thoi: 1 ngon tay cho can analog, ngon khac cho nut danh/ky nang
                if math.hypot(p[0] - ax, p[1] - ay) < ar + 10:
                    atk = True
                elif not got_stick and math.hypot(p[0] - JC[0], p[1] - JC[1]) < 190:
                    vx, vy = p[0] - JC[0], p[1] - JC[1]
                    l = math.hypot(vx, vy)
                    if l > 12:
                        mx, my = vx / l, vy / l
                        k = min(l, 90) / l
                        stick = (vx * k, vy * k)
                        got_stick = True
            game.inp = {'move': (mx, my), 'atk': atk, 'stick': stick}
            game.update(dt)
            game.draw_world(scr)
            game.draw_hud(scr)
        pygame.display.flip()


if __name__ == "__main__":
    main()

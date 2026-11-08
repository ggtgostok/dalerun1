import pygame, random, sys, math, json, os

from array import array

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

_info = pygame.display.Info()
try:
    _k = min(1.0, 600 / min(_info.current_w, _info.current_h))
    if _k <= 0:
        raise ValueError
    screen = pygame.display.set_mode((int(_info.current_w * _k), int(_info.current_h * _k)),
                                     pygame.SCALED | pygame.FULLSCREEN)
except Exception:
    screen = pygame.display.set_mode((0, 0))
W, H = screen.get_size()
clock = pygame.time.Clock()


def F(k):
    return pygame.font.SysFont(None, int(H * k))


f_s, f_m, f_b = F(0.032), F(0.05), F(0.09)


def _ov(a):
    o = pygame.Surface((W, H), pygame.SRCALPHA)
    o.fill((0, 0, 0, a))
    return o


OV90, OV160 = _ov(90), _ov(160)

HOR = H * 0.25
PY = H * 0.82
SPREAD = W * 0.30
TRAIN_H = H * 0.30     # высота поезда (обычный персонаж не допрыгивает)
PLAT_H = H * 0.10      # высота плиты в режиме «Лава»
TOL = H * 0.035        # допуск при приземлении
G = H * 5              # гравитация
DW = 0.025             # глубина «тела» игрока
SAVE = os.path.join(os.environ.get("ANDROID_PRIVATE", "."), "subway_save.json")

SPRINT_D = 40.0        # длина дистанции в режиме «Спринт»
CRATE_PRICE = 500

# ------------------------------------------------------------ ДАННЫЕ
CHARS = [
    dict(n="Макс", body=(40, 120, 255), skin=(255, 220, 180), acc=(255, 60, 60), hat="cap", price=0, desc="Классика. Без бонусов"),
    dict(n="Лиза", body=(255, 105, 180), skin=(255, 224, 189), acc=(255, 255, 255), hat="band", price=30, desc="Прыжок +20%. Перепрыгивает поезда", j=1.2),
    dict(n="Дима", body=(60, 180, 75), skin=(235, 190, 150), acc=(30, 90, 30), hat="cap", price=60, desc="Скорость растёт медленнее", ramp=0.6),
    dict(n="Ниндзя", body=(35, 35, 45), skin=(255, 220, 180), acc=(220, 30, 30), hat="mask", price=100, desc="Кувырок длится дольше", r=1.8),
    dict(n="Робот", body=(150, 160, 175), skin=(190, 200, 215), acc=(0, 220, 255), hat="antenna", price=150, desc="Прыжок +15%, медленный разгон. Перепрыгивает поезда", j=1.15, ramp=0.7),
    dict(n="Пират", body=(130, 80, 40), skin=(240, 200, 160), acc=(25, 25, 25), hat="pirate", price=200, desc="Монеты ×2", c=2),
    dict(n="Космонавт", body=(240, 240, 245), skin=(255, 220, 180), acc=(255, 140, 0), hat="helmet", price=280, desc="Прыжок +40%. Перепрыгивает поезда", j=1.4),
    dict(n="Клоун", body=(150, 60, 200), skin=(255, 235, 215), acc=(255, 220, 0), hat="clown", price=380, desc="Монеты ×2 и длинный кувырок", c=2, r=1.5),
    dict(n="Зомби", body=(70, 90, 60), skin=(140, 190, 110), acc=(90, 20, 20), hat="zombie", price=500, desc="Очки +30%, медленный разгон", sm=1.3, ramp=0.7),
    dict(n="Король", body=(120, 30, 160), skin=(255, 220, 180), acc=(255, 210, 0), hat="crown", price=800, desc="Прыжок +20%, кувырок, монеты ×2, медленный разгон. Перепрыгивает поезда", j=1.2, r=1.3, c=2, ramp=0.7),
    dict(n="Котик", body=(255, 150, 50), skin=(255, 190, 110), acc=(255, 120, 160), hat="ears", price=150, desc="Магнит: собирает монеты с соседних дорожек", mag=1),
    dict(n="Чёртик", body=(200, 30, 40), skin=(235, 80, 70), acc=(250, 240, 200), hat="horns", price=200, desc="Прыжок +30%. Перепрыгивает поезда", j=1.3),
    dict(n="Волшебник", body=(70, 70, 180), skin=(255, 220, 180), acc=(255, 230, 90), hat="wizard", price=260, desc="Щит: переживает одно столкновение", sh=1),
    dict(n="Повар", body=(245, 245, 245), skin=(255, 210, 170), acc=(230, 60, 60), hat="chef", price=330, desc="Монеты ×3", c=3),
    dict(n="Викинг", body=(140, 90, 40), skin=(255, 215, 175), acc=(170, 175, 190), hat="viking", price=400, desc="Прыжок +20%, кувырок дольше. Перепрыгивает поезда", j=1.2, r=1.4),
    dict(n="Супергерой", body=(40, 60, 200), skin=(255, 220, 180), acc=(230, 30, 50), hat="cape", price=500, desc="Прыжок +30%, очки +20%. Перепрыгивает поезда", j=1.3, sm=1.2),
    dict(n="Призрак", body=(215, 230, 255), skin=(235, 243, 255), acc=(120, 140, 200), hat="ghost", price=620, desc="Щит и медленный разгон", sh=1, ramp=0.7),
    dict(n="Диджей", body=(30, 30, 35), skin=(200, 150, 110), acc=(255, 0, 120), hat="phones", price=780, desc="Монеты ×2, очки +20%, магнит", c=2, sm=1.2, mag=1),
    dict(n="Дракончик", body=(60, 170, 80), skin=(110, 210, 110), acc=(255, 140, 0), hat="dino", price=1000, desc="Прыжок +35% и магнит. Перепрыгивает поезда", j=1.35, mag=1),
    dict(n="Легенда", body=(255, 235, 140), skin=(255, 225, 190), acc=(255, 255, 255), hat="halo", price=1500, desc="Все бонусы: щит, магнит, прыжок +45%, монеты ×3, кувырок и очки", j=1.45, r=1.5, c=3, ramp=0.6, sm=1.3, sh=1, mag=1),
    # --- новые 10
    dict(n="Самурай", body=(170, 30, 30), skin=(255, 220, 180), acc=(225, 190, 60), hat="samurai", price=700, desc="Кувырок +60%, прыжок +15%. Перепрыгивает поезда", r=1.6, j=1.15),
    dict(n="Ковбой", body=(160, 100, 60), skin=(245, 205, 165), acc=(120, 70, 30), hat="cowboy", price=900, desc="Монеты ×2 и очки +10%", c=2, sm=1.1),
    dict(n="Пингвин", body=(30, 30, 45), skin=(30, 30, 40), acc=(255, 150, 30), hat="penguin", price=1100, desc="Очень медленный разгон", ramp=0.45),
    dict(n="Лисичка", body=(240, 130, 40), skin=(250, 170, 90), acc=(255, 245, 230), hat="fox", price=1300, desc="Прыжок +25% и магнит. Перепрыгивает поезда", j=1.25, mag=1),
    dict(n="Мумия", body=(225, 215, 185), skin=(235, 225, 195), acc=(235, 225, 200), hat="mummy", price=1500, desc="Щит и монеты ×2", sh=1, c=2),
    dict(n="Рыцарь", body=(165, 170, 185), skin=(255, 220, 180), acc=(190, 195, 210), hat="knight", price=1800, desc="Щит и кувырок +30%", sh=1, r=1.3),
    dict(n="Пришелец", body=(90, 70, 160), skin=(120, 220, 120), acc=(180, 255, 180), hat="alien", price=2000, desc="Прыжок +50%. Перепрыгивает поезда", j=1.5),
    dict(n="Тыквоголов", body=(60, 40, 30), skin=(255, 140, 20), acc=(60, 160, 60), hat="pumpkin", price=2300, desc="Очки +50%", sm=1.5),
    dict(n="Снеговик", body=(240, 245, 255), skin=(250, 252, 255), acc=(220, 40, 40), hat="snowman", price=2700, desc="Магнит и щит", mag=1, sh=1),
    dict(n="Император", body=(150, 20, 40), skin=(255, 220, 180), acc=(255, 215, 0), hat="emperor", price=5000, desc="Максимум: 2 щита, магнит, прыжок +60%, монеты ×4, очки +50%", j=1.6, r=1.6, c=4, ramp=0.5, sm=1.5, sh=2, mag=1),
    # --- ещё 10
    dict(n="Лучник", body=(40, 120, 60), skin=(245, 205, 165), acc=(30, 150, 60), hat="archer", price=1200, desc="Магнит и монеты ×2", mag=1, c=2),
    dict(n="Шахтёр", body=(200, 140, 40), skin=(235, 190, 150), acc=(255, 230, 90), hat="miner", price=1500, desc="Монеты ×2 и очки +20%", c=2, sm=1.2),
    dict(n="Пчёлка", body=(255, 210, 40), skin=(255, 225, 120), acc=(30, 30, 30), hat="bee", price=1900, desc="Прыжок +30%, медленный разгон. Перепрыгивает поезда", j=1.3, ramp=0.7),
    dict(n="Мишка", body=(150, 100, 60), skin=(190, 130, 80), acc=(120, 80, 45), hat="bear", price=2300, desc="Щит и кувырок +40%", sh=1, r=1.4),
    dict(n="Единорог", body=(255, 230, 250), skin=(255, 245, 255), acc=(255, 150, 220), hat="unicorn", price=2800, desc="Прыжок +40% и магнит. Перепрыгивает поезда", j=1.4, mag=1),
    dict(n="Огненный", body=(220, 60, 20), skin=(255, 170, 100), acc=(255, 200, 40), hat="flame", price=3300, desc="Очки +40% и кувырок +30%", sm=1.4, r=1.3),
    dict(n="Ледяной", body=(120, 200, 255), skin=(210, 240, 255), acc=(255, 255, 255), hat="ice", price=4000, desc="Щит и очень медленный разгон", sh=1, ramp=0.5),
    dict(n="Киборг", body=(60, 70, 85), skin=(170, 175, 185), acc=(255, 40, 40), hat="cyborg", price=4800, desc="Прыжок +50% и монеты ×2. Перепрыгивает поезда", j=1.5, c=2),
    dict(n="Тёмный маг", body=(40, 20, 60), skin=(190, 170, 210), acc=(190, 80, 255), hat="darkmage", price=6000, desc="Монеты ×3, щит и магнит", c=3, sh=1, mag=1),
    dict(n="Громовержец", body=(230, 230, 255), skin=(255, 225, 190), acc=(255, 230, 60), hat="thunder", price=9000, desc="Максимум: 2 щита, прыжок +70%, монеты ×4, очки +60%", j=1.7, r=1.7, c=4, ramp=0.45, sm=1.6, sh=2, mag=1),
]

LOCS = [
    dict(n="Город", sky=((90, 170, 255), (190, 230, 255)), ground=(80, 130, 80), road=(70, 70, 80), line=(230, 230, 230),
         dec="city", sun=((255, 240, 120), 0.8, 0.07), price=0, base=262, scale=[0, 2, 4, 7, 9, 12], stars=False),
    dict(n="Пустыня", sky=((255, 170, 90), (255, 225, 160)), ground=(225, 190, 120), road=(120, 95, 70), line=(250, 235, 200),
         dec="desert", sun=((255, 90, 30), 0.25, 0.10), price=40, base=294, scale=[0, 1, 4, 5, 7, 8, 11], stars=False),
    dict(n="Снежные горы", sky=((150, 190, 230), (235, 245, 255)), ground=(235, 240, 250), road=(110, 120, 140), line=(255, 255, 255),
         dec="snow", sun=((255, 255, 255), 0.75, 0.05), price=100, base=330, scale=[0, 2, 3, 7, 8, 12], stars=False),
    dict(n="Неон-сити", sky=((10, 5, 40), (80, 20, 110)), ground=(20, 15, 40), road=(30, 30, 55), line=(0, 255, 230),
         dec="neon", sun=((240, 240, 255), 0.78, 0.06), price=180, base=220, scale=[0, 3, 5, 7, 10, 12], stars=True),
    dict(n="Вулкан", sky=((60, 10, 10), (255, 100, 30)), ground=(60, 25, 20), road=(45, 40, 45), line=(255, 170, 40),
         dec="lava", sun=((255, 200, 60), 0.5, 0.12), price=300, base=196, scale=[0, 1, 3, 6, 7, 10], stars=False),
    dict(n="Джунгли", sky=((70, 160, 120), (180, 230, 170)), ground=(30, 90, 40), road=(95, 70, 45), line=(240, 230, 150),
         dec="jungle", sun=((255, 250, 150), 0.3, 0.06), price=250, base=247, scale=[0, 2, 3, 5, 7, 10], stars=False),
    dict(n="Пляж", sky=((70, 190, 255), (200, 240, 255)), ground=(240, 215, 150), road=(150, 110, 70), line=(255, 255, 240),
         dec="beach", sun=((255, 230, 80), 0.7, 0.08), price=350, base=277, scale=[0, 2, 4, 7, 9], stars=False),
    dict(n="Космос", sky=((0, 0, 15), (20, 10, 50)), ground=(110, 110, 125), road=(45, 45, 60), line=(200, 200, 255),
         dec="space", sun=((255, 200, 120), 0.8, 0.04), price=450, base=185, scale=[0, 2, 3, 5, 7, 8, 10], stars=True),
    dict(n="Конфетный мир", sky=((255, 170, 220), (255, 235, 250)), ground=(255, 170, 200), road=(200, 130, 220), line=(255, 255, 255),
         dec="candy", sun=((255, 240, 160), 0.75, 0.07), price=600, base=330, scale=[0, 2, 4, 5, 7, 9, 11], stars=False),
    dict(n="Океан", sky=((0, 50, 110), (30, 170, 200)), ground=(30, 100, 130), road=(20, 60, 95), line=(160, 240, 255),
         dec="ocean", sun=((200, 255, 255), 0.5, 0.05), price=800, base=233, scale=[0, 3, 5, 7, 10], stars=False),
    # --- новые 5
    dict(n="Сакура", sky=((255, 200, 220), (255, 240, 245)), ground=(120, 170, 110), road=(140, 110, 100), line=(255, 255, 255),
         dec="sakura", sun=((240, 60, 60), 0.5, 0.1), price=700, base=262, scale=[0, 2, 4, 7, 9], stars=False),
    dict(n="Дикий Запад", sky=((200, 100, 60), (255, 205, 130)), ground=(200, 130, 80), road=(110, 70, 50), line=(240, 200, 150),
         dec="mesa", sun=((255, 235, 160), 0.2, 0.08), price=900, base=220, scale=[0, 3, 5, 7, 10], stars=False),
    dict(n="Хэллоуин", sky=((20, 10, 40), (90, 40, 80)), ground=(30, 40, 30), road=(50, 40, 50), line=(255, 140, 0),
         dec="spooky", sun=((255, 170, 40), 0.7, 0.09), price=1100, base=196, scale=[0, 1, 4, 6, 7], stars=True),
    dict(n="Синтвейв", sky=((20, 0, 60), (255, 60, 160)), ground=(20, 0, 40), road=(30, 10, 60), line=(0, 255, 255),
         dec="synth", sun=((255, 210, 60), 0.5, 0.16), price=1400, base=247, scale=[0, 3, 7, 10, 12, 15], stars=True),
    dict(n="Кристальная пещера", sky=((10, 15, 35), (50, 35, 90)), ground=(35, 30, 60), road=(55, 50, 90), line=(140, 200, 255),
         dec="crystal", sun=((150, 220, 255), 0.5, 0.03), price=1800, base=349, scale=[0, 2, 5, 7, 9, 12], stars=True),
    dict(n="Ферма", sky=((120, 190, 255), (220, 240, 255)), ground=(110, 170, 80), road=(150, 120, 80), line=(255, 245, 200),
         dec="farm", sun=((255, 245, 150), 0.78, 0.07), price=2200, base=262, scale=[0, 2, 4, 5, 7, 9], stars=False),
    dict(n="Парк аттракционов", sky=((60, 20, 110), (255, 120, 170)), ground=(50, 35, 80), road=(70, 50, 100), line=(255, 230, 90),
         dec="carnival", sun=((255, 240, 180), 0.2, 0.05), price=2600, base=330, scale=[0, 2, 4, 7, 9, 11], stars=True),
    dict(n="Метро", sky=((15, 15, 25), (40, 45, 60)), ground=(30, 32, 40), road=(60, 62, 72), line=(255, 220, 80),
         dec="metro", sun=((255, 230, 150), 0.5, 0.02), price=3000, base=196, scale=[0, 3, 5, 7, 10], stars=False),
    dict(n="Завод", sky=((90, 80, 75), (200, 140, 90)), ground=(60, 55, 55), road=(70, 68, 72), line=(255, 200, 40),
         dec="factory", sun=((255, 150, 60), 0.7, 0.09), price=3500, base=175, scale=[0, 1, 5, 7, 8], stars=False),
    dict(n="Небеса", sky=((90, 170, 255), (255, 230, 250)), ground=(230, 240, 255), road=(255, 235, 170), line=(255, 255, 255),
         dec="sky", sun=((255, 250, 200), 0.5, 0.1), price=4500, base=392, scale=[0, 2, 4, 7, 9, 12], stars=False),
]

MODES = [
    dict(key="classic", n="КЛАССИКА", col=(40, 120, 255), desc="Беги пока не врежешься. Один шанс, скорость растёт."),
    dict(key="lava", n="ПОЛ — ЭТО ЛАВА", col=(220, 80, 20),
         desc="Земля — лава! Плиты разделены пропастями. Большой прыжок перезаряжается 6–8 секунд. Упал в лаву — проиграл. Малый прыжок свайпом вверх, пока большой на паузе."),
    dict(key="rush", n="МОНЕТНАЯ ГОНКА", col=(200, 150, 20), desc="60 секунд и куча монет. Столкновение не убивает, но отнимает 5 секунд."),
    dict(key="sprint", n="СПРИНТ", col=(40, 170, 120), desc="Добеги до финиша как можно быстрее. Каждое столкновение — +2 секунды и замедление."),
    dict(key="chaos", n="ХАОС", col=(170, 60, 200), desc="Каждые 10 секунд случайное событие: зеркальное управление, турбо или дождь монет."),
    dict(key="dark", n="ТЬМА", col=(130, 110, 220), desc="Ночной бег с фонарём: видно только то, что рядом. Монеты ×2."),
    dict(key="hard", n="ХАРДКОР", col=(210, 40, 40), desc="Огромная скорость и плотные препятствия. Монеты ×2 и двойная награда в конце."),
]

# slot: glasses / back / board / trail / neck / pet / aura
ACCS = [
    dict(n="Тёмные очки", slot="glasses", price=50, desc="Крутой вид", col=(15, 15, 20), kind="dark"),
    dict(n="Очки-сердечки", slot="glasses", price=90, desc="Для романтиков", col=(255, 60, 120), kind="heart"),
    dict(n="Золотые очки", slot="glasses", price=180, desc="Очки +20%", col=(255, 215, 0), kind="dark", perk=dict(sm=1.2)),
    dict(n="Рюкзак", slot="back", price=60, desc="Просто рюкзак", col=(200, 90, 40), kind="pack"),
    dict(n="Ангельские крылья", slot="back", price=220, desc="Прыжок +10%", col=(255, 255, 255), kind="wings", perk=dict(j=1.1)),
    dict(n="Реактивный ранец", slot="back", price=320, desc="Разгон медленнее на 20%", col=(140, 150, 165), kind="jet", perk=dict(ramp=0.8)),
    dict(n="Скейт", slot="board", price=100, desc="Катись стильно", col=(220, 60, 60), kind="skate"),
    dict(n="Ховерборд", slot="board", price=260, desc="Щит: переживает одно столкновение", col=(60, 200, 255), kind="hover", perk=dict(sh=1)),
    dict(n="Огненная доска", slot="board", price=500, desc="Магнит для монет", col=(255, 120, 20), kind="fire", perk=dict(mag=1)),
    dict(n="Радужный след", slot="trail", price=150, desc="Красивый след за бегуном", col=None, kind="rainbow"),
    dict(n="Огненный след", slot="trail", price=300, desc="Горячо!", col=(255, 140, 20), kind="flame"),
    dict(n="Звёздный след", slot="trail", price=400, desc="Блестит", col=(255, 240, 120), kind="star"),
    dict(n="Шарф", slot="neck", price=80, desc="Тёплый шарф", col=(220, 50, 50), kind="scarf"),
    dict(n="Золотая цепь", slot="neck", price=200, desc="Очки +10%", col=(255, 215, 0), kind="chain", perk=dict(sm=1.1)),
    dict(n="Медаль чемпиона", slot="neck", price=350, desc="Разгон медленнее на 10%", col=(255, 215, 0), kind="medal", perk=dict(ramp=0.9)),
    dict(n="Котёнок", slot="pet", price=150, desc="Бежит рядом с тобой", col=(255, 170, 80), kind="kitty"),
    dict(n="Дракончик-питомец", slot="pet", price=500, desc="Кувырок +20%", col=(90, 200, 100), kind="pdragon", perk=dict(r=1.2)),
    dict(n="Дрон", slot="pet", price=450, desc="Магнит для монет", col=(170, 180, 200), kind="drone", perk=dict(mag=1)),
    dict(n="Огненная аура", slot="aura", price=300, desc="Горишь стильно", col=None, kind="afire"),
    dict(n="Звёздная аура", slot="aura", price=380, desc="Звёзды кружатся вокруг", col=None, kind="astar"),
    dict(n="Неоновая аура", slot="aura", price=500, desc="Очки +15%", col=None, kind="aneon", perk=dict(sm=1.15)),
    dict(n="Плащ вампира", slot="back", price=280, desc="Мрачный плащ", col=(120, 15, 40), kind="cloak"),
]
SLOT_RU = {"glasses": "Очки", "back": "Спина", "board": "Доска", "trail": "След", "neck": "Шея", "pet": "Питомец", "aura": "Аура"}
RAINBOW = [(255, 60, 60), (255, 150, 30), (255, 230, 50), (80, 220, 80), (60, 180, 255), (150, 100, 255)]

STYLE = {
    "city": dict(tr=((200, 50, 50), (232, 105, 105), (150, 35, 35), (240, 220, 90), "metro"), lo=("bar", (255, 140, 0), (255, 255, 255)), hi=("beam", (120, 120, 140), (230, 60, 60))),
    "desert": dict(tr=((170, 120, 70), (205, 160, 100), (120, 80, 45), (230, 200, 140), "wagon"), lo=("rock", (150, 130, 110), (110, 95, 80)), hi=("beam", (120, 80, 45), (200, 150, 90))),
    "snow": dict(tr=((90, 150, 210), (210, 235, 255), (60, 110, 170), (255, 255, 255), "stripes"), lo=("ice", (180, 225, 255), (255, 255, 255)), hi=("icicle", (120, 160, 200), (220, 245, 255))),
    "neon": dict(tr=((25, 20, 55), (60, 40, 110), (15, 10, 40), (0, 255, 230), "neon"), lo=("neon", (0, 255, 230), (255, 40, 200)), hi=("laser", (80, 80, 120), (255, 40, 200))),
    "lava": dict(tr=((45, 35, 45), (80, 60, 70), (30, 22, 30), (255, 120, 20), "rust"), lo=("rock", (60, 40, 40), (255, 120, 20)), hi=("pipe", (70, 50, 50), (255, 120, 20))),
    "jungle": dict(tr=((110, 75, 40), (150, 110, 60), (80, 55, 30), (60, 170, 70), "wagon"), lo=("log", (120, 80, 40), (170, 120, 60)), hi=("vine", (40, 130, 50), (80, 190, 80))),
    "beach": dict(tr=((255, 210, 60), (255, 235, 130), (215, 170, 40), (40, 160, 220), "stripes"), lo=("ball", (255, 90, 90), (255, 255, 255)), hi=("banner", (150, 100, 50), (255, 120, 60))),
    "space": dict(tr=((225, 230, 240), (250, 252, 255), (170, 175, 190), (80, 160, 255), "round"), lo=("rock", (130, 130, 145), (90, 90, 105)), hi=("laser", (160, 165, 180), (100, 200, 255))),
    "candy": dict(tr=((255, 130, 190), (255, 190, 225), (215, 90, 150), (255, 255, 255), "stripes"), lo=("cone", (255, 80, 140), (255, 255, 255)), hi=("rainbow", (255, 255, 255), (255, 80, 140))),
    "ocean": dict(tr=((240, 190, 40), (255, 225, 110), (190, 140, 20), (160, 230, 255), "round"), lo=("coral", (255, 120, 100), (255, 170, 60)), hi=("vine", (30, 120, 80), (60, 190, 120))),
    "sakura": dict(tr=((190, 50, 50), (235, 235, 225), (130, 35, 35), (255, 255, 255), "wagon"), lo=("lantern", (150, 150, 150), (255, 200, 90)), hi=("torii", (200, 40, 40), (30, 30, 30))),
    "mesa": dict(tr=((120, 75, 45), (165, 115, 75), (85, 52, 30), (200, 160, 100), "wagon"), lo=("barrel", (130, 85, 50), (90, 60, 35)), hi=("beam", (100, 65, 40), (170, 120, 70))),
    "spooky": dict(tr=((35, 30, 45), (65, 55, 85), (22, 18, 30), (190, 80, 255), "round"), lo=("tomb", (120, 120, 135), (80, 80, 95)), hi=("banner", (60, 50, 70), (255, 140, 0))),
    "synth": dict(tr=((40, 10, 80), (120, 40, 170), (25, 5, 55), (255, 60, 200), "neon"), lo=("neon", (255, 60, 200), (0, 255, 255)), hi=("laser", (60, 30, 100), (0, 255, 255))),
    "crystal": dict(tr=((90, 70, 170), (150, 130, 230), (60, 45, 120), (130, 230, 255), "glass"), lo=("crystal", (120, 230, 255), (255, 130, 230)), hi=("icicle", (80, 60, 140), (150, 230, 255))),
    "farm": dict(tr=((60, 140, 70), (110, 180, 110), (40, 100, 50), (255, 210, 60), "wagon"), lo=("bale", (230, 200, 90), (180, 150, 50)), hi=("beam", (130, 90, 50), (200, 160, 100))),
    "carnival": dict(tr=((220, 50, 60), (255, 255, 255), (160, 30, 40), (255, 230, 90), "stripes"), lo=("crate", (255, 200, 60), (200, 60, 60)), hi=("banner", (120, 80, 160), (255, 80, 120))),
    "metro": dict(tr=((170, 175, 185), (210, 215, 225), (110, 115, 125), (255, 200, 50), "metro"), lo=("cone", (255, 140, 0), (255, 255, 255)), hi=("pipe", (120, 125, 135), (255, 200, 50))),
    "factory": dict(tr=((140, 90, 50), (190, 140, 90), (95, 60, 35), (255, 200, 40), "rust"), lo=("barrel", (200, 60, 40), (255, 200, 40)), hi=("pipe", (90, 90, 100), (255, 200, 40))),
    "sky": dict(tr=((255, 255, 255), (255, 245, 200), (215, 220, 240), (255, 200, 60), "stripes"), lo=("cloud", (255, 255, 255), (210, 225, 250)), hi=("rainbow", (255, 255, 255), (255, 100, 150))),
}
FX = {"snow": "snow", "desert": "dust", "neon": "twinkle", "lava": "ember", "jungle": "leaf", "space": "twinkle",
      "candy": "sprinkle", "ocean": "bubble", "sakura": "petal", "mesa": "dust", "spooky": "ember", "synth": "twinkle",
      "crystal": "twinkle", "farm": "leaf", "carnival": "confetti", "factory": "ember", "sky": "twinkle"}
NOCLOUD = {"neon", "space", "spooky", "synth", "crystal", "metro", "carnival"}
CLOUDCOL = {"lava": (105, 50, 45), "desert": (255, 238, 215), "factory": (120, 105, 100), "mesa": (255, 225, 190)}


def _vign():
    v = pygame.Surface((W, H), pygame.SRCALPHA)
    v.fill((0, 0, 0, 238))
    cx, cy, R = W // 2, int(H * 0.74), int(H * 0.45)
    for i in range(24, 0, -1):
        pygame.draw.circle(v, (0, 0, 0, int(238 * (i / 24) ** 2.2)), (cx, cy), int(R * i / 24))
    return v


VIGN = _vign()

random.seed(7)
STARS = [(random.random() * W, random.random() * HOR * 0.9, random.choice([1, 2, 2, 3])) for _ in range(40)]
random.seed()


def eff_perks(ch, acc_sel):
    p = {k: ch.get(k, 0 if k in ("sh", "mag") else 1) for k in ("j", "r", "c", "ramp", "sm", "sh", "mag")}
    for slot, idx in acc_sel.items():
        if idx is not None:
            for k, v in ACCS[idx].get("perk", {}).items():
                if k in ("sh", "mag"):
                    p[k] += v
                else:
                    p[k] *= v
    return p


# ------------------------------------------------------------ ЗВУК
SR = 22050


def tone(f0, f1, dur, vol=0.5, noise=False):
    n = int(SR * dur)
    out = []
    ph = 0.0
    for i in range(n):
        k = i / n
        ph += 2 * math.pi * (f0 + (f1 - f0) * k) / SR
        v = random.uniform(-1, 1) if noise else math.sin(ph) + 0.3 * math.sin(2 * ph)
        out.append(v * vol * (1 - k) ** 1.5)
    return out


def mk(samples):
    a = array("h", [int(max(-1, min(1, v)) * 30000) for v in samples])
    return pygame.mixer.Sound(buffer=a.tobytes())


def make_music(li):
    L = LOCS[li]
    rnd = random.Random(li * 11 + 3)
    step = 0.22
    N = int(SR * step * 16)
    buf = [0.0] * N
    sc = L["scale"]
    pat = [rnd.randrange(len(sc)) for _ in range(16)]
    for s in range(16):
        if rnd.random() < 0.2:
            continue
        f = L["base"] * 2 ** (sc[pat[s]] / 12)
        w = 2 * math.pi * f / SR
        st = int(s * step * SR)
        ln = int(step * SR * 0.9)
        for i in range(ln):
            e = (1 - i / ln) ** 1.3
            buf[st + i] += 0.16 * e * (math.sin(w * i) + 0.4 * math.sin(2 * w * i))
        if s % 4 == 0:
            f = L["base"] / 2 * 2 ** (sc[pat[s] % 3] / 12)
            w = 2 * math.pi * f / SR
            ln = int(step * SR * 3.2)
            for i in range(ln):
                if st + i >= N:
                    break
                buf[st + i] += 0.22 * (1 - i / ln) ** 0.8 * math.sin(w * i)
        if s % 2 == 1:
            st = int(s * step * SR)
            for i in range(int(SR * 0.025)):
                buf[st + i] += 0.07 * random.uniform(-1, 1) * (1 - i / (SR * 0.025))
    return mk(buf)


class Audio:
    def __init__(self, on=True):
        self.on = on
        self.ok = pygame.mixer.get_init() is not None
        self.sfx = {}
        self.music = {}
        self.cur = None
        if not self.ok:
            return
        try:
            self.sfx = {
                "coin": mk(tone(988, 988, .06, .4) + tone(1319, 1319, .2, .4)),
                "jump": mk(tone(300, 750, .2, .5)),
                "mega": mk(tone(200, 1100, .45, .55)),
                "roll": mk(tone(650, 180, .2, .5)),
                "swipe": mk(tone(500, 500, .04, .3)),
                "crash": mk(tone(0, 0, .6, .9, True)),
                "click": mk(tone(700, 700, .04, .4)),
                "buy": mk(sum([tone(f, f, .09, .4) for f in (523, 659, 784, 1047)], [])),
                "no": mk(tone(220, 140, .25, .5)),
                "shield": mk(tone(400, 900, .15, .5) + tone(900, 400, .15, .4)),
                "ready": mk(tone(800, 800, .06, .4) + tone(1200, 1200, .12, .4)),
            }
        except Exception:
            self.ok = False

    def play(self, name):
        if self.ok and self.on and name in self.sfx:
            self.sfx[name].play()

    def play_music(self, li):
        if not (self.ok and self.on):
            return
        if self.cur == li:
            return
        self.stop_music()
        try:
            if li not in self.music:
                self.music[li] = make_music(li)
            self.music[li].set_volume(0.35)
            self.music[li].play(-1)
            self.cur = li
        except Exception:
            pass

    def stop_music(self):
        if self.cur is not None and self.cur in self.music:
            self.music[self.cur].stop()
        self.cur = None


# ------------------------------------------------------------ СОХРАНЕНИЕ
def load():
    d = dict(coins=0, best=0, bests=None, chars=[0], locs=[0], sel_c=0, sel_l=0, sound=True,
             acc_own=[], acc_sel=dict(glasses=None, back=None, board=None, trail=None, neck=None, pet=None, aura=None),
             stats=dict(runs=0, coins=0, score=0, distance=0, jumps=0, rolls=0,
                        hard_runs=0, sprint_runs=0, chars=1, locs=1, acc=0),
             task_claimed=[], achievements=[])
    try:
        d.update(json.load(open(SAVE)))
    except Exception:
        pass
    if not isinstance(d.get("bests"), list):
        d["bests"] = [d.get("best", 0)]
    while len(d["bests"]) < len(MODES):
        d["bests"].append(0)
    for sl in SLOT_RU:
        d["acc_sel"].setdefault(sl, None)
    d.setdefault("stats", {})
    for k,v in dict(runs=0,coins=0,score=0,distance=0,jumps=0,rolls=0,
                    hard_runs=0,sprint_runs=0,chars=len(d.get("chars",[0])),
                    locs=len(d.get("locs",[0])),acc=len(d.get("acc_own",[]))).items():
        d["stats"].setdefault(k,v)
    d.setdefault("task_claimed", [])
    d.setdefault("achievements", [])
    return d


def save():
    try:
        json.dump(SV, open(SAVE, "w"))
    except Exception:
        pass


SV = load()
audio = Audio(SV["sound"])


# ------------------------------------------------------------ РИСОВАНИЕ
def proj(lane, t):
    sc = 0.1 + 0.9 * t
    return W / 2 + lane * SPREAD * sc, HOR + (PY - HOR) * t, sc


def draw_board(kind, col, cx, by, u):
    s = screen
    if kind == "skate":
        pygame.draw.rect(s, col, (cx - u * 0.85, by, u * 1.7, u * 0.14))
        for sd in (-1, 1):
            pygame.draw.circle(s, (240, 240, 240), (int(cx + sd * u * 0.5), int(by + u * 0.2)), max(2, int(u * 0.1)))
    elif kind == "hover":
        pygame.draw.ellipse(s, (170, 235, 255), (cx - u * 1.0, by + u * 0.02, u * 2.0, u * 0.3))
        pygame.draw.rect(s, col, (cx - u * 0.8, by, u * 1.6, u * 0.12))
    else:
        pygame.draw.rect(s, (110, 60, 30), (cx - u * 0.8, by, u * 1.6, u * 0.12))
        pygame.draw.polygon(s, (255, 140, 20), [(cx - u * 0.7, by + u * 0.12), (cx - u * 0.35, by + u * 0.55), (cx, by + u * 0.12)])
        pygame.draw.polygon(s, (255, 140, 20), [(cx, by + u * 0.12), (cx + u * 0.35, by + u * 0.6), (cx + u * 0.7, by + u * 0.12)])
        pygame.draw.polygon(s, (255, 235, 80), [(cx - u * 0.4, by + u * 0.12), (cx - u * 0.25, by + u * 0.35), (cx - u * 0.1, by + u * 0.12)])


def draw_back(kind, col, cx, bx, bt, by, u):
    s = screen
    if kind == "pack":
        pygame.draw.rect(s, col, (bx - u * 0.3, bt + u * 0.1, u * 0.38, u * 0.7))
        pygame.draw.rect(s, (90, 40, 20), (bx - u * 0.3, bt + u * 0.1, u * 0.38, u * 0.7), 2)
    elif kind == "wings":
        for sd in (-1, 1):
            pygame.draw.polygon(s, col, [(cx + sd * u * 0.4, bt + u * 0.1), (cx + sd * u * 1.35, bt - u * 0.45),
                                         (cx + sd * u * 1.2, bt + u * 0.55), (cx + sd * u * 0.4, bt + u * 0.7)])
            pygame.draw.polygon(s, (170, 180, 200), [(cx + sd * u * 0.4, bt + u * 0.1), (cx + sd * u * 1.35, bt - u * 0.45),
                                                     (cx + sd * u * 1.2, bt + u * 0.55), (cx + sd * u * 0.4, bt + u * 0.7)], 2)
    elif kind == "cloak":
        pygame.draw.polygon(s, col, [(bx + u * 0.1, bt), (bx + u * 0.9, bt), (bx + u * 1.35, by + u * 0.1), (bx - u * 0.35, by + u * 0.1)])
        pygame.draw.polygon(s, (60, 5, 20), [(bx + u * 0.3, bt), (bx + u * 0.7, bt), (bx + u * 0.9, by + u * 0.1), (bx + u * 0.1, by + u * 0.1)])
    else:
        for xx in (bx - u * 0.18, bx + u * 0.98):
            pygame.draw.rect(s, col, (xx, bt + u * 0.1, u * 0.2, u * 0.7))
            pygame.draw.polygon(s, (255, 150, 30), [(xx, bt + u * 0.8), (xx + u * 0.2, bt + u * 0.8), (xx + u * 0.1, bt + u * 1.15)])


def draw_char(ch, cx, by, u, rolling=False, acc=None):
    s = screen
    if acc is None:
        acc = SV["acc_sel"]
    A = {sl: (ACCS[i] if i is not None else None) for sl, i in acc.items()}
    lw = max(1, int(u * 0.06))
    h = ch["hat"]
    a = ch["acc"]
    if rolling:
        pygame.draw.ellipse(s, ch["body"], (cx - u * 0.9, by - u * 0.8, u * 1.8, u * 0.8))
        pygame.draw.circle(s, ch["skin"], (int(cx + u * 0.5), int(by - u * 0.4)), int(u * 0.3))
        pygame.draw.ellipse(s, a, (cx - u * 0.5, by - u * 0.55, u * 0.5, u * 0.2))
        return
    bx, bt = cx - u * 0.5, by - u
    if A.get("aura"):
        draw_aura(A["aura"]["kind"], cx, by, u)
    if A.get("board"):
        draw_board(A["board"]["kind"], A["board"]["col"], cx, by, u)
    if A.get("back"):
        draw_back(A["back"]["kind"], A["back"]["col"], cx, bx, bt, by, u)
    if h in ("cape", "emperor"):
        cc = a if h == "cape" else (150, 20, 40)
        pygame.draw.polygon(s, cc, [(bx + u * 0.1, bt), (bx + u * 0.9, bt), (bx + u * 1.2, by), (bx - u * 0.2, by)])
    if h == "halo":
        for sd in (-1, 1):
            pygame.draw.polygon(s, (255, 255, 255), [(cx + sd * u * 0.45, bt + u * 0.15), (cx + sd * u * 1.4, bt - u * 0.3),
                                                      (cx + sd * u * 1.2, bt + u * 0.5), (cx + sd * u * 0.45, bt + u * 0.6)])
    pygame.draw.rect(s, ch["body"], (bx, bt, u, u))
    if h == "ghost":
        for i in range(3):
            pygame.draw.polygon(s, ch["body"], [(bx + u * i / 3, by), (bx + u * (i + 1) / 3, by), (bx + u * (i + 0.5) / 3, by + u * 0.25)])
    if h == "penguin":
        pygame.draw.rect(s, (245, 245, 250), (cx - u * 0.3, bt + u * 0.1, u * 0.6, u * 0.8))
    elif h == "mummy":
        for i in range(4):
            pygame.draw.line(s, (170, 160, 130), (bx, bt + u * 0.2 * (i + 1)), (bx + u, bt + u * 0.2 * (i + 1) - u * 0.1), lw)
    elif h == "cowboy":
        pygame.draw.circle(s, (255, 220, 60), (int(cx), int(bt + u * 0.3)), max(2, int(u * 0.1)))
    elif h == "snowman":
        pygame.draw.circle(s, (30, 30, 30), (int(cx), int(bt + u * 0.4)), max(2, int(u * 0.07)))
        pygame.draw.circle(s, (30, 30, 30), (int(cx), int(bt + u * 0.7)), max(2, int(u * 0.07)))
    else:
        pygame.draw.rect(s, a, (bx, bt + u * 0.55, u, u * 0.14))
    hr = u * 0.42
    hx, hy = int(cx), int(bt - hr * 0.9)
    pygame.draw.circle(s, ch["skin"], (hx, hy), int(hr))
    if h == "cap":
        pygame.draw.rect(s, a, (hx - hr, hy - hr * 1.0, hr * 2, hr * 0.7))
        pygame.draw.rect(s, a, (hx, hy - hr * 0.4, hr * 1.4, hr * 0.25))
    elif h == "band":
        pygame.draw.rect(s, a, (hx - hr, hy - hr * 0.55, hr * 2, hr * 0.28))
        pygame.draw.circle(s, a, (int(hx + hr * 0.7), int(hy - hr * 0.9)), int(hr * 0.35))
    elif h == "mask":
        pygame.draw.rect(s, ch["body"], (hx - hr, hy - hr * 0.95, hr * 2, hr * 0.8))
        pygame.draw.rect(s, a, (hx - hr, hy - hr * 0.45, hr * 2, hr * 0.2))
        pygame.draw.rect(s, ch["skin"], (hx - hr * 0.8, hy - hr * 0.25, hr * 1.6, hr * 0.3))
    elif h == "antenna":
        pygame.draw.line(s, a, (hx, hy - hr), (hx, hy - hr * 1.7), lw + 1)
        pygame.draw.circle(s, a, (hx, int(hy - hr * 1.8)), int(hr * 0.22))
        pygame.draw.rect(s, a, (hx - hr * 0.7, hy - hr * 0.2, hr * 1.4, hr * 0.28))
    elif h == "pirate":
        pygame.draw.ellipse(s, a, (hx - hr * 1.3, hy - hr * 1.2, hr * 2.6, hr * 0.9))
        pygame.draw.rect(s, (200, 30, 30), (hx - hr * 1.0, hy - hr * 0.55, hr * 2, hr * 0.18))
        pygame.draw.circle(s, a, (int(hx - hr * 0.35), int(hy - hr * 0.05)), int(hr * 0.25))
    elif h == "helmet":
        pygame.draw.circle(s, (170, 220, 255), (hx, hy), int(hr * 1.2), lw + 2)
        pygame.draw.rect(s, a, (hx - hr * 1.2, hy + hr * 0.9, hr * 2.4, hr * 0.3))
    elif h == "clown":
        pygame.draw.polygon(s, a, [(hx - hr * 0.7, hy - hr * 0.8), (hx + hr * 0.7, hy - hr * 0.8), (hx, hy - hr * 2.0)])
        pygame.draw.circle(s, (230, 30, 30), (hx, int(hy + hr * 0.15)), int(hr * 0.25))
    elif h == "zombie":
        pygame.draw.line(s, a, (hx - hr * 0.6, hy - hr * 0.8), (hx - hr * 0.1, hy - hr * 0.3), lw + 1)
        pygame.draw.line(s, a, (hx + hr * 0.2, hy + hr * 0.3), (hx + hr * 0.7, hy + hr * 0.7), lw + 1)
    elif h == "crown":
        pygame.draw.polygon(s, a, [(hx - hr * 0.9, hy - hr * 0.7), (hx - hr * 0.9, hy - hr * 1.6), (hx - hr * 0.45, hy - hr * 1.1),
                                   (hx, hy - hr * 1.8), (hx + hr * 0.45, hy - hr * 1.1), (hx + hr * 0.9, hy - hr * 1.6),
                                   (hx + hr * 0.9, hy - hr * 0.7)])
    elif h == "ears":
        for sd in (-1, 1):
            pygame.draw.polygon(s, ch["body"], [(hx + sd * hr * 0.9, hy - hr * 0.4), (hx + sd * hr * 0.75, hy - hr * 1.6),
                                                (hx + sd * hr * 0.1, hy - hr * 0.9)])
            pygame.draw.line(s, a, (hx + sd * hr * 0.3, hy + hr * 0.3), (hx + sd * hr * 1.2, hy + hr * 0.15), lw)
        pygame.draw.circle(s, a, (hx, int(hy + hr * 0.2)), int(hr * 0.15))
    elif h == "horns":
        for sd in (-1, 1):
            pygame.draw.polygon(s, a, [(hx + sd * hr * 0.9, hy - hr * 0.4), (hx + sd * hr * 0.95, hy - hr * 1.7),
                                       (hx + sd * hr * 0.25, hy - hr * 0.9)])
    elif h == "wizard":
        pygame.draw.polygon(s, (240, 240, 240), [(hx - hr * 0.8, hy + hr * 0.3), (hx + hr * 0.8, hy + hr * 0.3), (hx, hy + hr * 1.5)])
        pygame.draw.polygon(s, ch["body"], [(hx - hr * 1.1, hy - hr * 0.5), (hx + hr * 1.1, hy - hr * 0.5), (hx + hr * 0.1, hy - hr * 2.4)])
        pygame.draw.ellipse(s, ch["body"], (hx - hr * 1.5, hy - hr * 0.75, hr * 3.0, hr * 0.45))
        pygame.draw.circle(s, a, (int(hx), int(hy - hr * 1.2)), int(hr * 0.2))
    elif h == "chef":
        pygame.draw.rect(s, (250, 250, 250), (hx - hr * 0.9, hy - hr * 1.5, hr * 1.8, hr * 0.9))
        for ox in (-0.7, 0, 0.7):
            pygame.draw.circle(s, (250, 250, 250), (int(hx + ox * hr), int(hy - hr * 1.6)), int(hr * 0.55))
        pygame.draw.rect(s, a, (hx - hr * 0.9, hy - hr * 0.8, hr * 1.8, hr * 0.2))
    elif h == "viking":
        for sd in (-1, 1):
            pygame.draw.polygon(s, (245, 240, 220), [(hx + sd * hr * 0.95, hy - hr * 0.6), (hx + sd * hr * 1.7, hy - hr * 1.6),
                                                     (hx + sd * hr * 0.6, hy - hr * 0.95)])
        pygame.draw.rect(s, a, (hx - hr, hy - hr * 1.0, hr * 2, hr * 0.65))
        pygame.draw.rect(s, (200, 110, 40), (hx - hr * 0.6, hy + hr * 0.5, hr * 1.2, hr * 0.9))
    elif h == "cape":
        pygame.draw.rect(s, (20, 20, 25), (hx - hr, hy - hr * 0.35, hr * 2, hr * 0.45))
    elif h == "ghost":
        pygame.draw.circle(s, (40, 50, 90), (hx, int(hy + hr * 0.55)), int(hr * 0.18))
    elif h == "phones":
        pygame.draw.arc(s, a, (hx - hr * 1.2, hy - hr * 1.4, hr * 2.4, hr * 2.2), 0, math.pi, lw + 2)
        for sd in (-1, 1):
            pygame.draw.rect(s, a, (hx + sd * hr * 1.15 - hr * 0.2, hy - hr * 0.3, hr * 0.4, hr * 0.7))
        pygame.draw.rect(s, (10, 10, 10), (hx - hr * 0.9, hy - hr * 0.3, hr * 1.8, hr * 0.4))
    elif h == "dino":
        for i in (-1, 0, 1):
            pygame.draw.polygon(s, a, [(hx + i * hr * 0.6 - hr * 0.3, hy - hr * 0.9), (hx + i * hr * 0.6, hy - hr * 1.6),
                                       (hx + i * hr * 0.6 + hr * 0.3, hy - hr * 0.9)])
        pygame.draw.ellipse(s, (170, 235, 150), (hx - hr * 0.55, hy + hr * 0.05, hr * 1.1, hr * 0.7))
    elif h == "halo":
        pygame.draw.ellipse(s, (255, 230, 90), (hx - hr * 0.8, hy - hr * 1.8, hr * 1.6, hr * 0.45), lw + 2)
    elif h == "samurai":
        pygame.draw.rect(s, a, (hx - hr, hy - hr * 1.0, hr * 2, hr * 0.8))
        pygame.draw.rect(s, (80, 20, 20), (hx - hr * 1.15, hy - hr * 0.3, hr * 2.3, hr * 0.2))
        for sd in (-1, 1):
            pygame.draw.polygon(s, (255, 215, 0), [(hx + sd * hr * 0.15, hy - hr), (hx + sd * hr * 1.1, hy - hr * 2.0), (hx + sd * hr * 0.6, hy - hr * 0.9)])
    elif h == "cowboy":
        pygame.draw.ellipse(s, a, (hx - hr * 1.8, hy - hr * 0.85, hr * 3.6, hr * 0.55))
        pygame.draw.rect(s, a, (hx - hr * 0.8, hy - hr * 1.7, hr * 1.6, hr * 1.0))
        pygame.draw.rect(s, (90, 50, 20), (hx - hr * 0.8, hy - hr * 0.95, hr * 1.6, hr * 0.2))
    elif h == "penguin":
        pygame.draw.circle(s, (25, 25, 35), (hx, hy), int(hr))
        pygame.draw.ellipse(s, (250, 250, 250), (hx - hr * 0.65, hy - hr * 0.1, hr * 1.3, hr * 0.95))
        pygame.draw.polygon(s, a, [(hx - hr * 0.22, hy + hr * 0.2), (hx + hr * 0.22, hy + hr * 0.2), (hx, hy + hr * 0.55)])
    elif h == "fox":
        for sd in (-1, 1):
            pygame.draw.polygon(s, ch["body"], [(hx + sd * hr * 0.95, hy - hr * 0.3), (hx + sd * hr * 0.8, hy - hr * 1.7), (hx + sd * hr * 0.1, hy - hr * 0.9)])
            pygame.draw.polygon(s, a, [(hx + sd * hr * 1.0, hy + hr * 0.2), (hx + sd * hr * 0.2, hy + hr * 0.4), (hx + sd * hr * 0.9, hy + hr * 0.85)])
        pygame.draw.circle(s, (30, 20, 20), (hx, int(hy + hr * 0.3)), int(hr * 0.14))
    elif h == "mummy":
        for i in range(4):
            pygame.draw.line(s, (235, 225, 200), (hx - hr, hy - hr * 0.6 + i * hr * 0.42), (hx + hr, hy - hr * 0.4 + i * hr * 0.42), lw + 1)
    elif h == "knight":
        pygame.draw.rect(s, a, (hx - hr, hy - hr * 1.0, hr * 2, hr * 1.25))
        pygame.draw.rect(s, (30, 30, 40), (hx - hr * 0.85, hy - hr * 0.2, hr * 1.7, hr * 0.22))
        pygame.draw.polygon(s, (220, 40, 40), [(hx, hy - hr), (hx + hr * 0.2, hy - hr * 1.9), (hx + hr * 0.9, hy - hr * 1.25)])
    elif h == "alien":
        pygame.draw.circle(s, ch["skin"], (hx, int(hy - hr * 0.15)), int(hr * 1.25))
        for sd in (-1, 1):
            pygame.draw.ellipse(s, (15, 15, 25), (hx + sd * hr * 0.55 - hr * 0.4, hy - hr * 0.45, hr * 0.8, hr * 0.55))
            pygame.draw.line(s, a, (hx + sd * hr * 0.5, hy - hr * 1.2), (hx + sd * hr * 0.9, hy - hr * 1.9), lw)
            pygame.draw.circle(s, a, (int(hx + sd * hr * 0.9), int(hy - hr * 1.95)), max(2, int(hr * 0.15)))
    elif h == "pumpkin":
        pygame.draw.circle(s, ch["skin"], (hx, hy), int(hr * 1.15))
        pygame.draw.rect(s, a, (hx - hr * 0.1, hy - hr * 1.55, hr * 0.2, hr * 0.45))
        for sd in (-1, 1):
            pygame.draw.polygon(s, (255, 235, 80), [(hx + sd * hr * 0.7, hy - hr * 0.1), (hx + sd * hr * 0.2, hy - hr * 0.1), (hx + sd * hr * 0.45, hy - hr * 0.5)])
        pygame.draw.polygon(s, (255, 235, 80), [(hx - hr * 0.6, hy + hr * 0.3), (hx + hr * 0.6, hy + hr * 0.3), (hx + hr * 0.3, hy + hr * 0.7),
                                                (hx, hy + hr * 0.4), (hx - hr * 0.3, hy + hr * 0.7)])
    elif h == "snowman":
        pygame.draw.rect(s, (25, 25, 30), (hx - hr * 0.7, hy - hr * 1.8, hr * 1.4, hr * 1.0))
        pygame.draw.rect(s, (25, 25, 30), (hx - hr * 1.1, hy - hr * 0.85, hr * 2.2, hr * 0.2))
        pygame.draw.polygon(s, (255, 140, 30), [(hx, hy - hr * 0.05), (hx, hy + hr * 0.2), (hx + hr * 0.95, hy + hr * 0.1)])
        pygame.draw.rect(s, a, (hx - hr, hy + hr * 0.85, hr * 2, hr * 0.3))
    elif h == "emperor":
        pygame.draw.polygon(s, a, [(hx - hr * 1.0, hy - hr * 0.7), (hx - hr * 1.0, hy - hr * 1.9), (hx - hr * 0.5, hy - hr * 1.2),
                                   (hx, hy - hr * 2.1), (hx + hr * 0.5, hy - hr * 1.2), (hx + hr * 1.0, hy - hr * 1.9),
                                   (hx + hr * 1.0, hy - hr * 0.7)])
        pygame.draw.circle(s, (230, 30, 60), (hx, int(hy - hr * 1.3)), max(2, int(hr * 0.15)))
        pygame.draw.rect(s, a, (hx - hr * 0.95, hy - hr * 0.3, hr * 1.9, hr * 0.45))
    elif h == "archer":
        pygame.draw.polygon(s, a, [(hx - hr * 1.1, hy - hr * 0.5), (hx + hr * 1.1, hy - hr * 0.5), (hx + hr * 0.2, hy - hr * 1.7)])
        pygame.draw.polygon(s, (230, 50, 50), [(hx + hr * 0.2, hy - hr * 1.6), (hx + hr * 1.3, hy - hr * 2.0), (hx + hr * 0.7, hy - hr * 1.3)])
    elif h == "miner":
        pygame.draw.rect(s, a, (hx - hr, hy - hr * 1.0, hr * 2, hr * 0.7))
        pygame.draw.rect(s, (200, 150, 30), (hx - hr * 1.2, hy - hr * 0.4, hr * 2.4, hr * 0.15))
        pygame.draw.circle(s, (255, 255, 230), (hx, int(hy - hr * 0.75)), max(2, int(hr * 0.22)))
    elif h == "bee":
        for sd in (-1, 1):
            pygame.draw.line(s, (30, 30, 30), (hx + sd * hr * 0.3, hy - hr), (hx + sd * hr * 0.7, hy - hr * 1.8), lw)
            pygame.draw.circle(s, (30, 30, 30), (int(hx + sd * hr * 0.7), int(hy - hr * 1.85)), max(2, int(hr * 0.15)))
        pygame.draw.rect(s, (30, 30, 30), (hx - hr, hy - hr * 0.55, hr * 2, hr * 0.14))
    elif h == "bear":
        for sd in (-1, 1):
            pygame.draw.circle(s, ch["body"], (int(hx + sd * hr * 0.8), int(hy - hr * 0.85)), int(hr * 0.42))
            pygame.draw.circle(s, (220, 170, 130), (int(hx + sd * hr * 0.8), int(hy - hr * 0.85)), int(hr * 0.22))
        pygame.draw.ellipse(s, (230, 190, 140), (hx - hr * 0.45, hy + hr * 0.05, hr * 0.9, hr * 0.6))
        pygame.draw.circle(s, (40, 25, 20), (hx, int(hy + hr * 0.2)), max(2, int(hr * 0.13)))
    elif h == "unicorn":
        pygame.draw.polygon(s, (255, 225, 120), [(hx - hr * 0.18, hy - hr), (hx + hr * 0.18, hy - hr), (hx, hy - hr * 2.2)])
        for k in range(4):
            pygame.draw.circle(s, RAINBOW[k + 1], (int(hx - hr * 0.95), int(hy - hr * 0.6 + k * hr * 0.4)), max(2, int(hr * 0.24)))
    elif h == "flame":
        for i in (-1, 0, 1):
            tip = 1.9 if i == 0 else 1.5
            pygame.draw.polygon(s, (255, 110, 20), [(hx + i * hr * 0.7 - hr * 0.4, hy - hr * 0.6), (hx + i * hr * 0.7, hy - hr * tip), (hx + i * hr * 0.7 + hr * 0.4, hy - hr * 0.6)])
            pygame.draw.polygon(s, a, [(hx + i * hr * 0.7 - hr * 0.2, hy - hr * 0.6), (hx + i * hr * 0.7, hy - hr * (tip - 0.4)), (hx + i * hr * 0.7 + hr * 0.2, hy - hr * 0.6)])
    elif h == "ice":
        for i in (-1, 0, 1):
            tip = 1.9 - 0.3 * abs(i)
            pts = [(hx + i * hr * 0.65 - hr * 0.28, hy - hr * 0.75), (hx + i * hr * 0.65, hy - hr * tip), (hx + i * hr * 0.65 + hr * 0.28, hy - hr * 0.75)]
            pygame.draw.polygon(s, (170, 230, 255), pts)
            pygame.draw.polygon(s, a, pts, 2)
    elif h == "cyborg":
        pygame.draw.rect(s, (110, 115, 130), (hx - hr, hy - hr * 1.0, hr * 1.1, hr * 0.55))
        pygame.draw.rect(s, a, (hx - hr * 0.9, hy - hr * 0.3, hr * 1.8, hr * 0.3))
        pygame.draw.line(s, (110, 115, 130), (hx + hr * 0.6, hy - hr), (hx + hr * 0.6, hy - hr * 1.6), lw)
        pygame.draw.circle(s, a, (int(hx + hr * 0.6), int(hy - hr * 1.65)), max(2, int(hr * 0.12)))
    elif h == "darkmage":
        pygame.draw.polygon(s, ch["body"], [(hx - hr * 1.2, hy + hr * 0.9), (hx - hr * 1.2, hy - hr * 0.2), (hx, hy - hr * 1.9), (hx + hr * 1.2, hy - hr * 0.2), (hx + hr * 1.2, hy + hr * 0.9)])
        pygame.draw.ellipse(s, (20, 10, 30), (hx - hr * 0.8, hy - hr * 0.6, hr * 1.6, hr * 1.3))
        for sd in (-1, 1):
            pygame.draw.circle(s, a, (int(hx + sd * hr * 0.35), int(hy - hr * 0.05)), max(2, int(hr * 0.15)))
    elif h == "thunder":
        for i in (-2, -1, 0, 1, 2):
            pygame.draw.polygon(s, (255, 225, 80), [(hx + i * hr * 0.4 - hr * 0.25, hy - hr * 0.7), (hx + i * hr * 0.4, hy - hr * (1.5 + 0.2 * (i % 2))), (hx + i * hr * 0.4 + hr * 0.25, hy - hr * 0.7)])
        pygame.draw.polygon(s, a, [(hx + hr * 0.2, hy - hr * 2.5), (hx - hr * 0.35, hy - hr * 1.6), (hx, hy - hr * 1.6), (hx - hr * 0.2, hy - hr * 1.1), (hx + hr * 0.4, hy - hr * 1.85), (hx + hr * 0.05, hy - hr * 1.85)])
    if h not in ("helmet", "phones", "alien", "pumpkin", "emperor", "cyborg", "darkmage"):
        for ex in (-0.3, 0.3):
            pygame.draw.circle(s, (20, 20, 20), (int(hx + ex * hr + hr * 0.15), int(hy)), max(2, int(hr * 0.1)))
    if A.get("neck"):
        draw_neck(A["neck"]["kind"], A["neck"]["col"], cx, bt, u)
    g = A.get("glasses")
    if g:
        if g["kind"] == "heart":
            for sd in (-1, 1):
                pygame.draw.circle(s, g["col"], (int(hx + sd * hr * 0.45), int(hy - hr * 0.05)), max(3, int(hr * 0.38)))
            pygame.draw.line(s, g["col"], (hx - hr * 0.2, hy - hr * 0.05), (hx + hr * 0.2, hy - hr * 0.05), lw + 1)
        else:
            pygame.draw.rect(s, g["col"], (hx - hr * 0.95, hy - hr * 0.28, hr * 1.9, hr * 0.42))
            pygame.draw.line(s, (255, 255, 255), (hx - hr * 0.6, hy - hr * 0.2), (hx - hr * 0.3, hy - hr * 0.2), lw)
    if A.get("pet"):
        draw_pet(A["pet"]["kind"], A["pet"]["col"], cx, by, u)


BG = {}
LV = {}


def lava_loc(L):
    k = L["n"]
    if k not in LV:
        LV[k] = dict(L, n=k + "~", ground=(150, 35, 10), road=(215, 75, 15), line=(255, 210, 60))
    return LV[k]


def build_bg(L):
    surf = pygame.Surface((W, H))
    top, bot = L["sky"]
    bands = 8
    for i in range(bands):
        c = [top[k] + (bot[k] - top[k]) * i // (bands - 1) for k in range(3)]
        surf.fill(c, (0, HOR * i / bands, W, HOR / bands + 2))
    if L["stars"]:
        for x, y, r in STARS:
            pygame.draw.circle(surf, (255, 255, 255), (int(x), int(y)), r)
    sc, sx, sr = L["sun"]
    for rm, kk in ((2.0, 0.18), (1.5, 0.35)):
        hc = tuple(int(bot[i] + (sc[i] - bot[i]) * kk) for i in range(3))
        pygame.draw.circle(surf, hc, (int(W * sx), int(HOR * 0.45)), int(W * sr * rm))
    pygame.draw.circle(surf, sc, (int(W * sx), int(HOR * 0.45)), int(W * sr))
    d = L["dec"]
    if d == "lava":
        pygame.draw.polygon(surf, (35, 20, 20), [(W * 0.05, HOR), (W * 0.3, HOR * 0.3), (W * 0.55, HOR)])
        pygame.draw.polygon(surf, (255, 120, 20), [(W * 0.25, HOR * 0.38), (W * 0.3, HOR * 0.3), (W * 0.35, HOR * 0.38)])
    elif d in ("snow", "desert"):
        col = (200, 215, 235) if d == "snow" else (200, 140, 80)
        pygame.draw.polygon(surf, col, [(W * 0.55, HOR), (W * 0.75, HOR * 0.45), (W * 0.98, HOR)])
        pygame.draw.polygon(surf, col, [(0, HOR), (W * 0.2, HOR * 0.55), (W * 0.45, HOR)])
    elif d == "jungle":
        pygame.draw.ellipse(surf, (30, 100, 60), (-W * 0.2, HOR * 0.45, W * 0.8, HOR * 1.1))
        pygame.draw.ellipse(surf, (20, 80, 50), (W * 0.4, HOR * 0.55, W * 0.9, HOR * 1.0))
    elif d == "beach":
        surf.fill((30, 140, 200), (0, HOR * 0.8, W, HOR * 0.2))
        surf.fill((120, 210, 240), (0, HOR * 0.8, W, HOR * 0.04))
    elif d == "space":
        pygame.draw.circle(surf, (200, 110, 70), (int(W * 0.25), int(HOR * 0.5)), int(W * 0.12))
        pygame.draw.ellipse(surf, (230, 200, 160), (W * 0.08, HOR * 0.45, W * 0.34, HOR * 0.12), 3)
    elif d == "candy":
        for cx, cy, r in ((0.2, 0.5, 0.07), (0.27, 0.45, 0.09), (0.35, 0.5, 0.07), (0.6, 0.65, 0.06), (0.66, 0.6, 0.08), (0.73, 0.65, 0.06)):
            pygame.draw.circle(surf, (255, 255, 255), (int(W * cx), int(HOR * cy)), int(W * r))
    elif d == "ocean":
        for i in range(4):
            x = W * (0.1 + i * 0.25)
            pygame.draw.polygon(surf, (40, 150, 190), [(x, 0), (x + W * 0.06, 0), (x + W * 0.2, HOR), (x + W * 0.08, HOR)])
        for i in range(10):
            pygame.draw.circle(surf, (170, 235, 250), (int(W * ((i * 0.37) % 1)), int(HOR * ((i * 0.23) % 0.9))), 4, 2)
    elif d == "sakura":
        pygame.draw.polygon(surf, (110, 130, 170), [(W * 0.3, HOR), (W * 0.55, HOR * 0.3), (W * 0.8, HOR)])
        pygame.draw.polygon(surf, (255, 255, 255), [(W * 0.47, HOR * 0.5), (W * 0.55, HOR * 0.3), (W * 0.63, HOR * 0.5),
                                                    (W * 0.58, HOR * 0.44), (W * 0.55, HOR * 0.53), (W * 0.51, HOR * 0.44)])
    elif d == "mesa":
        pygame.draw.polygon(surf, (170, 80, 50), [(W * 0.08, HOR), (W * 0.14, HOR * 0.5), (W * 0.36, HOR * 0.5), (W * 0.42, HOR)])
        pygame.draw.polygon(surf, (150, 70, 45), [(W * 0.6, HOR), (W * 0.65, HOR * 0.62), (W * 0.85, HOR * 0.62), (W * 0.92, HOR)])
    elif d == "spooky":
        pygame.draw.polygon(surf, (15, 10, 25), [(0, HOR), (W * 0.1, HOR * 0.6), (W * 0.2, HOR * 0.8), (W * 0.35, HOR * 0.5), (W * 0.5, HOR)])
    elif d == "synth":
        r = int(W * 0.16)
        for k in range(5):
            surf.fill((50, 5, 90), (W * 0.5 - r, HOR * 0.45 + k * r * 0.22, r * 2, max(2, r * 0.05 * (k + 1))))
    elif d == "crystal":
        for i in range(9):
            x = W * i / 8
            pygame.draw.polygon(surf, (25, 20, 50), [(x - W * 0.07, 0), (x + W * 0.07, 0), (x, HOR * (0.2 + 0.3 * ((i * 7) % 5) / 5))])
    elif d == "farm":
        pygame.draw.ellipse(surf, (90, 160, 70), (-W * 0.3, HOR * 0.5, W * 0.9, HOR * 1.2))
        pygame.draw.ellipse(surf, (70, 140, 60), (W * 0.3, HOR * 0.6, W * 1.0, HOR * 1.0))
        wx, wy = int(W * 0.72), int(HOR * 0.55)
        pygame.draw.polygon(surf, (235, 225, 210), [(wx - W * 0.03, HOR * 0.95), (wx + W * 0.03, HOR * 0.95), (wx + W * 0.015, wy), (wx - W * 0.015, wy)])
        for ang in (0.3, 1.9, 3.5, 5.1):
            pygame.draw.line(surf, (240, 240, 240), (wx, wy), (wx + math.cos(ang) * W * 0.09, wy + math.sin(ang) * W * 0.09), 4)
    elif d == "carnival":
        cx_, cy_, r_ = int(W * 0.72), int(HOR * 0.5), int(W * 0.17)
        pygame.draw.circle(surf, (255, 230, 90), (cx_, cy_), r_, 3)
        for k in range(8):
            ang = k * math.pi / 4
            ex, ey = cx_ + math.cos(ang) * r_, cy_ + math.sin(ang) * r_
            pygame.draw.line(surf, (255, 230, 90), (cx_, cy_), (ex, ey), 2)
            pygame.draw.circle(surf, RAINBOW[k % 6], (int(ex), int(ey)), max(3, int(W * 0.012)))
        pygame.draw.line(surf, (200, 200, 220), (cx_, cy_), (cx_ - r_ * 0.6, HOR), 3)
        pygame.draw.line(surf, (200, 200, 220), (cx_, cy_), (cx_ + r_ * 0.6, HOR), 3)
    elif d == "metro":
        for k in range(7):
            hw = W * (0.5 - k * 0.06)
            top_ = HOR * (0.02 + k * 0.1)
            c = max(25, 85 - k * 8)
            pygame.draw.rect(surf, (c, c + 5, c + 15), (W * 0.5 - hw, top_, hw * 2, HOR - top_), 3)
        for k in range(5):
            pygame.draw.circle(surf, (255, 230, 150), (int(W * 0.5), int(HOR * (0.1 + k * 0.1))), max(2, 6 - k))
    elif d == "factory":
        for k in range(8):
            x_ = W * (0.03 + k * 0.13)
            h_ = HOR * (0.35 + 0.35 * ((k * 5) % 4) / 4)
            pygame.draw.rect(surf, (45, 40, 40), (x_, HOR - h_, W * 0.05, h_))
            pygame.draw.circle(surf, (95, 88, 85), (int(x_ + W * 0.03), int(HOR - h_ - W * 0.02)), int(W * 0.035))
    elif d == "sky":
        for k, c in enumerate(RAINBOW):
            pygame.draw.arc(surf, c, (W * 0.05 - k * 5, HOR * 0.25 - k * 5, W * 0.9 + k * 10, HOR * 1.5), 0, math.pi, 6)
        for k in range(7):
            pygame.draw.circle(surf, (255, 255, 255), (int(W * (0.05 + k * 0.15)), int(HOR * 0.98)), int(W * (0.07 + 0.02 * (k % 2))))
    surf.fill(L["ground"], (0, HOR, W, H - HOR))
    return surf


def draw_world(L, off, lava=False):
    if lava:
        L = lava_loc(L)
    key = L["n"]
    if key not in BG:
        BG[key] = build_bg(L)
    screen.blit(BG[key], (0, 0))
    draw_clouds(L, off)
    draw_ground(L, off)

    x0l, y0, _ = proj(-1.5, 0)
    x0r, _, _ = proj(1.5, 0)
    x1l, y1, _ = proj(-1.5, 1.3)
    x1r, _, _ = proj(1.5, 1.3)
    pygame.draw.polygon(screen, L["road"], [(x0l, y0), (x0r, y0), (x1r, y1), (x1l, y1)])
    for i in range(13):
        t = (i * 0.1 + off) % 1.3
        if t < 0.01:
            continue
        a, ya, _ = proj(-1.5, t)
        b, _, _ = proj(1.5, t)
        dark = tuple(max(0, c - 18) for c in L["road"])
        pygame.draw.line(screen, dark, (a, ya), (b, ya), 2)
    for l in (-0.5, 0.5):
        a, ya, _ = proj(l, 0)
        b, yb, _ = proj(l, 1.3)
        pygame.draw.line(screen, L["line"], (a, ya), (b, yb), 3)
    for l in (-1.5, 1.5):
        a, ya, _ = proj(l, 0)
        b, yb, _ = proj(l, 1.3)
        pygame.draw.line(screen, L["line"], (a, ya), (b, yb), 5)
    if lava:
        for i in range(14):
            t = (i * 0.093 + off) % 1.3
            if t < 0.03:
                continue
            ln = ((i * 37) % 7 - 3) * 0.5
            x, y, sc = proj(ln, t)
            pygame.draw.circle(screen, (255, 200, 60), (int(x), int(y)), max(1, int(W * 0.012 * sc)))

    items = []
    for i in range(10):
        t = (i * 0.12 + off) % 1.2
        if t > 0.03:
            items.append((t, i))
    items.sort()
    d = L["dec"]
    for t, i in items:
        v = (i * 7 % 5) / 5
        for side in (-1, 1):
            x, y, sc = proj(side * 2.4, t)
            if d == "city":
                w, h = W * 0.17 * sc, H * (0.18 + 0.15 * v) * sc
                col = [(120, 130, 150), (150, 120, 120), (110, 140, 160), (160, 160, 120), (130, 110, 150)][i % 5]
                pygame.draw.rect(screen, col, (x - w / 2, y - h, w, h))
                for r in range(3):
                    pygame.draw.rect(screen, (255, 240, 160), (x - w * 0.3, y - h * (0.8 - r * 0.25), w * 0.2, h * 0.1))
                    pygame.draw.rect(screen, (255, 240, 160), (x + w * 0.1, y - h * (0.8 - r * 0.25), w * 0.2, h * 0.1))
            elif d == "desert":
                h = H * (0.12 + 0.06 * v) * sc
                w = W * 0.03 * sc
                c = (40, 130, 60)
                pygame.draw.rect(screen, c, (x - w / 2, y - h, w, h))
                pygame.draw.rect(screen, c, (x - w * 2, y - h * 0.65, w * 1.5, w * 0.8))
                pygame.draw.rect(screen, c, (x - w * 2, y - h * 0.8, w * 0.8, h * 0.2))
                pygame.draw.rect(screen, c, (x + w / 2, y - h * 0.5, w * 1.5, w * 0.8))
                pygame.draw.rect(screen, c, (x + w * 1.2, y - h * 0.65, w * 0.8, h * 0.2))
            elif d == "snow":
                h = H * (0.16 + 0.08 * v) * sc
                w = W * 0.08 * sc
                pygame.draw.rect(screen, (90, 60, 40), (x - w * 0.1, y - h * 0.15, w * 0.2, h * 0.15))
                pygame.draw.polygon(screen, (30, 110, 70), [(x - w, y - h * 0.12), (x + w, y - h * 0.12), (x, y - h)])
                pygame.draw.polygon(screen, (255, 255, 255), [(x - w * 0.35, y - h * 0.7), (x + w * 0.35, y - h * 0.7), (x, y - h)])
            elif d == "neon":
                h = H * (0.2 + 0.12 * v) * sc
                w = W * 0.14 * sc
                col = (0, 255, 230) if i % 2 else (255, 40, 200)
                pygame.draw.rect(screen, (15, 10, 35), (x - w / 2, y - h, w, h))
                pygame.draw.rect(screen, col, (x - w / 2, y - h, w, h), max(1, int(3 * sc)))
                pygame.draw.circle(screen, col, (int(x), int(y - h * 0.6)), max(2, int(w * 0.18)))
            elif d == "lava":
                h = H * (0.1 + 0.08 * v) * sc
                w = W * 0.09 * sc
                pygame.draw.polygon(screen, (25, 20, 25), [(x - w, y), (x - w * 0.3, y - h), (x + w * 0.4, y - h * 0.8), (x + w, y)])
                pygame.draw.line(screen, (255, 120, 20), (x - w * 0.1, y - h * 0.9), (x, y - h * 0.2), max(1, int(3 * sc)))
            elif d == "jungle":
                h = H * (0.14 + 0.07 * v) * sc
                w = W * 0.03 * sc
                pygame.draw.rect(screen, (90, 60, 30), (x - w / 2, y - h, w, h))
                r = int(W * 0.09 * sc)
                pygame.draw.circle(screen, (30, 130, 50), (int(x), int(y - h)), r)
                pygame.draw.circle(screen, (60, 170, 70), (int(x - r * 0.4), int(y - h - r * 0.3)), int(r * 0.6))
            elif d == "beach":
                h = H * (0.14 + 0.06 * v) * sc
                tx = x + side * W * 0.02 * sc
                pygame.draw.line(screen, (150, 100, 50), (x, y), (tx, y - h), max(2, int(W * 0.015 * sc)))
                for ang in (-2.6, -2.0, -1.2, -0.5):
                    ex = tx + math.cos(ang) * W * 0.07 * sc
                    ey = y - h + math.sin(ang) * W * 0.05 * sc + W * 0.02 * sc
                    pygame.draw.line(screen, (40, 160, 60), (tx, y - h), (ex, ey), max(2, int(W * 0.012 * sc)))
            elif d == "space":
                h = H * (0.08 + 0.1 * v) * sc
                w = W * 0.06 * sc
                col = (120, 220, 255) if i % 2 else (200, 120, 255)
                pygame.draw.polygon(screen, col, [(x - w / 2, y), (x - w * 0.1, y - h), (x + w * 0.2, y - h * 0.6), (x + w / 2, y)])
                pygame.draw.polygon(screen, (255, 255, 255), [(x - w * 0.1, y - h), (x, y - h * 0.8), (x - w * 0.15, y - h * 0.7)])
            elif d == "candy":
                h = H * (0.12 + 0.06 * v) * sc
                r = int(W * 0.06 * sc)
                pygame.draw.rect(screen, (255, 255, 255), (x - W * 0.006 * sc, y - h, W * 0.012 * sc, h))
                col = [(255, 80, 140), (255, 200, 40), (80, 200, 255), (160, 100, 255)][i % 4]
                pygame.draw.circle(screen, col, (int(x), int(y - h)), r)
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y - h)), max(2, int(r * 0.6)), max(1, int(3 * sc)))
                pygame.draw.circle(screen, col, (int(x), int(y - h)), max(1, int(r * 0.25)))
            elif d == "ocean":
                h = H * (0.1 + 0.07 * v) * sc
                w = W * 0.012 * sc
                col = (255, 120, 100) if i % 2 else (255, 170, 60)
                pygame.draw.rect(screen, col, (x - w / 2, y - h, w, h))
                pygame.draw.rect(screen, col, (x - w * 3, y - h * 0.7, w * 2.5, w))
                pygame.draw.rect(screen, col, (x - w * 3, y - h * 0.95, w, h * 0.3))
                pygame.draw.rect(screen, col, (x + w * 0.5, y - h * 0.55, w * 2.5, w))
                pygame.draw.rect(screen, col, (x + w * 2, y - h * 0.8, w, h * 0.3))
                pygame.draw.circle(screen, (190, 240, 255), (int(x + w * 4), int(y - h * 1.3)), max(2, int(W * 0.01 * sc)), 2)
            elif d == "sakura":
                h = H * (0.13 + 0.06 * v) * sc
                w = W * 0.025 * sc
                pygame.draw.rect(screen, (90, 60, 45), (x - w / 2, y - h, w, h))
                r = int(W * 0.08 * sc)
                pygame.draw.circle(screen, (255, 170, 200), (int(x), int(y - h)), r)
                pygame.draw.circle(screen, (255, 205, 225), (int(x - r * 0.5), int(y - h - r * 0.2)), int(r * 0.6))
                pygame.draw.circle(screen, (255, 140, 180), (int(x + r * 0.5), int(y - h + r * 0.1)), int(r * 0.5))
            elif d == "mesa":
                h = H * (0.1 + 0.1 * v) * sc
                w = W * 0.07 * sc
                pygame.draw.rect(screen, (165, 85, 55), (x - w / 2, y - h, w, h))
                pygame.draw.rect(screen, (205, 125, 85), (x - w / 2, y - h * 0.65, w, h * 0.1))
                pygame.draw.rect(screen, (205, 125, 85), (x - w / 2, y - h * 0.35, w, h * 0.1))
                pygame.draw.rect(screen, (140, 70, 45), (x - w * 0.65, y - h, w * 1.3, h * 0.15))
            elif d == "spooky":
                if i % 2:
                    h = H * 0.09 * sc
                    w = W * 0.05 * sc
                    pygame.draw.rect(screen, (110, 110, 125), (x - w / 2, y - h, w, h))
                    pygame.draw.circle(screen, (110, 110, 125), (int(x), int(y - h)), max(2, int(w / 2)))
                    pygame.draw.line(screen, (60, 60, 70), (x, y - h * 0.9), (x, y - h * 0.5), max(1, int(3 * sc)))
                    pygame.draw.line(screen, (60, 60, 70), (x - w * 0.2, y - h * 0.75), (x + w * 0.2, y - h * 0.75), max(1, int(3 * sc)))
                else:
                    h = H * (0.15 + 0.05 * v) * sc
                    w = W * 0.02 * sc
                    pygame.draw.rect(screen, (30, 25, 35), (x - w / 2, y - h, w, h))
                    pygame.draw.line(screen, (30, 25, 35), (x, y - h * 0.7), (x - W * 0.05 * sc, y - h * 1.05), max(2, int(4 * sc)))
                    pygame.draw.line(screen, (30, 25, 35), (x, y - h * 0.85), (x + W * 0.05 * sc, y - h * 1.15), max(2, int(4 * sc)))
            elif d == "synth":
                h = H * (0.12 + 0.12 * v) * sc
                w = W * 0.1 * sc
                col = (0, 255, 255) if i % 2 else (255, 60, 200)
                pygame.draw.polygon(screen, (20, 5, 45), [(x - w / 2, y), (x, y - h), (x + w / 2, y)])
                pygame.draw.polygon(screen, col, [(x - w / 2, y), (x, y - h), (x + w / 2, y)], max(1, int(3 * sc)))
            elif d == "farm":
                if i % 2 == 0:
                    w = W * 0.13 * sc
                    h = H * (0.1 + 0.03 * v) * sc
                    pygame.draw.rect(screen, (170, 50, 40), (x - w / 2, y - h, w, h))
                    pygame.draw.polygon(screen, (110, 30, 25), [(x - w * 0.6, y - h), (x + w * 0.6, y - h), (x, y - h * 1.5)])
                    pygame.draw.rect(screen, (250, 250, 245), (x - w * 0.2, y - h * 0.6, w * 0.4, h * 0.6), max(1, int(2 * sc)))
                    pygame.draw.line(screen, (250, 250, 245), (x - w * 0.2, y - h * 0.6), (x + w * 0.2, y), max(1, int(2 * sc)))
                    pygame.draw.line(screen, (250, 250, 245), (x + w * 0.2, y - h * 0.6), (x - w * 0.2, y), max(1, int(2 * sc)))
                else:
                    w = W * 0.05 * sc
                    h = H * (0.15 + 0.04 * v) * sc
                    pygame.draw.rect(screen, (190, 195, 205), (x - w / 2, y - h, w, h))
                    pygame.draw.circle(screen, (150, 155, 170), (int(x), int(y - h)), max(2, int(w / 2)))
                    for k in range(3):
                        pygame.draw.line(screen, (150, 155, 170), (x - w / 2, y - h * (0.2 + 0.25 * k)), (x + w / 2, y - h * (0.2 + 0.25 * k)), max(1, int(2 * sc)))
            elif d == "carnival":
                if i % 2 == 0:
                    w = W * 0.13 * sc
                    h = H * (0.1 + 0.03 * v) * sc
                    pygame.draw.rect(screen, (240, 240, 240), (x - w / 2, y - h * 0.6, w, h * 0.6))
                    for k in range(4):
                        pygame.draw.rect(screen, (220, 50, 70), (x - w / 2 + w * k / 4, y - h * 0.6, w / 8, h * 0.6))
                    pygame.draw.polygon(screen, (220, 50, 70), [(x - w * 0.6, y - h * 0.6), (x + w * 0.6, y - h * 0.6), (x, y - h * 1.2)])
                    pygame.draw.line(screen, (255, 230, 90), (x, y - h * 1.2), (x, y - h * 1.5), max(1, int(2 * sc)))
                    pygame.draw.polygon(screen, (255, 230, 90), [(x, y - h * 1.5), (x + w * 0.2, y - h * 1.42), (x, y - h * 1.35)])
                else:
                    h = H * (0.14 + 0.04 * v) * sc
                    w = W * 0.012 * sc
                    pygame.draw.rect(screen, (90, 70, 120), (x - w / 2, y - h, w, h))
                    for k in range(5):
                        pygame.draw.circle(screen, RAINBOW[(i + k) % 6], (int(x), int(y - h * (0.25 + 0.17 * k))), max(2, int(W * 0.012 * sc)))
            elif d == "metro":
                w = W * 0.06 * sc
                h = H * 0.24 * sc
                pygame.draw.rect(screen, (125, 130, 142), (x - w / 2, y - h, w, h))
                for k in range(4):
                    pygame.draw.line(screen, (95, 100, 112), (x - w / 2, y - h * (0.2 + 0.2 * k)), (x + w / 2, y - h * (0.2 + 0.2 * k)), max(1, int(2 * sc)))
                pygame.draw.rect(screen, (255, 200, 50), (x - w / 2, y - h * 0.12, w, h * 0.05))
                pygame.draw.circle(screen, (255, 235, 150), (int(x - side * w * 0.9), int(y - h * 0.85)), max(3, int(w * 0.35)))
                pygame.draw.rect(screen, (70, 72, 82), (x - w * 0.6, y - h * 1.0, w * 1.2, h * 0.06))
            elif d == "factory":
                if i % 2 == 0:
                    w = W * 0.05 * sc
                    h = H * (0.18 + 0.1 * v) * sc
                    pygame.draw.rect(screen, (150, 80, 60), (x - w / 2, y - h, w, h))
                    pygame.draw.rect(screen, (240, 240, 240), (x - w / 2, y - h, w, h * 0.08))
                    for k in range(3):
                        g_ = 120 + k * 15
                        pygame.draw.circle(screen, (g_, g_ - 5, g_ - 5), (int(x + k * w * 0.4), int(y - h - w * (0.6 + k * 0.8))), max(2, int(w * (0.5 + k * 0.25))))
                else:
                    w = W * 0.14 * sc
                    h = H * (0.09 + 0.04 * v) * sc
                    pygame.draw.rect(screen, (95, 95, 105), (x - w / 2, y - h, w, h))
                    pygame.draw.polygon(screen, (70, 70, 80), [(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2, y - h * 1.3), (x - w / 2, y - h)])
                    for k in range(3):
                        pygame.draw.rect(screen, (255, 210, 90), (x - w * 0.4 + k * w * 0.28, y - h * 0.7, w * 0.18, h * 0.25))
            elif d == "sky":
                w = W * 0.04 * sc
                h = H * (0.16 + 0.06 * v) * sc
                pygame.draw.rect(screen, (250, 250, 255), (x - w / 2, y - h, w, h))
                pygame.draw.rect(screen, (255, 215, 100), (x - w * 0.8, y - h * 1.05, w * 1.6, h * 0.07))
                pygame.draw.rect(screen, (255, 215, 100), (x - w * 0.7, y - h * 0.05, w * 1.4, h * 0.05))
                r = int(W * 0.04 * sc)
                for ox in (-1.0, 0.0, 1.0):
                    pygame.draw.circle(screen, (255, 255, 255), (int(x + ox * r), int(y)), r)
            else:  # crystal
                h = H * (0.08 + 0.1 * v) * sc
                w = W * 0.05 * sc
                cols = [(100, 220, 255), (255, 120, 220), (120, 255, 170)]
                for k, ox in enumerate((-0.6, 0.0, 0.6)):
                    c = cols[(i + k) % 3]
                    hh = h * (1.0 - 0.3 * abs(ox))
                    pygame.draw.polygon(screen, c, [(x + ox * w - w * 0.3, y), (x + ox * w, y - hh), (x + ox * w + w * 0.3, y)])

    draw_decor2(L, off)
    draw_fx(L, off)


def draw_clouds(L, off):
    d = L["dec"]
    if L["stars"] or d in NOCLOUD:
        return
    col = CLOUDCOL.get(d, (255, 255, 255))
    n = 7 if d == "sky" else 4
    for i in range(n):
        x = ((i * 0.29 + off * 0.012 * (1 + i % 2)) % 1.3 - 0.15) * W
        y = HOR * (0.12 + 0.18 * ((i * 3) % 4) / 4)
        r = W * (0.05 + 0.015 * (i % 3))
        pygame.draw.circle(screen, col, (int(x), int(y)), int(r))
        pygame.draw.circle(screen, col, (int(x + r * 0.9), int(y + r * 0.15)), int(r * 0.8))
        pygame.draw.circle(screen, col, (int(x - r * 0.9), int(y + r * 0.2)), int(r * 0.7))
        pygame.draw.rect(screen, col, (x - r * 1.5, y + r * 0.3, r * 3.0, r * 0.5))


def draw_ground(L, off):
    g = L["ground"]
    lt = tuple(min(255, c + 14) for c in g)
    for i in range(10):
        t0 = (i * 0.13 + off) % 1.3
        y0 = HOR + (PY - HOR) * t0
        y1 = HOR + (PY - HOR) * (t0 + 0.065)
        if y0 > H:
            continue
        screen.fill(lt, (0, y0, W, y1 - y0 + 1))


def draw_fx(L, off):
    d = L["dec"]
    k = FX.get(d)
    if not k:
        return
    for i in range(28):
        bx = ((i * 53) % 97) / 97.0
        sp = 0.6 + ((i * 29) % 7) / 7.0
        ph = (i * 0.173 + off * 0.35 * sp) % 1.0
        sway = math.sin(off * 1.6 + i) * 0.03
        if k == "dust":
            x = ((bx + off * 0.12 * sp) % 1.0) * W
            y = H * (0.3 + 0.6 * ((i * 17) % 10) / 10)
            pygame.draw.circle(screen, (235, 205, 150), (int(x), int(y)), 2)
        elif k == "twinkle":
            if math.sin(off * 5 + i * 1.7) > 0.2:
                x = bx * W
                y = ((i * 31) % 100) / 100.0 * H * 0.85
                pygame.draw.circle(screen, (255, 255, 255) if i % 3 else (255, 230, 150), (int(x), int(y)), 1 + i % 2)
        elif k in ("ember", "bubble"):
            x = (bx + sway) * W
            y = (1.0 - ph) * H
            if k == "ember":
                col = (190, 90, 255) if d == "spooky" else ((220, 220, 220) if (d == "factory" and i % 2) else (255, 150, 40))
                pygame.draw.circle(screen, col, (int(x), int(y)), 2 + i % 2)
            else:
                pygame.draw.circle(screen, (200, 240, 255), (int(x), int(y)), 3 + i % 4, 1)
        else:
            x = (bx + sway) * W
            y = ph * H
            if k == "snow":
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 2 + i % 2)
            elif k == "petal":
                pygame.draw.ellipse(screen, (255, 185, 210), (x, y, 7, 4))
            elif k == "leaf":
                pygame.draw.rect(screen, (90, 170, 60) if i % 2 else (210, 170, 50), (x, y, 5, 3))
            elif k == "confetti":
                pygame.draw.rect(screen, RAINBOW[i % 6], (x, y, 4, 7))
            else:
                pygame.draw.rect(screen, RAINBOW[i % 6], (x, y, 6, 2))


def draw_decor2(L, off):
    d = L["dec"]
    s = screen
    for i in range(12):
        t = (i * 0.1 + off + 0.05) % 1.25
        if t < 0.04:
            continue
        for side in (-1, 1):
            x, y, sc = proj(side * 1.9, t)
            u = W * 0.03 * sc
            j = (i * 5 + (3 if side > 0 else 0)) % 7
            hh = H * 0.08 * sc
            if d == "city":
                pygame.draw.rect(s, (70, 75, 85), (x - u * 0.15, y - hh, u * 0.3, hh))
                pygame.draw.circle(s, (255, 240, 160), (int(x), int(y - hh)), max(2, int(u * 0.5)))
            elif d in ("desert", "mesa"):
                if j % 2:
                    pygame.draw.polygon(s, (150, 110, 70), [(x - u, y), (x - u * 0.4, y - u * 0.8), (x + u * 0.6, y - u * 0.6), (x + u, y)])
                elif d == "desert":
                    pygame.draw.circle(s, (170, 130, 80), (int(x), int(y - u * 0.6)), max(2, int(u * 0.6)), 2)
                else:
                    pygame.draw.rect(s, (150, 95, 55), (x - u * 0.5, y - u * 1.2, u, u * 1.2))
                    pygame.draw.rect(s, (90, 60, 35), (x - u * 0.5, y - u * 0.8, u, u * 0.15))
            elif d == "snow":
                pygame.draw.ellipse(s, (245, 250, 255), (x - u * 1.2, y - u * 0.6, u * 2.4, u * 0.9))
            elif d in ("neon", "synth"):
                col = (0, 255, 230) if j % 2 else (255, 40, 200)
                pygame.draw.rect(s, (30, 20, 60), (x - u * 0.1, y - hh, u * 0.2, hh))
                pygame.draw.circle(s, col, (int(x), int(y - hh)), max(2, int(u * 0.5)))
            elif d == "lava":
                pygame.draw.ellipse(s, (255, 110, 20), (x - u * 1.2, y - u * 0.3, u * 2.4, u * 0.6))
                pygame.draw.ellipse(s, (255, 210, 70), (x - u * 0.6, y - u * 0.2, u * 1.2, u * 0.3))
            elif d == "jungle":
                pygame.draw.circle(s, (30, 120, 50), (int(x), int(y - u * 0.5)), max(2, int(u * 0.8)))
                pygame.draw.circle(s, (55, 165, 75), (int(x + u * 0.5), int(y - u * 0.7)), max(2, int(u * 0.5)))
                pygame.draw.circle(s, RAINBOW[j % 6], (int(x - u * 0.3), int(y - u * 1.1)), max(1, int(u * 0.2)))
            elif d == "beach":
                if j % 2:
                    pygame.draw.rect(s, (200, 200, 200), (x - u * 0.08, y - hh, u * 0.16, hh))
                    pygame.draw.polygon(s, (255, 80, 80) if j % 3 else (255, 255, 255), [(x - u * 1.3, y - hh), (x + u * 1.3, y - hh), (x, y - hh * 1.4)])
                else:
                    pygame.draw.ellipse(s, (255, 200, 200), (x - u * 0.6, y - u * 0.5, u * 1.2, u * 0.5))
            elif d == "space":
                if j % 3:
                    pygame.draw.ellipse(s, (80, 80, 95), (x - u * 1.2, y - u * 0.4, u * 2.4, u * 0.7), 2)
                else:
                    pygame.draw.line(s, (220, 220, 230), (x, y), (x, y - hh), max(1, int(2 * sc)))
                    pygame.draw.polygon(s, (255, 90, 90), [(x, y - hh), (x + u * 1.2, y - hh * 0.85), (x, y - hh * 0.7)])
            elif d == "candy":
                pygame.draw.circle(s, RAINBOW[j % 6], (int(x), int(y - u * 0.4)), max(2, int(u * 0.8)))
                pygame.draw.rect(s, tuple(L["ground"]), (x - u * 0.8, y - u * 0.2, u * 1.6, u * 0.3))
            elif d == "ocean":
                pts = [(x, y), (x - u * 0.3, y - u * 0.8), (x + u * 0.3, y - u * 1.6), (x, y - u * 2.4)]
                pygame.draw.lines(s, (40, 160, 90), False, pts, 3)
                pygame.draw.circle(s, (200, 240, 255), (int(x + u * 0.8), int(y - u * 1.8)), max(2, int(u * 0.3)), 1)
            elif d == "sakura":
                pygame.draw.ellipse(s, (255, 190, 215), (x - u * 1.0, y - u * 0.4, u * 2.0, u * 0.5))
                if j % 3 == 0:
                    pygame.draw.rect(s, (150, 150, 150), (x - u * 0.3, y - u * 1.4, u * 0.6, u * 1.0))
                    pygame.draw.rect(s, (255, 200, 90), (x - u * 0.2, y - u * 1.2, u * 0.4, u * 0.4))
            elif d == "spooky":
                pygame.draw.circle(s, (255, 140, 20), (int(x), int(y - u * 0.5)), max(2, int(u * 0.7)))
                pygame.draw.circle(s, (40, 20, 10), (int(x - u * 0.25), int(y - u * 0.6)), max(1, int(u * 0.12)))
                pygame.draw.circle(s, (40, 20, 10), (int(x + u * 0.25), int(y - u * 0.6)), max(1, int(u * 0.12)))
            elif d == "crystal":
                pygame.draw.polygon(s, (120, 230, 255), [(x - u * 0.6, y), (x - u * 0.3, y - u * 1.4), (x, y)])
                pygame.draw.polygon(s, (255, 130, 230), [(x - u * 0.1, y), (x + u * 0.3, y - u * 1.0), (x + u * 0.7, y)])
            elif d == "farm":
                for ox in (-1.0, 0.0, 1.0):
                    pygame.draw.rect(s, (130, 90, 50), (x + ox * u - u * 0.1, y - u * 1.2, u * 0.2, u * 1.2))
                pygame.draw.rect(s, (160, 120, 70), (x - u * 1.1, y - u * 0.9, u * 2.2, u * 0.15))
                pygame.draw.rect(s, (160, 120, 70), (x - u * 1.1, y - u * 0.5, u * 2.2, u * 0.15))
            elif d == "carnival":
                pygame.draw.line(s, (255, 255, 255), (x, y), (x, y - hh), 1)
                pygame.draw.circle(s, RAINBOW[j % 6], (int(x), int(y - hh)), max(2, int(u * 0.7)))
            elif d == "metro":
                pygame.draw.rect(s, (130, 135, 145), (x - u * 0.35, y - hh * 1.7, u * 0.7, hh * 1.7))
                pygame.draw.rect(s, (255, 200, 50), (x - u * 0.35, y - hh * 1.6, u * 0.7, hh * 0.15))
            elif d == "factory":
                pygame.draw.rect(s, (200, 60, 40), (x - u * 0.5, y - u * 1.2, u, u * 1.2))
                pygame.draw.rect(s, (255, 200, 40), (x - u * 0.5, y - u * 0.8, u, u * 0.2))
            else:  # sky
                for ox in (-0.6, 0.0, 0.6):
                    pygame.draw.ellipse(s, (255, 255, 255), (x + ox * u - u * 0.6, y - u * 0.5, u * 1.2, u * 0.7))


def draw_aura(kind, cx, by, u):
    s = screen
    t = pygame.time.get_ticks() / 1000.0
    cy = by - u * 0.9
    if kind == "afire":
        for k in range(7):
            ang = k * 0.9 + 0.4
            bx_ = cx + math.cos(ang) * u * 0.9
            by_ = cy + math.sin(ang) * u * 1.0
            fl = 0.5 + 0.5 * math.sin(t * 9 + k)
            pygame.draw.polygon(s, (255, 110, 20), [(bx_ - u * 0.18, by_ + u * 0.2), (bx_ + u * 0.18, by_ + u * 0.2), (bx_, by_ - u * (0.4 + 0.3 * fl))])
            pygame.draw.polygon(s, (255, 220, 70), [(bx_ - u * 0.08, by_ + u * 0.2), (bx_ + u * 0.08, by_ + u * 0.2), (bx_, by_ - u * (0.1 + 0.15 * fl))])
    elif kind == "astar":
        for k in range(6):
            ang = t * 2.2 + k * math.pi / 3
            px = cx + math.cos(ang) * u * 1.25
            py = cy + math.sin(ang) * u * 0.9
            pygame.draw.circle(s, (255, 240, 120), (int(px), int(py)), max(2, int(u * 0.12)))
            pygame.draw.circle(s, (255, 255, 255), (int(px), int(py)), max(1, int(u * 0.05)))
    else:
        pygame.draw.ellipse(s, (0, 255, 230), (cx - u * 1.0, cy - u * 1.15, u * 2.0, u * 2.3), 3)
        o = u * 0.1 * math.sin(t * 5)
        pygame.draw.ellipse(s, (255, 60, 200), (cx - u * 1.15 - o, cy - u * 1.3 - o, u * 2.3 + 2 * o, u * 2.6 + 2 * o), 2)


def draw_neck(kind, col, cx, bt, u):
    s = screen
    if kind == "scarf":
        pygame.draw.rect(s, col, (cx - u * 0.5, bt - u * 0.04, u, u * 0.2))
        pygame.draw.polygon(s, col, [(cx + u * 0.25, bt + u * 0.14), (cx + u * 0.55, bt + u * 0.14), (cx + u * 0.45, bt + u * 0.6), (cx + u * 0.2, bt + u * 0.5)])
        pygame.draw.line(s, (255, 255, 255), (cx - u * 0.3, bt + u * 0.06), (cx + u * 0.3, bt + u * 0.06), max(1, int(u * 0.04)))
    elif kind == "chain":
        for k in range(7):
            px = cx - u * 0.4 + k * u * 0.8 / 6
            py = bt + u * 0.1 + math.sin(math.pi * k / 6) * u * 0.28
            pygame.draw.circle(s, col, (int(px), int(py)), max(2, int(u * 0.07)))
    else:
        pygame.draw.polygon(s, (60, 100, 220), [(cx - u * 0.3, bt), (cx + u * 0.3, bt), (cx + u * 0.12, bt + u * 0.5), (cx - u * 0.12, bt + u * 0.5)])
        pygame.draw.circle(s, col, (int(cx), int(bt + u * 0.58)), max(3, int(u * 0.17)))
        pygame.draw.circle(s, (200, 150, 20), (int(cx), int(bt + u * 0.58)), max(3, int(u * 0.17)), 2)


def draw_pet(kind, col, cx, by, u):
    s = screen
    t = pygame.time.get_ticks() / 1000.0
    px = cx + u * 1.55
    if kind == "kitty":
        pygame.draw.ellipse(s, col, (px - u * 0.4, by - u * 0.45, u * 0.8, u * 0.4))
        pygame.draw.circle(s, col, (int(px + u * 0.32), int(by - u * 0.5)), max(2, int(u * 0.23)))
        for sd in (0, 1):
            pygame.draw.polygon(s, col, [(px + u * 0.2 + sd * u * 0.22, by - u * 0.65), (px + u * 0.27 + sd * u * 0.22, by - u * 0.9), (px + u * 0.35 + sd * u * 0.22, by - u * 0.65)])
        pygame.draw.line(s, col, (px - u * 0.4, by - u * 0.35), (px - u * 0.7, by - u * 0.7 + math.sin(t * 8) * u * 0.1), max(2, int(u * 0.07)))
    elif kind == "pdragon":
        pygame.draw.ellipse(s, col, (px - u * 0.4, by - u * 0.5, u * 0.8, u * 0.45))
        pygame.draw.circle(s, col, (int(px + u * 0.38), int(by - u * 0.55)), max(2, int(u * 0.22)))
        pygame.draw.polygon(s, (60, 150, 80), [(px - u * 0.2, by - u * 0.45), (px, by - u * (0.95 + 0.1 * math.sin(t * 10))), (px + u * 0.15, by - u * 0.45)])
        pygame.draw.polygon(s, (255, 140, 30), [(px + u * 0.58, by - u * 0.55), (px + u * 0.95, by - u * 0.6), (px + u * 0.58, by - u * 0.45)])
    else:
        py = by - u * 1.7 + math.sin(t * 3) * u * 0.08
        pygame.draw.ellipse(s, col, (px - u * 0.3, py, u * 0.6, u * 0.28))
        pygame.draw.line(s, (60, 60, 70), (px - u * 0.5, py - u * 0.05), (px + u * 0.5, py - u * 0.05 + math.sin(t * 40) * u * 0.05), max(2, int(u * 0.05)))
        pygame.draw.circle(s, (255, 60, 60), (int(px), int(py + u * 0.14)), max(2, int(u * 0.06)))


def draw_front(kind, ca, cf, xf, yf, wf, th, sf):
    s = screen
    dk = tuple(int(c * 0.45) for c in cf)
    x0, y0 = xf - wf / 2, yf - th
    lw = max(1, int(3 * sf))
    if kind == "metro":
        pygame.draw.rect(s, ca, (xf - wf * 0.35, y0 + th * 0.15, wf * 0.7, th * 0.3))
    elif kind == "wagon":
        for k in range(1, 4):
            pygame.draw.line(s, dk, (x0, y0 + th * k / 4), (x0 + wf, y0 + th * k / 4), max(1, lw - 1))
        pygame.draw.rect(s, ca, (xf - wf * 0.2, y0 + th * 0.35, wf * 0.4, th * 0.25))
    elif kind == "stripes":
        for k in range(5):
            pygame.draw.rect(s, ca, (x0 + wf * (0.1 + k * 0.2), y0, wf * 0.08, th))
        pygame.draw.rect(s, (40, 60, 90), (xf - wf * 0.3, y0 + th * 0.15, wf * 0.6, th * 0.25))
    elif kind == "round":
        for sd in (-1, 1):
            pygame.draw.circle(s, ca, (int(xf + sd * wf * 0.22), int(y0 + th * 0.4)), max(2, int(wf * 0.13)))
            pygame.draw.circle(s, dk, (int(xf + sd * wf * 0.22), int(y0 + th * 0.4)), max(2, int(wf * 0.13)), lw)
    elif kind == "neon":
        pygame.draw.rect(s, ca, (x0, y0, wf, th), lw)
        pygame.draw.line(s, ca, (x0, y0 + th * 0.5), (x0 + wf, y0 + th * 0.5), lw)
    elif kind == "glass":
        pygame.draw.line(s, ca, (x0, yf), (x0 + wf, y0), lw)
        pygame.draw.polygon(s, ca, [(x0 + wf * 0.1, y0 + th * 0.2), (x0 + wf * 0.4, y0 + th * 0.2), (x0 + wf * 0.1, y0 + th * 0.55)])
    elif kind == "rust":
        n = 6
        for k in range(n):
            pygame.draw.rect(s, ca if k % 2 == 0 else (20, 20, 20), (x0 + wf * k / n, yf - th * 0.14, wf / n, th * 0.14))
        pygame.draw.rect(s, ca, (xf - wf * 0.3, y0 + th * 0.2, wf * 0.6, th * 0.22))
    elif kind == "plat":
        pygame.draw.line(s, ca, (x0, y0), (x0 + wf, y0), max(2, int(5 * sf)))
    if kind not in ("neon", "plat"):
        pygame.draw.rect(s, dk, (x0, y0, wf, th), lw)


def draw_low(kind, c1, c2, x, y, w, hh, sc):
    s = screen
    lw = max(1, int(3 * sc))
    if kind == "bar":
        pygame.draw.rect(s, c1, (x - w / 2, y - hh, w, hh))
        pygame.draw.rect(s, c2, (x - w * 0.2, y - hh, w * 0.12, hh))
    elif kind in ("rock", "ice"):
        pts = [(x - w / 2, y), (x - w * 0.3, y - hh * 0.8), (x - w * 0.05, y - hh), (x + w * 0.3, y - hh * 0.7), (x + w / 2, y)]
        pygame.draw.polygon(s, c1, pts)
        pygame.draw.polygon(s, c2, pts, lw)
    elif kind == "neon":
        pygame.draw.rect(s, (15, 10, 35), (x - w / 2, y - hh, w, hh))
        pygame.draw.rect(s, c1, (x - w / 2, y - hh, w, hh), lw + 1)
        pygame.draw.line(s, c2, (x - w / 2, y - hh / 2), (x + w / 2, y - hh / 2), lw)
    elif kind == "log":
        pygame.draw.rect(s, c1, (x - w / 2, y - hh, w, hh))
        pygame.draw.ellipse(s, c2, (x - w / 2 - hh * 0.2, y - hh, hh * 0.5, hh))
        pygame.draw.line(s, c2, (x - w * 0.2, y - hh * 0.6), (x + w * 0.3, y - hh * 0.6), lw)
    elif kind == "ball":
        r = hh * 0.55
        pygame.draw.circle(s, c1, (int(x), int(y - r)), max(2, int(r)))
        pygame.draw.line(s, c2, (x - r, y - r), (x + r, y - r), lw + 1)
        pygame.draw.rect(s, c1, (x - w / 2, y - hh * 0.2, w, hh * 0.2))
    elif kind == "cone":
        pygame.draw.polygon(s, c1, [(x - w * 0.3, y), (x + w * 0.3, y), (x, y - hh)])
        pygame.draw.polygon(s, c2, [(x - w * 0.18, y - hh * 0.4), (x + w * 0.18, y - hh * 0.4), (x + w * 0.1, y - hh * 0.65), (x - w * 0.1, y - hh * 0.65)])
        pygame.draw.rect(s, c1, (x - w * 0.5, y - hh * 0.1, w, hh * 0.1))
    elif kind == "coral":
        for ox, c in ((-0.3, c1), (0.0, c2), (0.3, c1)):
            top = hh * (1.0 if ox == 0 else 0.8)
            pygame.draw.rect(s, c, (x + ox * w - w * 0.07, y - top, w * 0.14, top))
            pygame.draw.circle(s, c, (int(x + ox * w), int(y - top)), max(2, int(w * 0.1)))
    elif kind == "lantern":
        pygame.draw.rect(s, c1, (x - w * 0.15, y - hh * 0.3, w * 0.3, hh * 0.3))
        pygame.draw.rect(s, c2, (x - w * 0.2, y - hh * 0.7, w * 0.4, hh * 0.4))
        pygame.draw.polygon(s, c1, [(x - w * 0.35, y - hh * 0.7), (x + w * 0.35, y - hh * 0.7), (x, y - hh)])
    elif kind == "barrel":
        pygame.draw.rect(s, c1, (x - w * 0.3, y - hh, w * 0.6, hh))
        pygame.draw.rect(s, c2, (x - w * 0.3, y - hh * 0.75, w * 0.6, hh * 0.12))
        pygame.draw.rect(s, c2, (x - w * 0.3, y - hh * 0.3, w * 0.6, hh * 0.12))
    elif kind == "tomb":
        pygame.draw.rect(s, c1, (x - w * 0.3, y - hh * 0.8, w * 0.6, hh * 0.8))
        pygame.draw.circle(s, c1, (int(x), int(y - hh * 0.8)), max(2, int(w * 0.3)))
        pygame.draw.line(s, c2, (x, y - hh * 0.9), (x, y - hh * 0.35), lw)
        pygame.draw.line(s, c2, (x - w * 0.12, y - hh * 0.7), (x + w * 0.12, y - hh * 0.7), lw)
    elif kind == "crystal":
        pygame.draw.polygon(s, c1, [(x - w * 0.35, y), (x - w * 0.15, y - hh), (x + w * 0.05, y)])
        pygame.draw.polygon(s, c2, [(x - w * 0.05, y), (x + w * 0.2, y - hh * 0.8), (x + w * 0.4, y)])
    elif kind == "bale":
        pygame.draw.rect(s, c1, (x - w / 2, y - hh, w, hh))
        for k in range(1, 4):
            pygame.draw.line(s, c2, (x - w / 2 + w * k / 4, y - hh), (x - w / 2 + w * k / 4, y), lw)
    elif kind == "crate":
        pygame.draw.rect(s, c1, (x - w * 0.4, y - hh, w * 0.8, hh))
        pygame.draw.rect(s, c2, (x - w * 0.4, y - hh, w * 0.8, hh), lw)
        pygame.draw.line(s, c2, (x - w * 0.4, y - hh), (x + w * 0.4, y), lw)
        pygame.draw.line(s, c2, (x + w * 0.4, y - hh), (x - w * 0.4, y), lw)
    else:  # cloud
        r = hh * 0.45
        for ox in (-0.25, 0.0, 0.25):
            pygame.draw.circle(s, c1, (int(x + ox * w), int(y - r)), max(2, int(r)))
        pygame.draw.rect(s, c2, (x - w * 0.4, y - r * 0.5, w * 0.8, r * 0.5))


def draw_high(kind, c1, c2, x, y, w, hh, sc):
    s = screen
    lw = max(1, int(3 * sc))
    pw = max(3, w * 0.08)
    if kind == "torii":
        pygame.draw.rect(s, c1, (x - w * 0.45, y - hh, pw, hh))
        pygame.draw.rect(s, c1, (x + w * 0.45 - pw, y - hh, pw, hh))
        pygame.draw.rect(s, c1, (x - w * 0.5, y - hh * 0.75, w, hh * 0.1))
        pygame.draw.rect(s, c2, (x - w * 0.6, y - hh, w * 1.2, hh * 0.2))
        return
    pc = (150, 150, 160) if kind == "rainbow" else c1
    pygame.draw.rect(s, pc, (x - w / 2, y - hh, pw, hh))
    pygame.draw.rect(s, pc, (x + w / 2 - pw, y - hh, pw, hh))
    if kind == "beam":
        pygame.draw.rect(s, c2, (x - w / 2, y - hh, w, hh * 0.3))
    elif kind == "laser":
        pygame.draw.rect(s, tuple(int(c * 0.5) for c in c2), (x - w / 2, y - hh * 0.9, w, hh * 0.25))
        pygame.draw.line(s, c2, (x - w / 2, y - hh * 0.78), (x + w / 2, y - hh * 0.78), lw + 1)
    elif kind == "pipe":
        pygame.draw.rect(s, c1, (x - w / 2, y - hh, w, hh * 0.35))
        for k in range(1, 5):
            pygame.draw.rect(s, c2, (x - w / 2 + w * k / 5, y - hh, w * 0.04, hh * 0.35))
    elif kind == "vine":
        pts = [(x - w / 2, y - hh), (x - w * 0.25, y - hh * 0.7), (x, y - hh * 0.6), (x + w * 0.25, y - hh * 0.7), (x + w / 2, y - hh)]
        pygame.draw.lines(s, c2, False, pts, lw + 2)
        for px_, py_ in pts[1:4]:
            pygame.draw.circle(s, c1, (int(px_), int(py_)), max(2, int(w * 0.05)))
    elif kind == "banner":
        pygame.draw.line(s, c1, (x - w / 2, y - hh), (x + w / 2, y - hh), lw)
        for k in range(5):
            bx = x - w / 2 + w * (k + 0.5) / 5
            pygame.draw.polygon(s, c2 if k % 2 else (255, 255, 255), [(bx - w * 0.07, y - hh), (bx + w * 0.07, y - hh), (bx, y - hh * 0.6)])
    elif kind == "icicle":
        pygame.draw.rect(s, c1, (x - w / 2, y - hh, w, hh * 0.18))
        for k in range(6):
            bx = x - w / 2 + w * (k + 0.5) / 6
            pygame.draw.polygon(s, c2, [(bx - w * 0.05, y - hh * 0.82), (bx + w * 0.05, y - hh * 0.82), (bx, y - hh * 0.5)])
    else:  # rainbow
        for k, c in enumerate(RAINBOW):
            pygame.draw.rect(s, c, (x - w / 2, y - hh + hh * 0.05 * k, w, hh * 0.05 + 1))


# ------------------------------------------------------------ ИГРА
class Game:
    def __init__(self, ch, loc, mode):
        self.ch, self.loc, self.mi = ch, loc, mode
        self.mode = MODES[mode]["key"]
        self.P = eff_perks(ch, SV["acc_sel"])
        self.lane = 0
        self.lx = 0.0
        self.h = 0.0
        self.vy = 0.0
        self.fl = 0.0
        self.on = True
        self.roll = 0.0
        self.jbuf = 0.0
        self.objs = []
        self.speed = {"rush": 0.7, "sprint": 0.8, "hard": 0.9}.get(self.mode, 0.45)
        self.maxsp = {"classic": 1.1, "lava": 0.9, "rush": 1.2, "sprint": 1.3, "chaos": 1.15, "dark": 1.1, "hard": 1.6}[self.mode]
        self.sty = STYLE.get(LOCS[loc]["dec"], STYLE["city"])
        self.score = 0.0
        self.coins = 0
        self.jumps = 0
        self.rolls = 0
        self.dist = 0.0
        self.gap = 0.35
        self.off = 0.0
        self.dead = False
        self.paused = False
        self.msg = ""
        self.inv = 0.0
        self.shield = self.P["sh"]
        self.time = 60.0
        self.reward = 0
        self.travel = 0.0
        self.elapsed = 0.0
        self.pen = 0.0
        self.event = None
        self.evt = 0.0
        self.nxt = 8.0
        self.cd = 0.0
        self.cdmax = max(6.0, min(8.0, 8.0 - 3 * (self.P["j"] - 1)))
        self.ready_snd = True
        if self.mode == "lava":
            self.h = self.fl = PLAT_H
            seg0 = 3.5
            for l in (-1, 0, 1):
                self.objs.append({"k": "plat", "l": l, "t": 1.2, "len": seg0, "top": PLAT_H})
            self.dist = 1.2
            self.gap = seg0 + 0.55 * 0.45 * 1.04

    # --- управление
    def jump(self):
        self.jumps += 1
        if self.mode == "lava" and self.cd <= 0:
            self.vy = H * 2.6
            self.cd = self.cdmax
            self.ready_snd = False
            audio.play("mega")
        else:
            self.vy = H * 1.6 * self.P["j"]
            audio.play("jump")
        self.on = False

    def swipe(self, dx, dy):
        if self.dead or self.paused:
            return
        if self.event == "mirror":
            dx = -dx
        if abs(dx) > abs(dy):
            nl = max(-1, min(1, self.lane + (1 if dx > 0 else -1)))
            if nl != self.lane:
                self.lane = nl
                audio.play("swipe")
        elif dy < 0:
            if self.on:
                self.jump()
            else:
                self.jbuf = 0.15
        else:
            self.roll = 0.6 * self.P["r"]
            self.rolls += 1
            audio.play("roll")
            if self.h > self.fl + 2:
                self.vy = -H * 2.5

    # --- появление объектов
    def coins_row(self, l, n, hz=0.0, start=0.0, d=0.07):
        for i in range(n):
            self.objs.append({"k": "coin", "l": l, "t": start - i * d, "hz": hz})

    def spawn_lava(self):
        sp_end = min(self.maxsp, self.speed + 0.007 * self.P["ramp"] * (self.cdmax + 1.5))
        seg_len = sp_end * (self.cdmax + 1.5) * random.uniform(1.0, 1.2)
        gap_big = 0.55 * self.speed * 1.04
        gs = 0.4 * sp_end * 0.64
        lanes = random.sample([-1, 0, 1], random.choices([1, 2, 3], [20, 45, 35])[0])
        pos = 0.0
        while pos < seg_len - 0.3:
            c = min(random.uniform(0.9, 1.6), seg_len - pos)
            for l in lanes:
                self.objs.append({"k": "plat", "l": l, "t": -pos, "len": c, "top": PLAT_H})
            if c > 0.7:
                r = random.random()
                l = random.choice(lanes)
                off = pos + random.uniform(0.35, c - 0.2)
                if r < 0.3:
                    self.objs.append({"k": "low", "l": l, "t": -off, "b": PLAT_H})
                elif r < 0.75:
                    self.coins_row(l, 3, PLAT_H, -off, 0.07)
            pos += c + gs
        self.gap = pos - gs + gap_big

    def spawn(self):
        m = self.mode
        if m == "lava":
            self.spawn_lava()
            return
        rush = m == "rush" or self.event == "rain"
        free = random.choice([-1, 0, 1])
        pt = {"rush": 0.2, "hard": 0.42}.get(m, 0.35)
        pl = {"rush": 0.15, "hard": 0.2}.get(m, 0.2)
        ph = {"rush": 0.1, "hard": 0.18}.get(m, 0.15)
        for l in (-1, 0, 1):
            if l == free:
                if rush or random.random() < 0.7:
                    self.coins_row(l, 5 if rush else 4)
                continue
            r = random.random()
            if r < pt:
                self.objs.append({"k": "train", "l": l, "t": 0.0, "len": 0.22, "top": TRAIN_H})
                if random.random() < 0.6:
                    self.coins_row(l, 3, TRAIN_H, -0.04, 0.06)
            elif r < pt + pl:
                self.objs.append({"k": "low", "l": l, "t": 0.0})
            elif r < pt + pl + ph:
                self.objs.append({"k": "high", "l": l, "t": 0.0})
            elif rush:
                self.coins_row(l, 4)
        self.gap = random.uniform(0.38, 0.5) if m == "hard" else (random.uniform(0.4, 0.6) if m in ("rush", "sprint") else random.uniform(0.45, 0.7))

    # --- столкновения
    def hit(self, lava=False):
        if self.inv > 0 or self.dead:
            return
        if self.shield > 0:
            self.shield -= 1
            self.inv = 1.5
            audio.play("shield")
            if lava:
                self.vy = H * 2.2
                self.on = False
            return
        if lava:
            self.die("УПАЛ В ЛАВУ")
            return
        if self.mode == "rush":
            self.time = max(0.0, self.time - 5)
            self.inv = 1.5
            audio.play("crash")
            return
        if self.mode == "sprint":
            self.pen += 2.0
            self.speed = max(0.5, self.speed * 0.6)
            self.inv = 1.5
            audio.play("crash")
            return
        self.die("GAME OVER")

    def collide(self):
        h = self.h
        fl = 0.0
        mag = self.P["mag"]
        for o in self.objs[:]:
            k = o["k"]
            dl = abs(o["l"] - self.lx)
            if k == "coin":
                if dl < (1.15 if mag else 0.5) and abs(o["t"] - 1.0) < 0.05 and abs(h - o.get("hz", 0.0)) < H * 0.12:
                    self.objs.remove(o)
                    self.coins += self.P["c"] * (2 if self.mode in ("dark", "hard") else 1)
                    self.score += 50 if self.mode == "rush" else 20
                    audio.play("coin")
                continue
            if dl > 0.5:
                continue
            if k in ("train", "plat"):
                if o["t"] - o["len"] < 1.0 + DW and o["t"] > 1.0 - DW:
                    top = o["top"]
                    if k == "plat" or h >= top - TOL:
                        fl = max(fl, top)
                    elif self.inv <= 0:
                        self.hit()
                        if self.dead:
                            return 0.0
            elif abs(o["t"] - 1.0) < 0.035:
                rel = h - o.get("b", 0.0)
                if k == "low" and rel < H * 0.06:
                    self.hit()
                elif k == "high" and self.roll <= 0 and rel < H * 0.09:
                    self.hit()
                if self.dead:
                    return 0.0
        return fl

    def die(self, msg, crash=True):
        self.dead = True
        self.msg = msg
        audio.stop_music()
        audio.play("crash" if crash else "buy")
        self.reward = (self.coins + int(self.score / 250)) * (2 if self.mode == "hard" else 1)
        SV["coins"] += self.reward
        SV["bests"][self.mi] = max(SV["bests"][self.mi], int(self.score))
        st = SV["stats"]
        st["runs"] += 1
        st["coins"] += self.coins
        st["score"] += int(self.score)
        st["distance"] += int(self.travel * 100)
        st["jumps"] += self.jumps
        st["rolls"] += self.rolls
        if self.mode == "hard": st["hard_runs"] += 1
        if self.mode == "sprint": st["sprint_runs"] += 1
        update_achievements()
        save()

    # --- шаг игры
    def update(self, dt):
        if self.dead or self.paused:
            return
        n = max(1, math.ceil(dt / 0.0167))
        for _ in range(n):
            self.step(dt / n)
            if self.dead:
                return

    def step(self, dt):
        m = self.mode
        self.speed = min(self.maxsp, self.speed + dt * 0.007 * self.P["ramp"])
        mult = 1.35 if self.event == "turbo" else 1.0
        sp = self.speed * mult * dt
        self.score += sp * 100 * self.P["sm"]
        self.off += sp
        self.travel += sp
        self.elapsed += dt
        self.lx += (self.lane - self.lx) * min(1.0, dt * 14)
        if self.inv > 0:
            self.inv -= dt
        if self.roll > 0:
            self.roll -= dt
        if self.cd > 0:
            self.cd -= dt
            if self.cd <= 0 and not self.ready_snd:
                self.ready_snd = True
                audio.play("ready")
        if self.jbuf > 0:
            self.jbuf -= dt
            if self.on:
                self.jump()
                self.jbuf = 0
        if m == "rush":
            self.time -= dt
            if self.time <= 0:
                self.time = 0
                self.die("ВРЕМЯ ВЫШЛО", False)
                return
        if m == "sprint" and self.travel >= SPRINT_D:
            total = self.elapsed + self.pen
            self.score = max(0.0, 150 - total) * 100 + self.coins * 20
            self.die(f"ФИНИШ! {total:.1f} с", False)
            return
        if m == "chaos":
            if self.event:
                self.evt -= dt
                if self.evt <= 0:
                    self.event = None
                    self.nxt = random.uniform(7, 11)
            else:
                self.nxt -= dt
                if self.nxt <= 0:
                    self.event = random.choice(["mirror", "turbo", "rain"])
                    self.evt = 5.0
                    audio.play("shield")
        self.dist += sp
        if self.dist >= self.gap:
            self.dist = 0
            self.spawn()
        for o in self.objs[:]:
            o["t"] += sp
            if o["t"] - o.get("len", 0) > 1.3:
                self.objs.remove(o)
        fl = self.collide()
        if self.dead:
            return
        self.fl = fl
        if self.h > fl or self.vy > 0:
            self.h += self.vy * dt
            self.vy -= G * dt
            if self.vy <= 0 and self.h <= fl:
                self.h = fl
                self.vy = 0.0
        else:
            if self.h < fl:
                self.h = min(fl, self.h + H * 3 * dt)
            self.vy = 0.0
        self.on = self.h <= fl + 1.5 and self.vy <= 0
        if m == "lava" and self.on and fl == 0:
            self.hit(True)

    # --- рисование
    def draw_solid(self, o):
        k, top = o["k"], o["top"]
        tf = o["t"]
        tb = max(o["t"] - o["len"], 0.0)
        if tf <= 0.02 or tb >= 1.4:
            return
        tfc = min(tf, 1.4)
        xf, yf, sf = proj(o["l"], tfc)
        xb, yb, sb = proj(o["l"], tb)
        wf, wb = W * 0.2 * sf, W * 0.2 * sb
        if k == "train":
            cf, ct, cs, ca, kind = self.sty["tr"]
        else:
            cf, ct, cs, ca, kind = (60, 45, 60), (100, 85, 105), (45, 32, 48), (255, 140, 30), "plat"
        if o["l"] < 0:
            pygame.draw.polygon(screen, cs, [(xb + wb / 2, yb - top * sb), (xf + wf / 2, yf - top * sf), (xf + wf / 2, yf), (xb + wb / 2, yb)])
        elif o["l"] > 0:
            pygame.draw.polygon(screen, cs, [(xb - wb / 2, yb - top * sb), (xf - wf / 2, yf - top * sf), (xf - wf / 2, yf), (xb - wb / 2, yb)])
        pygame.draw.polygon(screen, ct, [(xb - wb / 2, yb - top * sb), (xb + wb / 2, yb - top * sb),
                                         (xf + wf / 2, yf - top * sf), (xf - wf / 2, yf - top * sf)])
        if tf <= 1.4:
            th = top * sf
            pygame.draw.rect(screen, cf, (xf - wf / 2, yf - th, wf, th))
            draw_front(kind, ca, cf, xf, yf, wf, th, sf)

    def draw_small(self, o):
        if o["t"] <= 0.02:
            return
        x, y, sc = proj(o["l"], o["t"])
        k = o["k"]
        w = W * 0.2 * sc
        if k == "coin":
            r = max(3, W * 0.03 * sc)
            cy = int(y - (H * 0.04 + o.get("hz", 0.0)) * sc)
            cw = max(2, int(r * (0.25 + 0.75 * abs(math.cos(self.off * 9 + o["l"] + o["t"] * 3)))))
            pygame.draw.ellipse(screen, (255, 215, 0), (x - cw, cy - r, cw * 2, r * 2))
            pygame.draw.ellipse(screen, (190, 140, 0), (x - cw, cy - r, cw * 2, r * 2), 2)
            if cw > 4:
                pygame.draw.line(screen, (255, 245, 160), (x - cw * 0.3, cy - r * 0.5), (x - cw * 0.3, cy + r * 0.3), 2)
            return
        y -= o.get("b", 0.0) * sc
        if k == "low":
            kd, c1, c2 = self.sty["lo"]
            draw_low(kd, c1, c2, x, y, w, H * 0.07 * sc, sc)
        else:
            kd, c1, c2 = self.sty["hi"]
            draw_high(kd, c1, c2, x, y, w, H * 0.11 * sc, sc)

    def draw_obj(self, o):
        if o["k"] in ("train", "plat"):
            self.draw_solid(o)
        else:
            self.draw_small(o)

    def draw_finish(self):
        tf = 1.0 - (SPRINT_D - self.travel)
        if not (0.05 < tf <= 1.35):
            return
        for k in range(12):
            l0 = -1.5 + k * 0.25
            for row in range(2):
                t0, t1 = tf - 0.06 * (row + 1), tf - 0.06 * row
                if t0 <= 0.02:
                    continue
                pts = [proj(l0, t0), proj(l0 + 0.25, t0), proj(l0 + 0.25, t1), proj(l0, t1)]
                col = (20, 20, 20) if (k + row) % 2 else (250, 250, 250)
                pygame.draw.polygon(screen, col, [(p[0], p[1]) for p in pts])

    def draw_trail(self, x, y):
        tr = SV["acc_sel"].get("trail")
        if tr is None:
            return
        kind = ACCS[tr]["kind"]
        for i in range(9):
            px = x + math.sin(self.off * 25 + i) * W * 0.012
            py = y - self.h + H * 0.02 + i * H * 0.02
            r = max(2, int(W * 0.025 * (1 - i / 10)))
            if kind == "rainbow":
                col = RAINBOW[i % 6]
            elif kind == "flame":
                col = (255, max(30, 200 - i * 20), 20)
            else:
                col = (255, 240, 120) if i % 2 else (255, 255, 255)
            pygame.draw.circle(screen, col, (int(px), int(py)), r)

    def draw(self):
        draw_world(LOCS[self.loc], self.off, self.mode == "lava")
        if self.mode == "sprint":
            self.draw_finish()
        key = lambda o: o["t"] - o["len"] - 0.001 if "len" in o else o["t"]
        objs = sorted(self.objs, key=key)
        for o in objs:
            if key(o) <= 1.0:
                self.draw_obj(o)
        x, y, _ = proj(self.lx, 1.0)
        pygame.draw.ellipse(screen, (0, 0, 0), (x - W * 0.04, y - self.fl - 5, W * 0.08, 10))
        self.draw_trail(x, y)
        if not (self.inv > 0 and int(self.inv * 10) % 2 == 0):
            draw_char(self.ch, x, y - self.h, W * 0.07, self.roll > 0)
        for o in objs:
            if key(o) > 1.0:
                self.draw_obj(o)

        if self.mode == "dark":
            screen.blit(VIGN, (0, 0))
        text(f"Очки: {int(self.score)}", f_m, (255, 255, 255), 20, 20, "tl")
        text(f"Монеты: {self.coins}", f_m, (255, 230, 80), 20, 20 + H * 0.05, "tl")
        yy = 20 + H * 0.1
        if self.shield > 0:
            text(f"Щит: {self.shield}", f_s, (150, 220, 255), 20, yy, "tl")
            yy += H * 0.035
        if self.mode == "lava":
            bw = W * 0.45
            r = 1.0 - max(0.0, self.cd) / self.cdmax
            pygame.draw.rect(screen, (0, 0, 0), (20, yy, bw, H * 0.018))
            pygame.draw.rect(screen, (80, 230, 80) if r >= 1 else (255, 170, 30), (20, yy, bw * r, H * 0.018))
            lab = "БОЛЬШОЙ ПРЫЖОК ГОТОВ!" if r >= 1 else f"Перезарядка {self.cd:.1f} c"
            text(lab, f_s, (255, 255, 255), 20, yy + H * 0.022, "tl")
        if self.mode == "rush":
            text(str(math.ceil(self.time)), f_b, (255, 255, 255), W / 2, H * 0.07)
        if self.mode == "sprint":
            text(f"{self.elapsed + self.pen:.1f} с", f_b, (255, 255, 255), W / 2, H * 0.07)
            pw = W * 0.6
            pygame.draw.rect(screen, (0, 0, 0), (W / 2 - pw / 2, H * 0.12, pw, H * 0.012))
            pygame.draw.rect(screen, (80, 230, 120), (W / 2 - pw / 2, H * 0.12, pw * min(1.0, self.travel / SPRINT_D), H * 0.012))
        if self.mode == "chaos" and self.event:
            nm = {"mirror": "ЗЕРКАЛО! Управление наоборот", "turbo": "ТУРБО!", "rain": "ДОЖДЬ МОНЕТ!"}[self.event]
            text(nm, f_m, (255, 120, 255), W / 2, H * 0.13)
        pr = pygame.Rect(W - W * 0.14, H * 0.015, W * 0.12, W * 0.12)
        pygame.draw.rect(screen, (0, 0, 0), pr, border_radius=12)
        if self.paused:
            pygame.draw.polygon(screen, (255, 255, 255), [(pr.x + pr.w * 0.35, pr.y + pr.h * 0.25),
                                                          (pr.x + pr.w * 0.35, pr.y + pr.h * 0.75),
                                                          (pr.x + pr.w * 0.75, pr.y + pr.h * 0.5)])
        else:
            pygame.draw.rect(screen, (255, 255, 255), (pr.x + pr.w * 0.3, pr.y + pr.h * 0.25, pr.w * 0.14, pr.h * 0.5))
            pygame.draw.rect(screen, (255, 255, 255), (pr.x + pr.w * 0.56, pr.y + pr.h * 0.25, pr.w * 0.14, pr.h * 0.5))
        BTN.append((pr, toggle_pause))
        if self.dead or self.paused:
            screen.blit(OV160, (0, 0))
            if self.dead:
                text(self.msg, f_b, (255, 255, 255), W / 2, H * 0.22)
                text(f"Очки: {int(self.score)}   Рекорд: {SV['bests'][self.mi]}", f_m, (255, 255, 255), W / 2, H * 0.32)
                text(f"+{self.reward} монет (всего {SV['coins']})", f_m, (255, 220, 80), W / 2, H * 0.38)
                button(H * 0.5, "ИГРАТЬ СНОВА", start_game)
                button(H * 0.6, "МЕНЮ", lambda: go("menu"))
            else:
                text("ПАУЗА", f_b, (255, 255, 255), W / 2, H * 0.3)
                button(H * 0.5, "ПРОДОЛЖИТЬ", toggle_pause)
                button(H * 0.6, "МЕНЮ", lambda: go("menu"))


# ------------------------------------------------------------ UI
BTN = []
S = {"scr": "menu", "idx": 0, "kind": "chars", "off": 0.0, "mode": 0, "midx": 0,
     "crate": dict(phase="idle", t=0.0, res=None, dup=False, refund=0), "page": 0}
game = None
TC = {}
WC = {}


def text(s, font, col, x, y, anchor="c"):
    k = (s, id(font), col)
    r = TC.get(k)
    if r is None:
        if len(TC) > 300:
            TC.clear()
        r = TC[k] = font.render(s, True, col)
    if anchor == "c":
        screen.blit(r, (x - r.get_width() / 2, y - r.get_height() / 2))
    else:
        screen.blit(r, (x, y))


def wrap(s, font, maxw):
    k = (s, id(font), maxw)
    if k in WC:
        return WC[k]
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if font.size(t)[0] <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    WC[k] = lines
    return lines


def text_block(s, font, col, y, step, maxw=None):
    for ln in wrap(s, font, maxw or W * 0.9):
        text(ln, font, col, W / 2, y)
        y += step
    return y


def button(cy, label, action, color=(40, 120, 255), w=0.7, cx=None, bh=0.075):
    bw, bh = W * w, H * bh
    cx = W / 2 if cx is None else cx
    r = pygame.Rect(cx - bw / 2, cy - bh / 2, bw, bh)
    pygame.draw.rect(screen, (0, 0, 0), r.move(0, 5), border_radius=18)
    pygame.draw.rect(screen, color, r, border_radius=18)
    pygame.draw.rect(screen, (255, 255, 255), r, 3, border_radius=18)
    text(label, f_m, (255, 255, 255), r.centerx, r.centery)
    BTN.append((r, action))


def arrow(cx, cy, d, action):
    r = pygame.Rect(cx - W * 0.07, cy - W * 0.07, W * 0.14, W * 0.14)
    pygame.draw.rect(screen, (0, 0, 0), r, border_radius=14)
    p = W * 0.035
    pygame.draw.polygon(screen, (255, 255, 255), [(cx + d * p, cy - p), (cx + d * p, cy + p), (cx - d * p, cy)])
    BTN.append((r, action))


def go(scr, kind=None):
    global game
    audio.play("click")
    S["scr"] = scr
    if kind:
        S["kind"] = kind
        S["idx"] = SV["sel_c"] if kind == "chars" else SV["sel_l"]
    if scr == "modes":
        S["midx"] = S["mode"]
    if scr == "acc":
        S["idx"] = 0
    if scr == "crate":
        S["crate"] = dict(phase="idle", t=0.0, res=None, dup=False, refund=0)
    if scr == "menu":
        game = None
        audio.play_music(SV["sel_l"])


def start_game(mode=None):
    global game
    audio.play("click")
    if mode is not None:
        S["mode"] = mode
    game = Game(CHARS[SV["sel_c"]], SV["sel_l"], S["mode"])
    S["scr"] = "game"
    audio.stop_music()
    audio.play_music(SV["sel_l"])


def toggle_pause():
    if game and not game.dead:
        game.paused = not game.paused


def toggle_sound():
    SV["sound"] = not SV["sound"]
    audio.on = SV["sound"]
    if audio.on:
        audio.play_music(SV["sel_l"])
        audio.play("click")
    else:
        audio.stop_music()
    save()


def shift(d, n=None):
    if n is None:
        n = len(CHARS if S["kind"] == "chars" else LOCS)
    S["idx"] = (S["idx"] + d) % n
    audio.play("click")


def shift_mode(d):
    S["midx"] = (S["midx"] + d) % len(MODES)
    audio.play("click")


def shop_action():
    kind, i = S["kind"], S["idx"]
    items = CHARS if kind == "chars" else LOCS
    key = "chars" if kind == "chars" else "locs"
    sel = "sel_c" if kind == "chars" else "sel_l"
    if i in SV[key]:
        SV[sel] = i
        audio.play("click")
    elif SV["coins"] >= items[i]["price"]:
        SV["coins"] -= items[i]["price"]
        SV[key].append(i)
        SV["stats"]["chars" if kind == "chars" else "locs"] = len(SV[key])
        update_achievements()
        SV[sel] = i
        audio.play("buy")
    else:
        audio.play("no")
    if kind == "locs":
        audio.stop_music()
        audio.play_music(SV["sel_l"])
    save()


def acc_action():
    i = S["idx"]
    a = ACCS[i]
    if i in SV["acc_own"]:
        SV["acc_sel"][a["slot"]] = None if SV["acc_sel"][a["slot"]] == i else i
        audio.play("click")
    elif SV["coins"] >= a["price"]:
        SV["coins"] -= a["price"]
        SV["acc_own"].append(i)
        SV["stats"]["acc"] = len(SV["acc_own"])
        update_achievements()
        SV["acc_sel"][a["slot"]] = i
        audio.play("buy")
    else:
        audio.play("no")
    save()


def roll_crate():
    pool = list(range(1, len(CHARS)))
    wf = lambda ids: [1.0 / (CHARS[i]["price"] + 150) for i in ids]
    r = random.choices(pool, wf(pool))[0]
    unowned = [i for i in pool if i not in SV["chars"]]
    if r in SV["chars"] and unowned and random.random() < 0.6:
        r = random.choices(unowned, wf(unowned))[0]
    return r


def open_crate():
    if SV["coins"] < CRATE_PRICE:
        audio.play("no")
        return
    SV["coins"] -= CRATE_PRICE
    r = roll_crate()
    dup = r in SV["chars"]
    refund = 0
    if dup:
        refund = max(50, int(CHARS[r]["price"] * 0.3))
        SV["coins"] += refund
    else:
        SV["chars"].append(r)
        SV["stats"]["chars"] = len(SV["chars"])
        update_achievements()
    S["crate"] = dict(phase="shake", t=0.0, res=r, dup=dup, refund=refund)
    audio.play("click")
    save()


def update_crate(dt):
    c = S["crate"]
    if c["phase"] == "shake":
        c["t"] += dt
        if c["t"] >= 1.6:
            c["phase"], c["t"] = "open", 0.0
            audio.play("buy")
    elif c["phase"] == "open":
        c["t"] += dt


def rarity(price):
    if price < 300:
        return "Обычный", (200, 200, 200)
    if price < 800:
        return "Редкий", (90, 170, 255)
    if price < 1600:
        return "Эпический", (200, 110, 255)
    if price < 4000:
        return "Легендарный", (255, 200, 60)
    return "Мифический", (255, 90, 130)


# ------------------------------------------------------------ ЗАДАНИЯ И ДОСТИЖЕНИЯ
_TASK_FAMILIES = [
 ("coins","Собери монет","монет",[10,25,50,100,200,350,500,750,1000,1500]),
 ("score","Набери очков","очков",[500,1000,2500,5000,10000,20000,35000,50000,75000,100000]),
 ("runs","Заверши забегов","забегов",[1,2,3,5,8,10,15,20,30,50]),
 ("distance","Пробеги дистанцию","м",[100,250,500,1000,2000,3500,5000,7500,10000,15000]),
 ("jumps","Совершай прыжки","прыжков",[5,10,20,40,75,100,150,250,400,600]),
 ("rolls","Сделай кувырков","кувырков",[5,10,20,40,75,100,150,250,400,600]),
 ("hard_runs","Сыграй в режиме ХАРДКОР","забегов",[1,2,3,5,8,10,15,20,25,30]),
 ("sprint_runs","Попробуй режим СПРИНТ","забегов",[1,2,3,5,8,10,15,20,25,30]),
 ("chars","Открой персонажей","персонажей",[2,3,5,8,10,15,20,25,30,40]),
 ("locs","Открой локации","локаций",[2,3,4,5,7,9,11,13,16,20]),
 ("acc","Собери аксессуары","аксессуаров",[1,2,3,5,7,10,12,15,18,22]),
 ("coins","Накопи монеты","монет",[50,150,300,600,1200,2500,4000,7000,12000,25000]),
 ("distance","Преодолей путь","м",[200,400,800,1600,3000,4500,6500,9000,12000,18000]),
 ("score","Стань рекордсменом","очков",[750,1500,3000,6000,12000,24000,40000,60000,90000,120000]),
 ("jumps","Прыгай выше","прыжков",[8,16,30,60,90,130,180,280,450,700]),
]
TASKS = [dict(stat=st,title=title,unit=unit,goal=g,reward=max(25,g//2))
         for st,title,unit,goals in _TASK_FAMILIES for g in goals]

_ACH_FAMILIES = [
 ("runs","Первые шаги","забегов",[1,5,10,20,30,50,75,100,150,200]),
 ("coins","Богач","монет",[100,250,500,1000,2000,5000,10000,20000,35000,50000]),
 ("score","Мастер очков","очков",[1000,5000,10000,25000,50000,100000,200000,350000,500000,1000000]),
 ("distance","Покоритель путей","м",[500,1000,2500,5000,10000,20000,35000,50000,75000,100000]),
 ("jumps","Прыгун","прыжков",[10,25,50,100,200,350,500,750,1000,1500]),
]
ACHIEVEMENTS = [dict(stat=st,title=title,unit=unit,goal=g)
                for st,title,unit,goals in _ACH_FAMILIES for g in goals]

def task_progress(i):
    t = TASKS[i]
    return min(t["goal"], SV["stats"].get(t["stat"], 0))

def update_achievements():
    st = SV["stats"]
    for i,a in enumerate(ACHIEVEMENTS):
        if i not in SV["achievements"] and st.get(a["stat"],0) >= a["goal"]:
            SV["achievements"].append(i)
            SV["coins"] += 100

def draw_tasks():
    draw_world(LOCS[SV["sel_l"]], S["off"])
    screen.blit(OV160, (0, 0))
    i = max(0, min(len(TASKS)-1, S["page"]))
    t = TASKS[i]
    cur = task_progress(i)
    text("ЗАДАНИЯ", f_b, (255, 255, 255), W/2, H*0.09)
    text(f"{i+1} / {len(TASKS)}", f_s, (220,220,220), W/2, H*0.17)
    text_block(f"{t['title']} {t['goal']} {t['unit']}", f_m, (255,255,255), H*0.29, H*0.05)
    text(f"Прогресс: {cur} / {t['goal']}", f_m, (255,220,80), W/2, H*0.43)
    bar = pygame.Rect(W*.15, H*.50, W*.70, H*.025)
    pygame.draw.rect(screen, (50,50,60), bar, border_radius=8)
    pygame.draw.rect(screen, (60,210,100), (bar.x,bar.y,bar.w*cur/max(1,t['goal']),bar.h), border_radius=8)
    if i in SV["task_claimed"]:
        button(H*.65, "НАГРАДА ПОЛУЧЕНА", lambda: None, (90,90,100))
    elif cur >= t["goal"]:
        button(H*.65, f"ЗАБРАТЬ +{t['reward']} МОНЕТ", lambda: claim_task(i), (40,180,70))
    else:
        text(f"Награда: {t['reward']} монет", f_s, (255,220,80), W/2, H*.65)
    arrow(W*.12, H*.79, 1, lambda: task_page(-1))
    arrow(W*.88, H*.79, -1, lambda: task_page(1))
    button(H*.91, "НАЗАД", lambda: go("menu"), bh=.06)

def draw_achievements():
    draw_world(LOCS[SV["sel_l"]], S["off"])
    screen.blit(OV160, (0, 0))
    i = max(0, min(len(ACHIEVEMENTS)-1, S["page"]))
    a = ACHIEVEMENTS[i]
    cur = min(a["goal"], SV["stats"].get(a["stat"], 0))
    unlocked = i in SV["achievements"]
    text("ДОСТИЖЕНИЯ", f_b, (255,255,255), W/2, H*.09)
    text(f"{i+1} / {len(ACHIEVEMENTS)}", f_s, (220,220,220), W/2, H*.17)
    text_block(f"{a['title']}: {a['goal']} {a['unit']}", f_m, (255,255,255), H*.29, H*.05)
    text(f"Прогресс: {cur} / {a['goal']}", f_m, (255,220,80), W/2, H*.43)
    bar = pygame.Rect(W*.15,H*.50,W*.70,H*.025)
    pygame.draw.rect(screen,(50,50,60),bar,border_radius=8)
    pygame.draw.rect(screen,(60,210,100),(bar.x,bar.y,bar.w*cur/max(1,a['goal']),bar.h),border_radius=8)
    text("ОТКРЫТО! +100 монет" if unlocked else "Награда за открытие: 100 монет", f_s,
         (100,255,130) if unlocked else (255,255,255), W/2,H*.65)
    arrow(W*.12,H*.79,1,lambda: achievement_page(-1))
    arrow(W*.88,H*.79,-1,lambda: achievement_page(1))
    button(H*.91,"НАЗАД",lambda:go("menu"),bh=.06)

def task_page(d):
    S["page"] = (S["page"] + d) % len(TASKS)
    audio.play("click")

def achievement_page(d):
    S["page"] = (S["page"] + d) % len(ACHIEVEMENTS)
    audio.play("click")

def claim_task(i):
    if i not in SV["task_claimed"] and task_progress(i) >= TASKS[i]["goal"]:
        SV["task_claimed"].append(i)
        SV["coins"] += TASKS[i]["reward"]
        audio.play("buy")
        save()

def draw_menu():
    draw_world(LOCS[SV["sel_l"]], S["off"])
    text("SUBWAY RUN", f_b, (255, 255, 255), W / 2, H * 0.07)
    text(f"Монеты: {SV['coins']}", f_m, (255, 230, 80), W / 2, H * 0.13)
    ch = CHARS[SV["sel_c"]]
    draw_char(ch, W / 2, H * 0.39, W * 0.15)
    text(ch["n"] + " • " + LOCS[SV["sel_l"]]["n"], f_m, (255, 255, 255), W / 2, H * 0.43)
    bh = 0.052
    button(H * 0.49, "ИГРАТЬ", lambda: go("modes"), (40, 180, 70), bh=bh)
    button(H * 0.56, "ПЕРСОНАЖИ", lambda: go("shop", "chars"), bh=bh)
    button(H * 0.63, "ЛОКАЦИИ", lambda: go("shop", "locs"), bh=bh)
    button(H * 0.70, f"ЯЩИК ({CRATE_PRICE})", lambda: go("crate"), (200, 120, 30), bh=bh)
    button(H * 0.77, "АКСЕССУАРЫ", lambda: go("acc"), (150, 70, 200), bh=bh)
    button(H * 0.84, "ЗАДАНИЯ", lambda: (S.update(page=0), go("tasks")), (30, 150, 190), bh=bh)
    button(H * 0.91, "ДОСТИЖЕНИЯ", lambda: (S.update(page=0), go("achievements")), (150, 90, 200), bh=bh)
    button(H * 0.975, "ЗВУК: " + ("ВКЛ" if SV["sound"] else "ВЫКЛ"), toggle_sound, (110, 110, 130), bh=0.04)


def draw_modes():
    draw_world(LOCS[SV["sel_l"]], S["off"])
    screen.blit(OV90, (0, 0))
    i = S["midx"]
    m = MODES[i]
    text("РЕЖИМЫ", f_b, (255, 255, 255), W / 2, H * 0.08)
    text(f"{i + 1} / {len(MODES)}", f_s, (255, 255, 255), W / 2, H * 0.14)
    text(m["n"], f_b, m["col"] if sum(m["col"]) > 200 else (255, 255, 255), W / 2, H * 0.28)
    text_block(m["desc"], f_s, (255, 255, 255), H * 0.37, H * 0.034, W * 0.7)
    text(f"Рекорд: {SV['bests'][i]}", f_m, (255, 230, 80), W / 2, H * 0.66)
    arrow(W * 0.09, H * 0.28, 1, lambda: shift_mode(-1))
    arrow(W * 0.91, H * 0.28, -1, lambda: shift_mode(1))
    button(H * 0.77, "ИГРАТЬ", lambda: start_game(i), m["col"])
    button(H * 0.88, "НАЗАД", lambda: go("menu"))


def draw_shop():
    kind, i = S["kind"], S["idx"]
    items = CHARS if kind == "chars" else LOCS
    it = items[i]
    draw_world(it if kind == "locs" else LOCS[SV["sel_l"]], S["off"])
    screen.blit(OV90, (0, 0))
    text("ПЕРСОНАЖИ" if kind == "chars" else "ЛОКАЦИИ", f_b, (255, 255, 255), W / 2, H * 0.08)
    text(f"Монеты: {SV['coins']}", f_m, (255, 230, 80), W / 2, H * 0.15)
    text(f"{i + 1} / {len(items)}", f_s, (255, 255, 255), W / 2, H * 0.2)
    if kind == "chars":
        draw_char(it, W / 2, H * 0.5, W * 0.2)
    text(it["n"], f_b, (255, 255, 255), W / 2, H * 0.57)
    if kind == "chars":
        text_block(it["desc"], f_s, (255, 255, 255), H * 0.62, H * 0.032)
    arrow(W * 0.09, H * 0.4, 1, lambda: shift(-1))
    arrow(W * 0.91, H * 0.4, -1, lambda: shift(1))
    key = "chars" if kind == "chars" else "locs"
    sel = SV["sel_c"] if kind == "chars" else SV["sel_l"]
    if i == sel:
        label, col = "ВЫБРАНО", (110, 110, 130)
    elif i in SV[key]:
        label, col = "ВЫБРАТЬ", (40, 180, 70)
    else:
        label, col = f"КУПИТЬ за {it['price']}", (230, 150, 20) if SV["coins"] >= it["price"] else (150, 60, 60)
    button(H * 0.76, label, shop_action, col)
    button(H * 0.87, "НАЗАД", lambda: go("menu"))


def draw_acc():
    i = S["idx"]
    a = ACCS[i]
    draw_world(LOCS[SV["sel_l"]], S["off"])
    screen.blit(OV90, (0, 0))
    text("АКСЕССУАРЫ", f_b, (255, 255, 255), W / 2, H * 0.08)
    text(f"Монеты: {SV['coins']}", f_m, (255, 230, 80), W / 2, H * 0.15)
    text(f"{i + 1} / {len(ACCS)}  •  {SLOT_RU[a['slot']]}", f_s, (255, 255, 255), W / 2, H * 0.2)
    pv = dict(SV["acc_sel"])
    pv[a["slot"]] = i
    draw_char(CHARS[SV["sel_c"]], W / 2, H * 0.48, W * 0.2, acc=pv)
    text(a["n"], f_b, (255, 255, 255), W / 2, H * 0.58)
    text_block(a["desc"], f_s, (255, 255, 255), H * 0.63, H * 0.032)
    arrow(W * 0.09, H * 0.4, 1, lambda: shift(-1, len(ACCS)))
    arrow(W * 0.91, H * 0.4, -1, lambda: shift(1, len(ACCS)))
    if i in SV["acc_own"]:
        if SV["acc_sel"][a["slot"]] == i:
            label, col = "СНЯТЬ", (150, 70, 70)
        else:
            label, col = "НАДЕТЬ", (40, 180, 70)
    else:
        label, col = f"КУПИТЬ за {a['price']}", (230, 150, 20) if SV["coins"] >= a["price"] else (150, 60, 60)
    button(H * 0.76, label, acc_action, col)
    button(H * 0.87, "НАЗАД", lambda: go("menu"))


def draw_crate():
    draw_world(LOCS[SV["sel_l"]], S["off"])
    screen.blit(OV160, (0, 0))
    c = S["crate"]
    text("ЯЩИК ПЕРСОНАЖЕЙ", f_b, (255, 255, 255), W / 2, H * 0.07)
    text(f"Монеты: {SV['coins']}", f_m, (255, 230, 80), W / 2, H * 0.13)
    cx = W / 2
    if c["phase"] in ("idle", "shake"):
        sh = math.sin(c["t"] * 45) * W * 0.025 * min(1.0, c["t"]) if c["phase"] == "shake" else math.sin(S["off"] * 6) * W * 0.005
        bw = W * 0.45
        top = H * 0.3
        pygame.draw.rect(screen, (150, 100, 50), (cx - bw / 2 + sh, top + bw * 0.2, bw, bw * 0.6))
        pygame.draw.rect(screen, (110, 70, 30), (cx - bw / 2 + sh, top + bw * 0.2, bw, bw * 0.2))
        pygame.draw.rect(screen, (200, 200, 210), (cx - bw * 0.08 + sh, top + bw * 0.2, bw * 0.16, bw * 0.6))
        pygame.draw.rect(screen, (60, 40, 20), (cx - bw / 2 + sh, top + bw * 0.2, bw, bw * 0.6), 4)
        text("?", f_b, (255, 255, 255), cx + sh, top + bw * 0.58)
        if c["phase"] == "shake":
            for k in range(6):
                ang = k * 1.05 + c["t"] * 6
                rr = W * 0.12 * (0.5 + c["t"])
                pygame.draw.circle(screen, (255, 230, 80), (int(cx + math.cos(ang) * (bw * 0.7 + rr)), int(top + bw * 0.5 + math.sin(ang) * (bw * 0.5 + rr))), 6)
        else:
            text("Внутри случайный персонаж!", f_s, (255, 255, 255), W / 2, H * 0.62)
            text(f"Повтор вернёт часть монет", f_s, (200, 200, 200), W / 2, H * 0.66)
    else:
        res = CHARS[c["res"]]
        rn, rc = rarity(res["price"])
        for k in range(18):
            ang = k * 0.35 + c["t"] * 2
            rr = W * (0.28 + 0.06 * math.sin(c["t"] * 4 + k))
            pygame.draw.circle(screen, rc, (int(cx + math.cos(ang) * rr), int(H * 0.38 + math.sin(ang) * rr * 0.9)), 5)
        draw_char(res, cx, H * 0.5, W * 0.2, acc=SV["acc_sel"])
        text(res["n"], f_b, (255, 255, 255), W / 2, H * 0.57)
        text(rn, f_m, rc, W / 2, H * 0.63)
        if c["dup"]:
            text(f"Повтор! +{c['refund']} монет", f_m, (255, 220, 80), W / 2, H * 0.68)
        else:
            text("НОВЫЙ ПЕРСОНАЖ!", f_m, (120, 255, 140), W / 2, H * 0.68)
        text_block(res["desc"], f_s, (255, 255, 255), H * 0.73, H * 0.03)
    if c["phase"] != "shake":
        col = (230, 150, 20) if SV["coins"] >= CRATE_PRICE else (150, 60, 60)
        button(H * 0.84, f"ОТКРЫТЬ за {CRATE_PRICE}", open_crate, col, bh=0.065)
        button(H * 0.93, "НАЗАД", lambda: go("menu"), bh=0.065)


def tap(pos):
    for r, a in BTN:
        if r.collidepoint(pos):
            a()
            return


def loading():
    if not audio.ok:
        return
    n = len(LOCS)
    for li in range(n):
        screen.fill((20, 20, 40))
        text("Загрузка...", f_b, (255, 255, 255), W / 2, H * 0.45)
        text(f"{li + 1} / {n}", f_m, (255, 255, 255), W / 2, H * 0.55)
        pygame.display.flip()
        pygame.event.pump()
        try:
            audio.music[li] = make_music(li)
        except Exception:
            pass


SCREENS = {"menu": draw_menu, "modes": draw_modes, "shop": draw_shop, "acc": draw_acc,
           "crate": draw_crate, "tasks": draw_tasks, "achievements": draw_achievements}


def main():
    global BTN
    start = None
    pressed = fired = False
    TH = W * 0.07
    loading()
    audio.play_music(SV["sel_l"])
    while True:
        dt = min(clock.tick(60) / 1000, 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                start, pressed, fired = e.pos, True, False
            elif e.type == pygame.MOUSEMOTION and pressed and not fired and S["scr"] == "game" and game:
                dx, dy = e.pos[0] - start[0], e.pos[1] - start[1]
                if math.hypot(dx, dy) > TH:
                    game.swipe(dx, dy)
                    fired = True
            elif e.type == pygame.MOUSEBUTTONUP:
                if pressed and not fired:
                    dx, dy = e.pos[0] - start[0], e.pos[1] - start[1]
                    if S["scr"] == "game" and game and math.hypot(dx, dy) > TH:
                        game.swipe(dx, dy)
                    else:
                        tap(e.pos)
                pressed = False
            elif e.type == pygame.KEYDOWN and S["scr"] == "game" and game:
                m = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}
                if e.key in m:
                    game.swipe(*m[e.key])
        BTN = []
        if S["scr"] == "game" and game:
            game.update(dt)
            game.draw()
        else:
            S["off"] += dt * 0.4
            if S["scr"] == "crate":
                update_crate(dt)
            SCREENS.get(S["scr"], draw_menu)()
        pygame.display.flip()


if __name__ == "__main__":
    main()

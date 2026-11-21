#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI-редактор сохранений Ultima 1 (файлы player1.u1 ... player4.u1).
Только стандартная библиотека (tkinter).

Запуск:  python ultima1_editor_gui.py
"""

import os
import shutil
import struct
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

SIZE = 820  # размер файла сохранения

RACES = {0: "Human (Человек)", 1: "Elf (Эльф)", 2: "Dwarf (Дворф)", 3: "Bobbit (Боббит)"}
CLASSES = {0: "Fighter (Воин)", 1: "Cleric (Клирик)", 2: "Wizard (Маг)", 3: "Thief (Вор)"}
SEXES = {0: "Мужской", 1: "Женский"}
WEAPONS = {0: "Ничего", 1: "Кинжал", 2: "Булава", 3: "Топор", 4: "Верёвка и шипы",
           5: "Меч", 6: "Большой меч", 7: "Лук со стрелами", 8: "Амулет", 9: "Жезл",
           10: "Посох", 11: "Треугольник", 12: "Пистолет", 13: "Световой меч",
           14: "Фейзор", 15: "Бластер"}
ARMORS = {0: "Ничего", 1: "Кожаная", 2: "Кольчуга", 3: "Латы",
          4: "Вакуумный костюм", 5: "Отражающий костюм"}

# (смещение, название, минимум, максимум, словарь-расшифровка или None)
CHAR_FIELDS = [
    (0x16, "Хиты (Hits)",              0, 9999, None),
    (0x18, "Сила (Strength)",          0, 99,   None),
    (0x1A, "Ловкость (Agility)",       0, 99,   None),
    (0x1C, "Стамина (Stamina)",        0, 99,   None),
    (0x1E, "Харизма (Charisma)",       0, 99,   None),
    (0x20, "Мудрость (Wisdom)",        0, 99,   None),
    (0x22, "Интеллект (Intelligence)", 0, 99,   None),
    (0x24, "Монеты (Coins)",           0, 9999, None),
    (0x26, "Опыт (Experience)",        0, 9999, None),
    (0x28, "Еда (Food)",               0, 9999, None),
    (0x2A, "Оружие в руках",           0, 15,   WEAPONS),
    (0x2C, "Готовое заклинание",       0, 10,   {0: "Ничего", 1: "Open", 2: "Unlock",
                                                   3: "Magic Missile", 4: "Steal",
                                                   5: "Лестница вниз", 6: "Лестница вверх",
                                                   7: "Blink", 8: "Create", 9: "Destroy",
                                                   10: "Kill"}),
    (0x2E, "Броня на теле",            0, 5,    ARMORS),
    (0x30, "Транспорт (в ожидании)",   0, 5,    {0: "Пешком", 1: "Конь", 2: "Телега",
                                                   3: "Плот", 4: "Фрегат", 5: "Аэрокар"}),
    (0x34, "X на карте",               0, 65535, None),
    (0x36, "Y на карте",               0, 65535, None),
    (0xA6, "Сбито кораблей в космосе (Space Ace)", 0, 999, None),
    (0xAC, "Пройдено шагов",           0, 65535, None),
]

# Инвентарь: количество каждого предмета (0 = нет, 1+ = есть)
INVENTORY = [
    ("Самоцветы (гемы)", [
        (0x4C, "Самоцвет: красный"),
        (0x4E, "Самоцвет: зелёный"),
        (0x50, "Самоцвет: синий"),
        (0x52, "Самоцвет: белый"),
    ]),
    ("Броня в рюкзаке", [
        (0x56, "Кожаная броня"),
        (0x58, "Кольчуга"),
        (0x5A, "Латы"),
        (0x5C, "Вакуумный костюм"),
        (0x5E, "Отражающий костюм"),
    ]),
    ("Оружие в рюкзаке", [
        (0x62, "Кинжал"),
        (0x64, "Булава"),
        (0x66, "Топор"),
        (0x68, "Верёвка и шипы"),
        (0x6A, "Меч"),
        (0x6C, "Большой меч"),
        (0x6E, "Лук со стрелами"),
        (0x70, "Амулет"),
        (0x72, "Жезл"),
        (0x74, "Посох"),
        (0x76, "Треугольник"),
        (0x78, "Пистолет"),
        (0x7A, "Световой меч"),
        (0x7C, "Фейзор"),
        (0x7E, "Бластер"),
    ]),
    ("Заклинания (кол-во зарядов)", [
        (0x82, "Open"),
        (0x84, "Unlock"),
        (0x86, "Magic Missile"),
        (0x88, "Steal"),
        (0x8A, "Лестница вниз"),
        (0x8C, "Лестница вверх"),
        (0x8E, "Blink"),
        (0x90, "Create"),
        (0x92, "Destroy"),
        (0x94, "Kill"),
    ]),
    ("Транспорт в собственности", [
        (0x98, "Конь"),
        (0x9A, "Телега"),
        (0x9C, "Плот"),
        (0x9E, "Фрегат"),
        (0xA0, "Аэрокар"),
        (0xA2, "Шаттл"),
        (0xA4, "Машина времени"),
    ]),
]


def read16(data, off):
    return struct.unpack_from("<H", data, off)[0]


def write16(data, off, val):
    struct.pack_into("<H", data, off, val)


def read_name(data):
    raw = bytes(data[0:15]).split(b"\x00", 1)[0]
    return raw.decode("ascii", errors="replace").strip()


def write_name(data, name):
    allowed = [c for c in name if ord(c) < 128]
    enc = "".join(allowed).encode("ascii", errors="replace")[:14]
    data[0:15] = enc + b"\x00" * (15 - len(enc))


def new_character_data():
    data = bytearray(SIZE)
    for off in (0x54, 0x60, 0x80, 0x96):
        write16(data, off, 0xFFFF)
    write16(data, 0xA8, 0xFFFF)
    return data


class EditorApp:
    def __init__(self, root):
        self.root = root
        root.title("Редактор сохранений Ultima 1")
        root.geometry("780x660")
        self.data = None
        self.path = None
        self.char_vars = {}
        self.combo_vars = {}
        self.inv_vars = {}

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")
        ttk.Button(top, text="Открыть...", command=self.open_file).pack(side="left", padx=3)
        ttk.Button(top, text="Новый персонаж", command=self.new_char).pack(side="left", padx=3)
        ttk.Button(top, text="Сохранить", command=self.save).pack(side="left", padx=3)

        self.status = tk.StringVar(value="Откройте файл player1.u1 ... player4.u1")
        ttk.Label(top, textvariable=self.status, foreground="#0a58ca").pack(side="left", padx=10)

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        self.tab_char(nb)
        self.tab_inv(nb)

    def tab_char(self, nb):
        frame = ttk.Frame(nb, padding=8)
        nb.add(frame, text="Персонаж")

        name_row = ttk.Frame(frame)
        name_row.pack(fill="x", pady=4)
        ttk.Label(name_row, text="Имя:").pack(side="left")
        self.name_var = tk.StringVar()
        ttk.Entry(name_row, textvariable=self.name_var, width=20).pack(side="left", padx=6)
        ttk.Button(name_row, text="Применить имя", command=self.apply_name).pack(side="left")

        head = ttk.Frame(frame)
        head.pack(fill="x", pady=4)
        self.race_var, self.cls_var, self.sex_var = (tk.StringVar() for _ in range(3))
        for label, var, table in (("Раса", self.race_var, RACES),
                                  ("Класс", self.cls_var, CLASSES),
                                  ("Пол", self.sex_var, SEXES)):
            ttk.Label(head, text=label + ":").pack(side="left", padx=(10, 2))
            cb = ttk.Combobox(head, textvariable=var, width=18, state="readonly",
                              values=[table[k] for k in sorted(table)])
            cb.pack(side="left")
            cb._table = table

        grid = ttk.Frame(frame)
        grid.pack(fill="both", expand=True, pady=8)
        for i, (off, label, lo, hi, table) in enumerate(CHAR_FIELDS):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(grid, text=label).grid(row=row, column=col, sticky="w", padx=4, pady=2)
            var = tk.StringVar()
            if table is None:
                ent = ttk.Entry(grid, textvariable=var, width=8)
            else:
                ent = ttk.Combobox(grid, textvariable=var, width=8, state="readonly",
                                   values=[table[k] for k in sorted(table)])
                self.combo_vars[off] = (var, table, ent)
            ent.grid(row=row, column=col + 1, sticky="w", padx=4, pady=2)
            var.trace_add("write", lambda *a, o=off: self.apply_field(o))
            self.char_vars[off] = (var, label)

    def tab_inv(self, nb):
        frame = ttk.Frame(nb, padding=8)
        nb.add(frame, text="Инвентарь")
        canvas = tk.Canvas(frame)
        sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for group, items in INVENTORY:
            ttk.Label(inner, text=group, font=("", 10, "bold")).pack(anchor="w", pady=(8, 2))
            for off, lbl in items:
                row = ttk.Frame(inner)
                row.pack(fill="x", padx=12)
                ttk.Label(row, text=lbl, width=26).pack(side="left")
                var = tk.StringVar()
                sp = tk.Spinbox(row, from_=0, to=99, textvariable=var, width=5,
                                command=lambda o=off: self.apply_inv(o))
                sp.pack(side="left", padx=6)
                var.trace_add("write", lambda *a, o=off: self.apply_inv(o))
                self.inv_vars[off] = var

    def refresh(self):
        if self.data is None:
            return
        self.name_var.set(read_name(self.data))
        race, cls, sex = (read16(self.data, o) for o in (0x10, 0x12, 0x14))
        self.race_var.set(RACES.get(race, race))
        self.cls_var.set(CLASSES.get(cls, cls))
        self.sex_var.set(SEXES.get(sex, sex))
        for off, (var, label) in self.char_vars.items():
            if off in self.combo_vars:
                table = self.combo_vars[off][1]
                var.set(table.get(read16(self.data, off), "???"))
            else:
                var.set(str(read16(self.data, off)))
        for off, var in self.inv_vars.items():
            var.set(str(read16(self.data, off)))

    def apply_name(self):
        if self.data is None:
            return
        write_name(self.data, self.name_var.get().strip() or "Hero")
        self.status.set("Имя изменено. Не забудьте «Сохранить».")

    def apply_field(self, off):
        if self.data is None:
            return
        var = self.char_vars[off][0]
        try:
            if off in self.combo_vars:
                table = self.combo_vars[off][1]
                val = next(k for k, v in table.items() if v == var.get())
            else:
                val = int(var.get())
        except (ValueError, StopIteration):
            return
        write16(self.data, off, val)
        self.status.set(f"Поле изменено ({self.char_vars[off][1]} = {val}). Не забудьте «Сохранить».")

    def apply_inv(self, off):
        if self.data is None:
            return
        try:
            val = max(0, min(99, int(self.inv_vars[off].get())))
        except ValueError:
            return
        write16(self.data, off, val)
        self.status.set(f"Инвентарь изменён ({val}). Не забудьте «Сохранить».")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Ultima 1 saves", "*.u1"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            messagebox.showerror("Ошибка", str(e))
            return
        if len(data) != SIZE:
            messagebox.showwarning("Предупреждение",
                                   f"Файл {len(data)} байт вместо {SIZE}.\nПродолжаю, но правьте только те поля, в которых уверены.")
        self.data = bytearray(data)
        self.path = path
        self.refresh()
        self.status.set(f"Загружено: {path}")

    def new_char(self):
        if not messagebox.askyesno("Новый персонаж", "Создать нового персонажа с нуля?\n"
                                                    "Текущие данные в памяти будут перезаписаны!"):
            return
        self.data = new_character_data()
        self.refresh()
        self.status.set("Новый персонаж создан. Заполните поля и «Сохранить» (лучше в новый файл).")

    def save(self):
        if self.data is None:
            messagebox.showinfo("Нечего сохранять", "Сначала откройте или создайте персонажа.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".u1",
                                            filetypes=[("Ultima 1 saves", "*.u1")],
                                            initialfile=os.path.basename(self.path or "player1.u1"))
        if not path:
            return
        if os.path.exists(path):
            shutil.copy2(path, path + ".bak")
        with open(path, "wb") as f:
            f.write(bytes(self.data))
        self.status.set(f"Сохранено: {path}" + (" (бэкап .bak создан)" if os.path.exists(path + ".bak") else ""))


def main():
    root = tk.Tk()
    EditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

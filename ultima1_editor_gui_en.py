#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI save editor for Ultima 1 (player1.u1 ... player4.u1 files).
Standard library only (tkinter).

Run:  python ultima1_editor_gui_en.py
"""

import os
import shutil
import struct
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

SIZE = 820  # save file size

RACES = {0: "Human", 1: "Elf", 2: "Dwarf", 3: "Bobbit"}
CLASSES = {0: "Fighter", 1: "Cleric", 2: "Wizard", 3: "Thief"}
SEXES = {0: "Male", 1: "Female"}
WEAPONS = {0: "None", 1: "Dagger", 2: "Mace", 3: "Axe", 4: "Rope & Spikes",
           5: "Sword", 6: "Great Sword", 7: "Bow & Arrows", 8: "Amulet", 9: "Wand",
           10: "Staff", 11: "Triangle", 12: "Pistol", 13: "Light Sword",
           14: "Phazor", 15: "Blaster"}
ARMORS = {0: "None", 1: "Leather", 2: "Chain Mail", 3: "Plate Mail",
          4: "Vacuum Suit", 5: "Reflect Suit"}

# (offset, label, minimum, maximum, decode-dict or None)
CHAR_FIELDS = [
    (0x16, "Hit Points",                 0, 9999, None),
    (0x18, "Strength",                   0, 99,   None),
    (0x1A, "Agility",                    0, 99,   None),
    (0x1C, "Stamina",                    0, 99,   None),
    (0x1E, "Charisma",                   0, 99,   None),
    (0x20, "Wisdom",                     0, 99,   None),
    (0x22, "Intelligence",               0, 99,   None),
    (0x24, "Coins",                      0, 9999, None),
    (0x26, "Experience",                 0, 9999, None),
    (0x28, "Food",                       0, 9999, None),
    (0x2A, "Weapon in hand",             0, 15,   WEAPONS),
    (0x2C, "Ready spell",                0, 10,   {0: "None", 1: "Open", 2: "Unlock",
                                                   3: "Magic Missile", 4: "Steal",
                                                   5: "Ladder Down", 6: "Ladder Up",
                                                   7: "Blink", 8: "Create", 9: "Destroy",
                                                   10: "Kill"}),
    (0x2E, "Armor worn",                 0, 5,    ARMORS),
    (0x30, "Transport (pending)",        0, 5,    {0: "On foot", 1: "Horse", 2: "Cart",
                                                   3: "Raft", 4: "Frigate", 5: "Aircar"}),
    (0x34, "Map X",                      0, 65535, None),
    (0x36, "Map Y",                      0, 65535, None),
    (0xA6, "Enemy vessels down (Space Ace)", 0, 999, None),
    (0xAC, "Steps travelled",            0, 65535, None),
]

# Inventory: quantity of each item (0 = none, 1+ = owned)
INVENTORY = [
    ("Gems", [
        (0x4C, "Red Gem"),
        (0x4E, "Green Gem"),
        (0x50, "Blue Gem"),
        (0x52, "White Gem"),
    ]),
    ("Armor in pack", [
        (0x56, "Leather Armor"),
        (0x58, "Chain Mail"),
        (0x5A, "Plate Mail"),
        (0x5C, "Vacuum Suit"),
        (0x5E, "Reflect Suit"),
    ]),
    ("Weapons in pack", [
        (0x62, "Dagger"),
        (0x64, "Mace"),
        (0x66, "Axe"),
        (0x68, "Rope & Spikes"),
        (0x6A, "Sword"),
        (0x6C, "Great Sword"),
        (0x6E, "Bow & Arrows"),
        (0x70, "Amulet"),
        (0x72, "Wand"),
        (0x74, "Staff"),
        (0x76, "Triangle"),
        (0x78, "Pistol"),
        (0x7A, "Light Sword"),
        (0x7C, "Phazor"),
        (0x7E, "Blaster"),
    ]),
    ("Spells (charges)", [
        (0x82, "Open"),
        (0x84, "Unlock"),
        (0x86, "Magic Missile"),
        (0x88, "Steal"),
        (0x8A, "Ladder Down"),
        (0x8C, "Ladder Up"),
        (0x8E, "Blink"),
        (0x90, "Create"),
        (0x92, "Destroy"),
        (0x94, "Kill"),
    ]),
    ("Vehicles owned", [
        (0x98, "Horse"),
        (0x9A, "Cart"),
        (0x9C, "Raft"),
        (0x9E, "Frigate"),
        (0xA0, "Aircar"),
        (0xA2, "Shuttle"),
        (0xA4, "Time Machine"),
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
        root.title("Ultima 1 Save Editor")
        root.geometry("780x660")
        self.data = None
        self.path = None
        self.char_vars = {}
        self.combo_vars = {}
        self.inv_vars = {}

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")
        ttk.Button(top, text="Open...", command=self.open_file).pack(side="left", padx=3)
        ttk.Button(top, text="New Character", command=self.new_char).pack(side="left", padx=3)
        ttk.Button(top, text="Save", command=self.save).pack(side="left", padx=3)

        self.status = tk.StringVar(value="Open a player1.u1 ... player4.u1 file")
        ttk.Label(top, textvariable=self.status, foreground="#0a58ca").pack(side="left", padx=10)

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        self.tab_char(nb)
        self.tab_inv(nb)

    def tab_char(self, nb):
        frame = ttk.Frame(nb, padding=8)
        nb.add(frame, text="Character")

        name_row = ttk.Frame(frame)
        name_row.pack(fill="x", pady=4)
        ttk.Label(name_row, text="Name:").pack(side="left")
        self.name_var = tk.StringVar()
        ttk.Entry(name_row, textvariable=self.name_var, width=20).pack(side="left", padx=6)
        ttk.Button(name_row, text="Apply name", command=self.apply_name).pack(side="left")

        head = ttk.Frame(frame)
        head.pack(fill="x", pady=4)
        self.race_var, self.cls_var, self.sex_var = (tk.StringVar() for _ in range(3))
        for label, var, table in (("Race", self.race_var, RACES),
                                  ("Class", self.cls_var, CLASSES),
                                  ("Sex", self.sex_var, SEXES)):
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
        nb.add(frame, text="Inventory")
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
        self.status.set("Name changed. Don't forget to Save.")

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
        self.status.set(f"Field changed ({self.char_vars[off][1]} = {val}). Don't forget to Save.")

    def apply_inv(self, off):
        if self.data is None:
            return
        try:
            val = max(0, min(99, int(self.inv_vars[off].get())))
        except ValueError:
            return
        write16(self.data, off, val)
        self.status.set(f"Inventory changed ({val}). Don't forget to Save.")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Ultima 1 saves", "*.u1"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            messagebox.showerror("Error", str(e))
            return
        if len(data) != SIZE:
            messagebox.showwarning("Warning",
                                   f"File is {len(data)} bytes instead of {SIZE}.\nContinuing, but edit only the fields you are sure about.")
        self.data = bytearray(data)
        self.path = path
        self.refresh()
        self.status.set(f"Loaded: {path}")

    def new_char(self):
        if not messagebox.askyesno("New Character", "Create a new character from scratch?\n"
                                                    "Current data in memory will be overwritten!"):
            return
        self.data = new_character_data()
        self.refresh()
        self.status.set("New character created. Fill in the fields and Save (a new file is best).")

    def save(self):
        if self.data is None:
            messagebox.showinfo("Nothing to save", "Open or create a character first.")
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
        self.status.set(f"Saved: {path}" + (" (.bak backup created)" if os.path.exists(path + ".bak") else ""))


def main():
    root = tk.Tk()
    EditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

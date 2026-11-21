# Ultima 1 Save Editor

A save file editor for **Ultima I: The First Age of Darkness** (DOS, 1987).
Edits and creates player save files (`player1.u1` ... `player4.u1`, 820 bytes each)
in a friendly interface — no hex editor required.

Both a **console** and a **GUI** version are included. Console version supports
English and Russian (choose at startup or via `--en` / `--ru`).

## Features

- Edit character stats: Hit Points, Strength, Agility, Stamina, Charisma,
  Wisdom, Intelligence, Coins, Experience, Food
- Level is derived from Experience in-game (1000 XP = 1 level, max 10),
  so set XP 9999 for level 10
- Edit inventory: gems, weapons, armor, spells (with charges), vehicles
  (horse, cart, raft, frigate, aircar, shuttle, time machine)
- Rename character (ASCII only — the DOS game understands nothing else)
- Create a brand-new character from scratch (writes all required 0xFFFF
  list-terminator markers correctly)
- **Space Ace counter** — the number of enemy vessels destroyed in space
  (needed for the princess to reveal the Time Machine location). This field
  is undocumented on ModdingWiki; its address was found experimentally and
  is included in this editor as a named field
- Automatic `.bak` backup before every save
- Safe value limits (HP/coins/food max 9999, stats max 99) so you can't
  corrupt the file with a typo

## Usage

### Console version
```
python ultima1_editor.py [path\to\player1.u1]
```
Without an argument it will ask for the file path.

### GUI version
```
python ultima1_editor_gui.py        # Russian interface
python ultima1_editor_gui_en.py     # English interface
```

### Build a standalone .exe (Windows)
```
pip install pyinstaller
pyinstaller --onefile --windowed ultima1_editor_gui_en.py
```
The ready executable appears in `dist\`. No Python required on target machines.

## Important notes

- **Close DOSBox before editing** — a running game overwrites the save file
  on exit with its in-memory state.
- Save the game on the world map (`Q` command) before editing.
- If your copy is from GOG, modified files may live in `<game folder>\cloud_saves\`.
- Don't set Intelligence too high (200+): shop prices are calculated from INT
  and will skyrocket.
- Don't edit bytes in the middle section of the file (`0x54`–`0x96` markers,
  object map `0xB4`+) unless you know what you're doing — `0xFFFF` markers
  terminate the inventory lists, and the object map spawns creatures.

## Save file format (820 bytes)

Based on [ModdingWiki: Ultima I Save Game Format](https://moddingwiki.shikadi.net/wiki/Ultima_I_Save_Game_Format)
with our experimental finding for the space-kills counter. All 16-bit values are little-endian.

| Offset | Size | Field |
|--------|------|-------|
| 0x00 | 15 | Character name (NUL-padded ASCII) |
| 0x10 | 2 | Race (0 Human, 1 Elf, 2 Dwarf, 3 Bobbit) |
| 0x12 | 2 | Class (0 Fighter, 1 Cleric, 2 Wizard, 3 Thief) |
| 0x14 | 2 | Sex (0 male, 1 female) |
| 0x16 | 2 | Hit Points |
| 0x18 | 2 | Strength |
| 0x1A | 2 | Agility |
| 0x1C | 2 | Stamina |
| 0x1E | 2 | Charisma |
| 0x20 | 2 | Wisdom |
| 0x22 | 2 | Intelligence |
| 0x24 | 2 | Coins |
| 0x26 | 2 | Experience (1000 per level, max 9999) |
| 0x28 | 2 | Food |
| 0x2A | 2 | Weapon in hand |
| 0x2C | 2 | Readied spell |
| 0x2E | 2 | Armor worn |
| 0x30 | 2 | Pending transport |
| 0x34 | 2 | X coordinate |
| 0x36 | 2 | Y coordinate |
| 0x4C–0x52 | 2 each | Gems: red, green, blue, white |
| 0x54 | 2 | 0xFFFF marker (end of armor list) |
| 0x56–0x5E | 2 each | Armor in pack: leather, chain, plate, vac suit, reflect suit |
| 0x60 | 2 | 0xFFFF marker (end of weapon list) |
| 0x62–0x7E | 2 each | Weapons in pack (dagger ... blaster) |
| 0x80 | 2 | 0xFFFF marker (end of spell list) |
| 0x82–0x94 | 2 each | Spell charges (Open ... Kill) |
| 0x96 | 2 | 0xFFFF marker (end of vehicle list) |
| 0x98–0xA4 | 2 each | Vehicles owned: horse, cart, raft, frigate, aircar, shuttle, time machine |
| **0xA6** | **2** | **Enemy vessels destroyed in space (Space Ace counter)** — our experimental finding, undocumented elsewhere |
| 0xA8 | 2 | 0xFFFF marker |
| 0xAC | 2 | Steps travelled |
| 0xB4 | 80 | Object map (creatures/vehicles on world map) |

## Files

- `ultima1_editor.py` — bilingual console editor
- `ultima1_editor_gui.py` — GUI (Russian)
- `ultima1_editor_gui_en.py` — GUI (English)
- `ultima1_diff.py` — diff tool: compares two saves and shows changed fields
  (useful for discovering unknown fields experimentally)

## How the 0xA6 field was found

1. Save the game (`Q` on the world map), copy `player1.u1` to `before.u1`.
2. Destroy exactly one enemy vessel in space, return via shuttle, save again.
3. Run `python ultima1_diff.py before.u1 after.u1` — the field incremented by 1
   in the undocumented zone is the counter.
4. Verified: setting this field to 25 shows "Enemy vessels...25" in the in-game
   inventory screen (`Z`).

## Disclaimer

This project contains **no game assets or code** — only an open-source save
file editor. Ultima I is © Origin Systems / Electronic Arts. Own the game
legally (e.g. on [GOG](https://www.gog.com/en/game/ultima_1_2)) before using this tool.

## License

MIT — see [LICENSE](LICENSE).

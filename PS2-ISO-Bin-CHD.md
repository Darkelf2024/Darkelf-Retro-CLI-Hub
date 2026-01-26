# PS2 ISO & BIN/CUE → CHD Bulk Conversion (macOS Apple Silicon)

This guide walks you through **bulk converting PlayStation 2 games to CHD** on **macOS (M1 / Apple Silicon)** using `chdman`.

It covers **all supported scenarios** in one place:

- ISO → CHD (in-place)
- ISO → CHD (separate output folder)
- BIN/CUE → CHD (in-place)
- BIN/CUE → CHD (separate output folder)

CHD is **lossless**, saves space, and works perfectly with **AetherSX2** and **NetherSX2**.

---

## Requirements

- macOS (Apple Silicon: M1 / M2 / M3)
- Homebrew installed
- PS2 games dumped as `.iso` or `.bin/.cue`
- Enough free disk space during conversion

---

## Step 1 — Install `chdman`

`chdman` is included with **MAME**.

```bash
brew install mame
```

Verify installation:

```bash
/opt/homebrew/bin/chdman
```

If help text appears, it’s installed correctly.

---

## Step 2 — Confirm game location

This guide assumes your games are stored at:

```
/Users/kevinmoore/Desktop/PS2
```

Check how many ISOs exist:

```bash
ls "/Users/kevinmoore/Desktop/PS2"/*.iso | wc -l
```

---

# Scenario A — ISO → CHD (in-place)

Creates `.chd` files **next to the ISOs**.

```bash
for f in "/Users/kevinmoore/Desktop/PS2/"*.iso; do
  /opt/homebrew/bin/chdman createcd -i "$f" -o "${f%.iso}.chd"
done
```

Result:
```
PS2/
 ├── Game.iso
 ├── Game.chd
```

---

# Scenario B — ISO → CHD (separate folder) ⭐ Recommended

```bash
mkdir -p "/Users/kevinmoore/Desktop/PS2_CHD"

for f in "/Users/kevinmoore/Desktop/PS2/"*.iso; do
  base=$(basename "$f" .iso)
  /opt/homebrew/bin/chdman createcd -i "$f" -o "/Users/kevinmoore/Desktop/PS2_CHD/$base.chd"
done
```

---

# Scenario C — BIN/CUE → CHD (in-place)

⚠️ Always point `chdman` at the **`.cue` file**, not the `.bin`.

```bash
for f in "/Users/kevinmoore/Desktop/PS2/"*.cue; do
  /opt/homebrew/bin/chdman createcd -i "$f" -o "${f%.cue}.chd"
done
```

---

# Scenario D — BIN/CUE → CHD (separate folder)

```bash
mkdir -p "/Users/kevinmoore/Desktop/PS2_CHD"

for f in "/Users/kevinmoore/Desktop/PS2/"*.cue; do
  base=$(basename "$f" .cue)
  /opt/homebrew/bin/chdman createcd -i "$f" -o "/Users/kevinmoore/Desktop/PS2_CHD/$base.chd"
done
```

---

## Important BIN/CUE Notes

- Multi-track audio is preserved
- CHD replaces all BIN files
- Safe to delete BIN/CUE after verification

---

## Conversion Time

- ~1–2 minutes per game on M1
- 121 games ≈ 2–4 hours
- No performance loss vs ISO

---

## Emulator Setup

1. Open **AetherSX2** or **NetherSX2**
2. Set game directory to:
   - `PS2` (in-place)
   - `PS2_CHD` (separate folder)
3. Rescan games
4. Test a few titles

---

## Summary

- ✔ ISO → CHD supported
- ✔ BIN/CUE → CHD supported
- ✔ Bulk-safe conversion
- ✔ Works perfectly in PS2 emulators
- ✔ Cleaner, future-proof library

Enjoy your optimized PS2 collection 🎮

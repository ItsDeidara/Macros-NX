# SysBot.Base Controls Reference for Macro Building (LLM-Friendly)

This document describes all valid controls and macro step types for Nintendo Switch sys-botbase, suitable for use by an LLM/chatbot to help users build macros.

---

## 1. Button Controls

**Supported Buttons:**
| Button Name | Description         |
|-------------|--------------------|
| A           | Main action button |
| B           | Cancel/jump        |
| X           | Secondary action   |
| Y           | Tertiary action    |
| L           | Left shoulder      |
| R           | Right shoulder     |
| ZL          | Left trigger       |
| ZR          | Right trigger      |
| PLUS        | Start/Menu         |
| MINUS       | Select/Map         |
| HOME        | Home button        |
| CAPTURE     | Screenshot         |
| LSTICK      | Left stick click   |
| RSTICK      | Right stick click  |

**Macro Step Syntax:**
- `Button:A` — Press the A button
- `Button:B` — Press the B button

---

## 2. Hold/Release Controls

- `Hold:<Button>` — Hold down a button (e.g., `Hold:L`)
- `Release:<Button>` — Release a held button (e.g., `Release:L`)

**Example:**
- `Hold:A` (hold A)
- `Wait:500` (wait 500 ms)
- `Release:A` (release A)

---

## 3. Stick Controls

**Stick Move:**
- `%<X>,<Y>` — Move the **left stick** to position (X, Y)
- `&<X>,<Y>` — Move the **right stick** to position (X, Y)
    - X and Y range from -32767 (full left/down) to 32767 (full right/up)
    - Center is `%0,0` or `&0,0` (stick release)

**Examples:**
- `%0,32767` — Left stick full up
- `%32767,0` — Left stick full right
- `%-32767,0` — Left stick full left
- `%0,-32767` — Left stick full down
- `%0,0` — Left stick center (release)
- `&0,32767` — Right stick full up
- `&32767,0` — Right stick full right
- `&-32767,0` — Right stick full left
- `&0,-32767` — Right stick full down
- `&0,0` — Right stick center (release)

**Common Directions:**
| Direction    | X       | Y       | Left Stick Example | Right Stick Example |
|--------------|---------|---------|-------------------|--------------------|
| Up           | 0       | 32767   | `%0,32767`        | `&0,32767`         |
| Down         | 0       | -32767  | `%0,-32767`       | `&0,-32767`        |
| Left         | -32767  | 0       | `%-32767,0`       | `&-32767,0`        |
| Right        | 32767   | 0       | `%32767,0`        | `&32767,0`         |
| Up-Left      | -32767  | 32767   | `%-32767,32767`   | `&-32767,32767`    |
| Up-Right     | 32767   | 32767   | `%32767,32767`    | `&32767,32767`     |
| Down-Left    | -32767  | -32767  | `%-32767,-32767`  | `&-32767,-32767`   |
| Down-Right   | 32767   | -32767  | `%32767,-32767`   | `&32767,-32767`    |
| Center       | 0       | 0       | `%0,0`            | `&0,0`             |

---

## 4. D-Pad Controls (if supported)

- `Button:DUP` — D-Pad Up
- `Button:DDOWN` — D-Pad Down
- `Button:DLEFT` — D-Pad Left
- `Button:DRIGHT` — D-Pad Right
- (Also supports diagonals: `DUPLEFT`, `DUPRIGHT`, `DDOWNLEFT`, `DDOWNRIGHT`)

---

## 5. Wait/Delay

- `Wait:<ms>` — Wait for the specified number of milliseconds
    - Example: `Wait:500` (wait 0.5 seconds)

---

## 6. Macro Step Sequence

A macro is a sequence of steps, separated by newlines or commas. Each step is one of the above types.

**Example Macro:**
```
Hold:A
Wait:300
Release:A
%32767,0
Wait:200
Button:B
&0,32767
Wait:100
&0,0
```

---

## 7. General Notes
- All button names are case-insensitive (A, a, A).
- Stick values must be integers between -32767 and 32767.
- Wait times are in milliseconds (ms).
- Steps are executed in order, top to bottom.
- `%0,0` and `&0,0` are used to release the left and right stick (center position).

---

## 8. Example Macros

**Jump Right (Left Stick):**
```
Button:B
%32767,0
Wait:200
%0,0
```

**Camera Up (Right Stick):**
```
&0,32767
Wait:200
&0,0
```

**Hold Shield, Move Up:**
```
Hold:L
%0,32767
Wait:500
Release:L
%0,0
```

**Simple Combo:**
```
Button:Y
Wait:100
Button:B
Wait:100
Button:A
```

---

This reference is designed for LLM/chatbot use. For any step, the bot should output the correct macro step syntax as shown above. 
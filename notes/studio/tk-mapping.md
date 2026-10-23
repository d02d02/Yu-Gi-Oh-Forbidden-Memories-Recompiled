# Tk mapping and editor limits

Facts from `../native-models-feasibility.md` sec. 9 (read from code, nothing run). The wireframes are web; the editor is Tk.

| Wireframe element | Tk realisation | Limit to respect |
|---|---|---|
| Tab / view switch | a `Tab` subclass in `tabs.py` listed in `app.tabs` | edits call `app.changed()` / `app.say()` |
| Split pane | `ttk.PanedWindow` (rail left, stage right) | narrow window: rail collapses to a Combobox |
| Stage rail | `ttk.Treeview` or a Frame of buttons with a state glyph | keyboard: arrows, Enter |
| Engine viewport | frames from the engine process shown as `tk.PhotoImage` via `pngio.ppm`, or the game window docked beside the editor | no PIL, no embedded viewer in the editor today; pure-Python PNG path is slow for large frames, so low-res stream plus "open game window" |
| Overlay toggles, transport | `ttk.Checkbutton`, `ttk.Button`, `ttk.Scale` | engine draws the overlays, Tk only sends commands |
| Time-map / act table | `ttk.Treeview` (table) and a `tk.Canvas` ruler with draggable items | Canvas is fine for rulers and sparklines |
| Checks list | Frame rows with a coloured label and wrapped text | wrap length must follow the pane width |
| Knobs | `ttk.Label` + `Combobox` / `Spinbox` / `Checkbutton` / `Entry` | visible label on every control; units in the label |
| Slide-over (source chooser) | a side Frame that replaces the knob column | no stacked `Toplevel` dialogs |
| Confirm dialog | modal `Toplevel`, Cancel focused | |
| Long jobs (convert, audit, engine) | subprocess polled with `after()` | no worker threads |
| Autosave of recipe | write on knob change (debounced) | |
| Tests | `GuiCase` tests skip without a display | keep logic (state model, checks) in plain modules that tests can run headless |

## Viewport transport (Q6)
The viewport must show the engine's own render. Two ways to get it into the editor:
* **Stream frames**: the engine process sends captured frames over the control channel; Tk shows them as an image. Works on Windows, macOS and Linux. Cost: the editor has no PIL, so frames go through pure-Python PNG/PPM decoding, which is slow; at a low resolution (about 640x360) it gives stills and a few frames per second, enough to scrub, pause and judge a pose, not to judge smooth motion.
* **Dock the game window**: embed the OS window of the game in the editor. Possible on Windows (parent the window), not portable to macOS or Linux, and the laptop and macOS need the same flow. Fragile with GL.
* **Recommendation**: stream low-res frames as the default viewport, and add "Pop out game window" for full-speed live playback beside the editor. Needed because every judging stage (S4-S8) depends on seeing the real render. Awaiting the user's confirmation.

Design consequence: put the state model, check results and recipe edits in a UI-free module so the CLI, tests and the Tk tab share them.

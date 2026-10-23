# Studio decisions

## Taken (user, 2026-10-23 unless noted)
| id | Decision |
|---|---|
| SD1 | Viewport = the real game engine, driven over `yfm_control`; no second renderer for the stages that judge look, timing or fit. A web viewport is allowed only for S1-S3 if ever needed. |
| SD2 | One `recipe.json` holds every choice; `glb + recipe -> package` is deterministic and byte-identical. The studio edits the recipe, never the source file. |
| SD3 | The studio is not a modeller or a weight painter. Mesh and weight fixes go to Blender and come back (re-audit on return). |
| SD4 | UX and GUI first, code after. Recipe schema, converter entry and engine viewer commands are derived from the screens. |
| SD5 | The studio is an add-on to the FM Editor (Tk), not a separate app. |
| SD6 | The three-view structure (Models, Studio, Flow) is a hypothesis; each view must be detailed before the structure is trusted (user, same day). |

## Adopted rules
1. **Stage gates are honest.** A fail blocks Next. A warn needs one explicit acknowledgement, recorded with the measured value; a changed value clears it.
2. **Every check names a fix.** A check that cannot suggest a knob or a hand-off says so and why.
3. **Auto first, always reversible.** Each stage opens with the category preset applied. "Reset to auto" restores that stage only and says what it changed.
4. **No surprise writes.** The recipe autosaves, the package is written only by Build.
5. **One surface per task length** (surfaces skill): one field = inline; short task = slide-over (Tk: a side frame, not a dialog stack); long task = its own screen; never two dialogs stacked; destructive = dialog naming the entity, Cancel focused.
6. **What you see is the game.** Overlays are drawn by the engine; a toggle that cannot be drawn faithfully is not offered.
7. **Honest scope.** Where the engine cannot do something (IK, physics, non-uniform scale, more than 16 clips) the screen says it once, in the stage, not as a failed check later.

## Out of scope
Modelling, weight painting, texture painting, auto-rigging inside the tool (it is a hand-off), runtime IK or physics, changing a disc row's length, a web viewport as the judging view.

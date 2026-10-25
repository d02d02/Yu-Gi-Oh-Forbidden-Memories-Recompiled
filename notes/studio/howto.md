# Model Studio: glb to game, step by step

Needs: a rigged glb (skeleton plus clips), the disc image for the field and arena runs (the editor passes its own disc on), Python with Tk.

1. Start the editor: `python tools/pc/fm_editor` (a Python that has Tk).
2. Open the **Studio** tab, click **Open glb...**, pick the file. A recipe is saved beside it (`<name>.recipe.json`) and reloaded next time. Undo and Redo are at the top.
3. **S0 Intake:** check the category (the tool guesses; below 60% confidence it asks) and the card number. Fill in author, licence and URL.
4. **S1-S3:** read each check row. Red means fix it (the row names the fix); amber can be accepted with **Accept**.
   `S1 bind-vs-rest` red: the mesh was bound in a different pose than the skeleton rests in. Fix it in Blender and re-open.
5. **S4 Size:** set the size mode and value. Wide or winged creatures: mode `extent`, about 600.
6. **S5 Clips:** map each act (idle, enter, attack, hit, guard, destroyed, win) to a clip. An act the model has no clip for shows a row with **Make a <act> clip**: the tool then makes a simple move itself (a stand-in, listed as such in the report). A library file (`library.path`) can supply clips instead.
7. **S6 Timing, S7 Look:** adjust only if the preview shows a problem.
8. **S8 Validate:** press **Run** on each row (Library turntable, Field attack, Arena attack). The game runs in the background with no window and no sound, and the pictures appear as a contact sheet. Then **Looks right** or **Report a problem**. Run builds its own preview, so S9 is not needed first.
9. **S9 Package, top to bottom:** set the package name; **1. Build package** (builds twice and checks the two results are byte-identical, about 1 minute; the check list above shows `native_check`); **2.** copy the shown folder into the game's `mods` folder (**Open folder** opens it); optional **Save report** writes `report.md` (checks, build, scene runs, and the list of stand-ins) next to the recipe.
10. The preview mod is installed as `game32/mods/studio-preview`. The folder S9 builds is the one to ship.

Logs: `studio.log` (size-capped) and `run.log` per run, in the Studio's work folder.
Missing pieces: a check row that needs a file offers **Open a rigged glb...** (S1/S2 skin and bone map), **Use a clip** or **Library clip...** (S5), and **Choose card...** sets S0 cards. S8 **Scrub the attack live...** holds one running game paused on the attack: drag the slider to a phase, Play/Pause, **Save a shot** (needs a card and the disc). Known limits: one scene per Run launch; see `engine-needs.md`.

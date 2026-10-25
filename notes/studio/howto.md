# Model Studio: glb to game, step by step

Needs: a rigged glb (skeleton plus clips), the disc image for the preview (`MEMORIES_DISC`), Python with Tk.

1. Start the editor: `python tools/pc/fm_editor` (a Python that has Tk).
2. Open the **Studio** tab, click **Open glb**, pick the file. A recipe is saved beside it (`<name>.recipe.json`) and reloaded next time.
3. **S0 Intake:** check the category (the tool guesses; below 60% confidence it asks). Fill in author, licence and URL.
4. **S1-S3:** read each check row. Red means fix it (the row names the fix); amber can be accepted with **Accept**.
   `S1 bind-vs-rest` red: the mesh was bound in a different pose than the skeleton rests in. Fix it in Blender and re-open.
5. **S4 Size:** set the size mode and value. Wide or winged creatures: mode `extent`, about 600.
6. **S5 Clips:** map each act (idle, attack, hit, guard, destroyed, enter, win) to a clip. An act with no clip can use another clip or a procedural move.
7. **S6 Timing, S7 Look:** adjust only if the preview shows a problem.
8. **S9 Package:** **Build package**. It builds twice and the two results must be byte-identical (about 1 minute). **Export report** writes `report.md`.
9. **S8 Validate:** **Run** on Field attack and Arena attack. The game starts by itself (17-55 s). Then **Looks right** or **Report a problem**.
10. The built mod is installed as `game32/mods/studio-preview`. To ship it, copy that mod folder.

Known limits: no live scrub or pause (the game is launched per run); one scene per launch; see `engine-needs.md`.

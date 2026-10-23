# Models view

Page pattern: **List / Index**. The entry point of the add-on. Draft; the questions below decide whether this is its own view or part of the FM Editor's existing "Native models" tab.

## Job
See every native model in the project, open one into the Studio, start a new one, or add a finished package.

## Layout (from the wireframe)
Header: title, one sentence, `[Add finished package]` `[Start from .glb]`. Toolbar in a visible frame: Search (`/` focuses), one Filters control (category, status, card), chips for active filters. Table: Model (name + author/licence line), Category, Card, Stages (ten state dots), Status (Packaged / Needs review / Blocked / In progress), Updated, chevron. Default sort: Updated, newest first. Pager always shown. Empty state inside the frame: "No models yet. Start from a .glb, or add a finished package." with the same two buttons.

## Rules
* Row opens the Studio at the first stage that is not `pass`.
* Start from .glb: pick file, then Studio S0 with the file loaded. No dialog before that.
* Add finished package = today's `native_models.add_package` copy; the row shows stages as `n/a` and Status `Imported`; it can still be opened in the Studio only if a recipe exists.
* Remove model: dialog "Remove model 'Dragon'?" naming what is deleted (recipe, package, built files) and what is kept (the source .glb). Cancel is the default focus.
* Provenance: author, licence and source URL are columns in a details popover, and shown in the Library.

## Questions (this view)
1. Is a list needed at all for one to five models, or is a model picker in the Studio header enough? (Decides whether this is a view or a dropdown.)
2. Where do models live on disk, and does the list read the project's `native_models` entry, a folder scan, or a recipe index?
3. One model on several cards, and variants (palette swaps): one row with several card chips, or several rows?
4. First run: is there a sample model (the mannequin) to open, so a new person sees a finished run?
5. Does a built package that has no recipe (imported) belong in this list?

Decisions go to `open-questions.md`.

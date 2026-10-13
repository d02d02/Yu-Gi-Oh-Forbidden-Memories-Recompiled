# 05 Release strategy per use case

Hard rules (all releases)
- Outward actions are the user's to confirm: opening a PR, publishing a release, posting on Discord, posting a poll. Claude prepares text/zips/SHA and says "not sent" until told.
- Nothing from the disc or personal data in any zip: no ROM, no extracted game data, no `settings.txt`/saves, no personal HD packs. State files hold RAM = disc data: never commit or ship them.
- Repo commits: no `Claude-Session` trailer; identity `git -c user.name=d02d02 -c user.email=334354742+d02d02@users.noreply.github.com`. Push every branch early (unpushed branches lost history once).
- Zips by Python `zipfile` (forward slashes), not Compress-Archive. Record SHA-256 beside each zip.
- No `gh`: fork releases by API with a token from `git credential fill`.
- Test on the **official release exe on a fresh install** before anything that claims to work with it.

## R1 Engine fix / feature as an upstream PR (Unchiga)
Use when: the behaviour lives in `src/` (frame slots, bilinear HD art, PGXP, 4x mips).
1. Branch from `upstream/master` (fetch first; `origin/master` is stale). One topic per branch; names in Unchiga's style; avoid used branch names.
2. Gate: `04` L2 + L3 + L4: affected scenarios A/B at 1x (+2x/4x), vanilla unchanged (feature off = pixel-identical), timing not worse, native CTests/`make check-pc` where available, list NOT verified (Linux/mac/Android).
3. PR text: observed problem -> fix -> observed result; mark measured vs seen; risk section; manual duel test the maintainer can run. Title `Area: what the player sees`.
4. Fallback if upstream is slow: ship the effect as a mod where possible (R2) and keep the PR open; an unofficial exe ("fix pack") only as last resort (R4).
5. Rollback: the PR is revertable by design (small); keep the evidence folder.

## R2 Code mod (C, compiled `.o`: anime-art, duel-links-2d-arts, test-scenes, 3d/2d monsters)
Constraint: no engine change; must run on the released port (currently v0.3.0 SDK).
1. Version bump in `mod.json` (+ HOWTO "What changed"); settings migrations noted (layout change => full zip only).
2. Build `.o` per target with the released SDK `build_mod.py <stage dir> --target i386 --target x86_64-windows` (other targets only if asked). Rebuild after every source change.
3. Declare `conflicts` (e.g. `3d-monsters`); defaults safe (new effects OFF by default).
4. Gate: scene matrix `04` (mixed @1x/2x), vanilla with mod off, fresh official v0.3.0 install with the zip unpacked, mod + assets-hd at the user's internal scale (record result or "not verified").
5. Package: zip (code/, shipped-art/, art/, card-ids.txt as the mod defines), SHA-256, `RELEASE-DRAFT.md` on `Desktop\<mod>-vX.Y\`.
6. Publish: tag on fork `d02d02` master (`<mod>-vX.Y`), asset = zip; source on its feature branch (pushed); Discord post edited **in place** (2000-char limit, masked links; text kept in `..\duel-links-discord-post.md`).
7. Rollback: previous release stays up; mention it in notes; never delete a published asset others use.

## R3 Data / asset mod (HD pack, Duel Links art, kuriboh data)
1. Generated assets stay out of git (`.tex`, HD PNGs); scripts and recipes are in git; originals' credit in the release ("WillliTo & d02d02").
2. Gate: pack builds from originals on a clean checkout; `shared\mods-data\<mod>` single copy; scene shots at 1x and 4x compared with the previous version; size/hash list.
3. Release as zip with a manifest; version in the folder name; known limits stated (platform, internal scale).

## R4 Fix pack (mod + our patched `memories-pc.exe`) / unofficial build
Only when the bug cannot be avoided in a mod. Decision matrix (from the anime-frame case):
| Option | Pros | Cons |
|---|---|---|
| Mod-only + note (recommended) | Official exe untouched, nothing to maintain | Bug remains for those on the official exe |
| Mod + unofficial exe | Fixes it now | Dev build (4.8 MB vs 3.9 MB), AV heuristics, support burden |
| Wait for upstream | Clean | Unbounded |
| Poll first | Evidence of demand | Slow; do not say "sent" until the PR is open |
If shipped: label clearly unofficial, state the base commit, include SHA-256, test official vs fix pack on the fresh matrix (`C:\YFM-fresh\v030-official\...`), keep a path back to the official exe.

## R5 Official port release (Unchiga's `pc-release.yml`)
Not ours to run. Know the flow: tag `vX.Y.Z[-preview.N]` -> Windows zip + Linux tar.gz + macOS app + Android APK -> **draft** GitHub release (pre-release if hyphenated) -> test archives -> publish. Our job is to be able to test a release candidate quickly: run `rigkit.py scene/hand --exe <candidate>` on the standard scenarios and compare to the previous release's outputs (the same A/B runner, `02` #7).

## R6 Personal / dev builds
Never distributed. Worktree fresh by default; personal mods linked only on opt-in (`shared\link.ps1`); `play.bat` for a human test; notes updated in the shared folder.

## Release checklist (copy per release)
- [ ] Type (R1-R4) and base (upstream/master commit, or v0.3.0 SDK)
- [ ] Pre-flight (`04`) done; evidence folder with commands + outputs
- [ ] Vanilla/off unchanged; fresh official install test done
- [ ] Not-verified list written
- [ ] Zip built from tracked files, no personal/disc data; SHA-256 recorded
- [ ] Branch pushed; commit identity ok; no session trailer
- [ ] Drafts ready (release notes, Discord text <= 2000 chars, PR text, poll if any), marked NOT SENT
- [ ] User confirmed each outward step
- [ ] After publish: update `..\INDEX.md` / topic note with release URL, remove resolved pending items

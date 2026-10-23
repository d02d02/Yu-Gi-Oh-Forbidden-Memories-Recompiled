# Job sm2-audit: tests for studio/audit.py (S0-S3), fixing the bugs they find

Read JOB.md first (goal, pasted facts, rules, acceptance). One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. In tests/test_studio_audit.py: the `variant(tmp_dir, mutate)` helper, and class TestFixtures: a no-op variant loads with audit.load_model (53 triangles are not needed: assert 6 bones, names start pelvis, spine_01), a mutation (rename a joint) is visible after loading, and a corrupt file gives audit.AuditError / `S0.load` fail from audit_all
  check: python3 tools/hd-models/tests/test_studio_audit.py -k TestFixtures
- [ ] 2. Class TestS0: S0.licence both ways (fail when empty, absent when set; fix text mentions the file's licence when asset.extras.license exists), S0.attribution, S0.category and S0.category-confidence (unskinned variant: remove skins and the skin keys of the nodes and primitives -> confidence below 60), S0.skins (a second skin), S0.ok
  check: python3 tools/hd-models/tests/test_studio_audit.py -k TestS0
- [ ] 3. Class TestS1Mesh: S1.bones (patch audit.spec.MAX_BONES), S1.weights (warn and fail by percentage: zero the weights of some vertices), S1.influences (add WEIGHTS_1), S1.scale (mesh node scale 0.01 and a non-uniform one), S1.normals (flip normals), S1.size (patch TRIANGLES_WARN), S1.skin (no skin), S1.merge, S1.ok
  check: python3 tools/hd-models/tests/test_studio_audit.py -k TestS1Mesh
- [ ] 4. Class TestS1BindVsRest: no finding when rest == bind; warn between 4% and 12% and fail above 12% (set a joint's rest rotation or translation so the posed mesh drifts, and remove or keep the animations as needed; compute the expected percent yourself and assert the value within 0.2); the finding carries the region name; a clip whose frame 0 matches the bind pose makes the file pass even when the node rest pose is wrong
  check: python3 tools/hd-models/tests/test_studio_audit.py -k TestS1BindVsRest
- [ ] 5. Class TestS2: S2.chains (add a parentless joint: warn, value = count), S2.map (fail for C1, absent for C4 or when recipe rig.humanoid fills the slots), S2.root-side (root far from the body: warn with value; absent when near), S2.reversed-scale, S2.extras-weights, S2.skin, S2.ok
  check: python3 tools/hd-models/tests/test_studio_audit.py -k TestS2
- [ ] 6. Class TestS3: S3.dropped (texCoord 1, an extension), S3.vertex-colour (add COLOR_0), S3.emissive, S3.uv-repeat, S3.memory (patch TEXTURE_MB_WARN to 0), S3.atlas (patch audit.nc.build_textures to raise), S3.ok
  check: python3 tools/hd-models/tests/test_studio_audit.py -k TestS3
- [ ] 7. Class TestIntegration: audit_all on the plain synthetic glb with a full recipe (license, author, category C1... use a category for which the synthetic skeleton does not trigger S2.map or choose C5) then apply_to_studio puts S0-S3 into a state.Studio; states are pass or warn as the findings dictate; acknowledge a warn and it turns pass; edit rig.root and S2 and later stages go stale; report_json is valid JSON with the four stages. Add one line about studio/ to tools/hd-models/README.md
  check: python3 tools/hd-models/tests/test_studio_audit.py -k TestIntegration && grep -q "studio/" tools/hd-models/README.md

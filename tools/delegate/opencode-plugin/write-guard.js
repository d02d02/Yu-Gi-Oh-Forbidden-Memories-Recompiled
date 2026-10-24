// OpenCode plugin: stops the agent from damaging the files that judge it (see notes/delegation-audit.md, 2026-10-24).
// Blocks edit/write of: JOB.md, verify.sh, any path suffix listed in <project>/protected.txt;
// in test_*.py files: touching the `if __name__` / `unittest.main()` tail, dropping an existing test class, writing a
// file without the tail. The thrown message goes back to the model.
import fs from "node:fs"
import path from "node:path"

const classes = (s) => [...String(s || "").matchAll(/^\s*class\s+(\w+)/gm)].map((m) => m[1])

export const WriteGuard = async () => ({
  "tool.execute.before": async (input, output) => {
    if (input.tool !== "edit" && input.tool !== "write") return
    const a = output.args || {}
    const file = a.filePath || a.path
    if (!file) return
    const rel = path.relative(process.cwd(), path.resolve(file)).split(path.sep).join("/")
    let protectedList = []
    try { protectedList = fs.readFileSync("protected.txt", "utf8").split("\n").map((x) => x.trim()).filter(Boolean) } catch {}
    if (["JOB.md", "verify.sh", "protected.txt"].includes(rel) || protectedList.some((p) => rel === p || rel.endsWith("/" + p)))
      throw new Error(`${rel} is protected: the supervisor owns it. If it seems wrong, write BLOCKED with the reason; do not edit it.`)
    if (!/(^|\/)test_[^/]*\.py$/.test(rel)) return
    if (input.tool === "edit") {
      const oldS = a.oldString ?? "", newS = a.newString ?? ""
      if (/__main__|unittest\.main/.test(oldS))
        throw new Error(`Do not edit the tail of ${rel} (if __name__ == "__main__": unittest.main()). Add new test classes ABOVE it, with an edit whose old text is a line above the tail.`)
      const lost = classes(oldS).filter((c) => !classes(newS).includes(c))
      if (lost.length) throw new Error(`This edit would delete test class ${lost.join(", ")} in ${rel}. Existing test classes must stay; make an edit that only adds lines.`)
    } else if (fs.existsSync(file)) {
      const content = a.content ?? ""
      const lost = classes(fs.readFileSync(file, "utf8")).filter((c) => !classes(content).includes(c))
      if (lost.length || !/unittest\.main\(\)/.test(content))
        throw new Error(`Writing ${rel} whole would drop ${lost.join(", ") || "the unittest.main() tail"}. Use edits that only add lines instead.`)
    }
  },
})

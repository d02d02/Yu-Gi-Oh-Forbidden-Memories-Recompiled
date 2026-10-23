// OpenCode plugin: the harness-side twin of ~/.claude/hooks/token_guard.py.
// Blocks `read` of a file over LIMIT lines without offset/limit, and a repeat of an identical read of an unchanged file.
// The thrown message goes back to the model, which then greps and reads a range instead.
import fs from "node:fs"

const LIMIT = 150
const seen = new Map()

export const TokenGuard = async () => ({
  "tool.execute.before": async (input, output) => {
    if (input.tool !== "read") return
    const a = output.args || {}
    const path = a.filePath || a.path
    if (!path || !fs.existsSync(path) || !fs.statSync(path).isFile()) return
    const key = `${path}|${a.offset}|${a.limit}`
    const mtime = fs.statSync(path).mtimeMs
    if (seen.get(key) === mtime) throw new Error(`Already read ${path} this session and it is unchanged. Use what you have, or grep.`)
    if (a.offset === undefined && a.limit === undefined) {
      const n = fs.readFileSync(path, "utf8").split("\n").length
      if (n > LIMIT) throw new Error(`${path} has ${n} lines. Do not read it whole: run \`grep -n "def \|class " ${path}\` (or grep the name you need), then read with offset and limit (at most ${LIMIT} lines).`)
    }
    seen.set(key, mtime)
  },
})

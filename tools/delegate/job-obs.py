#!/usr/bin/env python3
"""End-of-job (or mid-job) report from the router ledger: calls, waste, error classes, latency per model, request size trend.

    python job-obs.py JOB_ID [--ledger PATH] [--append notes/delegation-audit.md]

Reads llm-router/data/ledger.sqlite read-only; rows of the job have job LIKE '<JOB_ID>-%' (ralph names its runs <id>-<timestamp>).
Waste = tokens of failed calls. Request-size trend = mean req_chars per quarter of the calls in time order (a rise = the agent re-reads
files / context bloat)."""
import argparse, collections, sqlite3, statistics as st, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("job")
ap.add_argument("--ledger", default=str(Path.home() / "llm-router" / "data" / "ledger.sqlite"))
ap.add_argument("--append", default="")
a = ap.parse_args()
con = sqlite3.connect(f"file:{a.ledger}?mode=ro", uri=True)
rows = con.execute("SELECT ts,provider,model,ok,tokens,latency_ms,error_class,req_chars FROM calls WHERE job LIKE ? ORDER BY ts", (a.job + "-%",)).fetchall()
if not rows:
    raise SystemExit(f"no ledger rows for job {a.job}")
n, ok = len(rows), sum(1 for r in rows if r[3])
tok, wasted = sum(r[4] or 0 for r in rows), sum(r[4] or 0 for r in rows if not r[3])
span = (rows[-1][0] - rows[0][0]) / 60
out = [f"### Router report: `{a.job}` ({time.strftime('%Y-%m-%d %H:%M', time.localtime(rows[-1][0]))})",
       f"{n} calls over {span:.0f} min, {ok} ok ({100 * ok // n}%), {tok:,} tokens, {wasted:,} wasted ({100 * wasted // max(tok, 1)}%).", "",
       "| model | calls | ok | p50 | p95 |", "|---|---|---|---|---|"]
by = collections.defaultdict(list)
for r in rows:
    by[f"{r[1]}/{r[2]}"].append(r)
for m, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
    lat = sorted(r[5] for r in rs if r[5] and r[3])
    f = lambda p: f"{lat[min(len(lat) - 1, int(len(lat) * p))] / 1000:.1f}s" if lat else "-"
    out.append(f"| {m} | {len(rs)} | {sum(1 for r in rs if r[3])} | {f(.5)} | {f(.95)} |")
errs = collections.Counter(r[6] or "unclassified" for r in rows if not r[3])
if errs:
    out += ["", "Failures: " + ", ".join(f"{k} {v}" for k, v in errs.most_common())]
sizes = [r[7] for r in rows if r[7]]
if len(sizes) >= 8:
    q = len(sizes) // 4
    out += ["", "Request size (mean chars) by quarter: " + " -> ".join(f"{st.mean(sizes[i * q:(i + 1) * q]):,.0f}" for i in range(4))]
text = "\n".join(out)
print(text)
if a.append:
    with open(a.append, "a", encoding="utf-8") as f:
        f.write("\n" + text + "\n")

20260223T022156Z: Pre-fix: CLAUDECODE nesting guard blocked claude -p
20260223T022227Z: Pre-fix: sys.executable bug — judge silently returned 0/0 (workdir had valid 15/15 calculator.py)
20260223T022507Z: Pre-fix: model timed out at 300s, workdir inside project tree
20260223T023043Z: Pre-fix: context contamination — workdir in project tree, model produced file but judge worked (1/15)
20260223T023235Z: Pre-fix: model hallucinated 'calculator.py already exists' due to parent CLAUDE.md context
20260223T023435Z: Pre-fix: same context contamination — model claimed file exists
20260223T024533Z: Post-fix: /tmp/ workdir + --no-session-persistence + --setting-sources user — clean 15/15
20260223T025056Z: First native run — cloud Sonnet missed ValueError for '2 + + 3'
20260223T025244Z: First hybrid run — proxy routed all 6 requests local, 0 cloud
20260223T025244Z: Proxy overhead only ~1.1s across 6 requests (62.9s model inference, 64.0s wall clock). 28s gap vs offline is model variance, not routing.
20260223T044721Z: Post-fairness-fix: warm-up + randomized order. Offline 15/15 in 50.6s
20260223T044823Z: Post-fairness-fix: native 14/15 — same ValueError miss as before
20260223T044853Z: Post-fairness-fix: hybrid 1/15, only 2 requests — model barely engaged
20260223T045515Z: Second fairness run: native 14/15 consistent
20260223T045546Z: Second fairness run: offline 15/15 consistent
20260223T045651Z: stream_options fix: tokens now captured (34.5K/2.4K). 0/15 = model variance (calc returned None)
20260223T050533Z: Offline timed out at 300s but still fixed 4/5 bugs (8/10 tests). Model was thorough but slow.
20260223T051057Z: Hybrid 4/10 — only 4 requests, 523 output tokens. Model barely engaged, fixed 2/5 bugs.
20260223T051134Z: Native 10/10 — cloud Sonnet fixed all 5 bugs in 27s. Best debug_hunt result.
20260223T051208Z: Native 14/20 — missed 6 validation/edge-case tests. 47s.
20260223T051259Z: Offline 14/20 — same pass count as native, different test set likely. 72.5s.
20260223T051418Z: Hybrid 0/20, 4 requests, 1.6K output. Model barely engaged — only produced partial code.
20260223T113533Z: gemma3:4b baseline — no tool support in Ollama (capabilities: completion, vision only). Dead on arrival.
20260223T113549Z: llama3.2:3b baseline — claims tool support but dumped raw JSON to stdout instead of calling Write tool. Broken tool calling.
20260223T113852Z: qwen3:4b baseline — 14/15 ties cloud Sonnet and gpt-oss:20b. Best small model candidate at 2.5GB VRAM.
20260223T114047Z: qwen3:1.7b baseline — 1/15, too small to produce working code. Not viable for background model.
20260223T114240Z: qwen3:4b debug_hunt — timed out at 300s, only fixed 1.5/5 bugs (3/10). Struggles with multi-file reasoning.
20260223T114758Z: qwen3:4b api_server — 0/20 in 12s. Barely engaged, minimal output. Can't handle complex API design.
20260223T115653Z: Split routing calculator — 1/15, bad run. Proxy log shows 0 background-tier requests: claude -p sends all as thinking tier.
20260223T115821Z: Split routing debug_hunt — 10/10 in 65s! Perfect score through proxy. All 25 requests were thinking tier (0 background).
20260223T115933Z: Split routing api_server — 14/20 in 15s. Only 3 requests. All thinking tier, no background requests.
20260223T115933Z: KEY FINDING: claude -p never sends haiku/background-tier requests. Background model routing only fires in interactive agentic sessions with subagent delegation.
20260223T121838Z: qwen3-coder calculator — 15/15 in 49s. Perfect score, faster than gpt-oss:20b (14/15, 59s). Best local model on this scenario.
20260223T121941Z: qwen3-coder debug_hunt — 10/10 in 109s. All 5 bugs fixed. gpt-oss:20b only managed 8/10 with timeout.
20260223T122142Z: qwen3-coder api_server — 14/20 in 197s (exit -15). Ties gpt-oss:20b and cloud Sonnet on pass count but slower.
20260223T122142Z: qwen3-coder SUMMARY: best local model tested (15/15, 10/10, 14/20). Tradeoff: 18GB VRAM vs gpt-oss:20b's 13GB — less headroom for background model coloading on 24GB GPU.
20260223T124435Z: qwen3-coder consistency calculator #2 — 15/15 in 124s. Consistent.
20260223T124656Z: qwen3-coder consistency calculator #3 — 0/0 in 135s. Model described solution in text but didn't call Write tool. Claude Code flake, not model quality issue.
20260223T124929Z: qwen3-coder consistency debug_hunt #2 — 10/10, timed out at 300s. Fixed all 5 bugs but slow.
20260223T125453Z: qwen3-coder consistency debug_hunt #3 — 10/10 in 138s. Solid.
20260223T125726Z: qwen3-coder consistency api_server #2 — 11/20 in 394s. Variance: missed 3 more tests than run 1.
20260223T130436Z: qwen3-coder consistency api_server #3 — 14/20 in 65s. Back to baseline.
20260223T130436Z: CONSISTENCY SUMMARY: calculator 15/15 reliable (1 flake = tool-call miss, not code quality). debug_hunt 10/10 rock solid. api_server 11-14/20 with variance. Wall clock varies 2-3x across runs (Ollama nondeterminism).
20260224T171352Z: First clawdpot run post-extraction — 0/0 because pytest missing from venv. Added pytest to base deps.
20260224T172118Z: calculator 15/15 in 159s. Clean run after pytest fix. Extraction verified working.
20260224T172707Z: debug_hunt 10/10 in 242s. All 5 bugs fixed. Clawdpot fully operational as standalone repo.
20260224T191243Z: CPU test: qwen3:4b calculator — 4/15 in 106.1s. Tool use works but code quality too low.
20260224T192324Z: CPU test: qwen3:4b calculator #2 — 1/15 in 106.2s. Consistent timing, high correctness variance. Model too small.
20260224T193236Z: CPU test: gpt-oss:20b calculator — 14/15 in 29.4s. MoE architecture = fastest CPU model. Near-perfect correctness.
20260224T193628Z: CPU test: qwen3-coder calculator — 15/15 in 87.3s. Perfect score on CPU. Slower than gpt-oss:20b but flawless.
20260224T193628Z: CPU SUMMARY: gpt-oss:20b is best CPU model (speed), qwen3-coder is best CPU model (correctness). qwen3:4b eliminated for CPU — tool use works but quality unusable. MoE (3.6B active params) beats dense 4B on both speed and quality.

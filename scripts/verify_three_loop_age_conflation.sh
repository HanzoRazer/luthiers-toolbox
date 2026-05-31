#!/usr/bin/env bash
# Reproducible verification of the Three-Loop / Vectorizer AGE conflation claim.
#
# Run this from anywhere; point the two env vars at your local clones if they are
# not at the default sibling paths. Every check prints the command, the live
# output, and PASS/FAIL against the documented expectation. Exit code is non-zero
# if any check fails — so CI or a skeptical developer can gate on it.
#
#   RT=/path/to/luthiers-toolbox SB=/path/to/vectorizer-sandbox \
#     bash scripts/verify_three_loop_age_conflation.sh
#
# Companion doc: docs/handoffs/THREE_LOOP_AGE_CONFLATION_EVIDENCE_PACKET.md
set -u

RT="${RT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SB="${SB:-$RT/../vectorizer-sandbox}"

fail=0
hr() { printf '%s\n' "------------------------------------------------------------"; }
check() {  # check "<label>" "<actual>" "<expected>"
  local label="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    printf '  PASS  %-46s (%s)\n' "$label" "$actual"
  else
    printf '  FAIL  %-46s got=%s want=%s\n' "$label" "$actual" "$expected"
    fail=1
  fi
}

echo "Three-Loop / Vectorizer AGE conflation — live verification"
echo "RT=$RT"
echo "SB=$SB"
hr
echo "Repo anchors (record these; the packet is anchored to runtime 7210d78):"
echo "  runtime HEAD : $(git -C "$RT" rev-parse HEAD 2>/dev/null || echo '??')"
echo "  sandbox HEAD : $(git -C "$SB" rev-parse HEAD 2>/dev/null || echo '??')"
hr

echo "FACT 1 — named architecture exists in ZERO code files"
rt_cls=$(git -C "$RT" grep -nE "class (ValidatedExtractor|AdaptiveExtractor|VectorizerAGE)\b" -- '*.py' 2>/dev/null | wc -l | tr -d ' ')
sb_cls=$(git -C "$SB" grep -nE "class (ValidatedExtractor|AdaptiveExtractor|VectorizerAGE)\b" -- '*.py' 2>/dev/null | wc -l | tr -d ' ')
rt_any=$(git -C "$RT" grep -lE "VectorizerAGE|ValidatedExtractor|AdaptiveExtractor" -- '*.py' 2>/dev/null | grep -v archive | wc -l | tr -d ' ')
check "runtime class definitions"        "$rt_cls" "0"
check "sandbox class definitions"        "$sb_cls" "0"
check "runtime any .py mention (non-archive)" "$rt_any" "0"
hr

echo "FACT 2 — names appear ONLY in markdown prose"
py_hits=$(git -C "$RT" grep -lE "VectorizerAGE|ValidatedExtractor|AdaptiveExtractor" 2>/dev/null | grep -c '\.py$' | tr -d ' ')
md_hits=$(git -C "$RT" grep -lE "VectorizerAGE|ValidatedExtractor|AdaptiveExtractor" 2>/dev/null | grep -c '\.md$' | tr -d ' ')
check "runtime .py files containing names" "$py_hits" "0"
echo "        (markdown files containing names: $md_hits — informational)"
git -C "$RT" grep -lE "VectorizerAGE|ValidatedExtractor|AdaptiveExtractor" 2>/dev/null | sed 's/^/          /'
hr

echo "FACT 3 — CLAUDE.md already corrected (conflation removed)"
hdr=$(git -C "$RT" show HEAD:CLAUDE.md 2>/dev/null | grep -c "EXPERIMENTAL, SANDBOXED" | tr -d ' ')
check "CLAUDE.md has EXPERIMENTAL/SANDBOXED header" "$hdr" "1"
echo "        reframe commit:"
git -C "$RT" log --oneline -S "EXPERIMENTAL, SANDBOXED" -- CLAUDE.md 2>/dev/null | head -1 | sed 's/^/          /'
hr

echo "FACT 4 — real runtime scale gate (decoupled, must NOT be deleted)"
gate=$(git -C "$RT" show HEAD:services/blueprint-import/vectorizer_phase3.py 2>/dev/null | grep -cE "def _safe_dxf_save|def validate_scale_before_export" | tr -d ' ')
check "scale-gate function defs present" "$gate" "2"
hr

echo "FACT 5 — two-repo seam + collision surface are real"
util=$(git -C "$RT" show HEAD:services/api/app/util/dxf_compat.py 2>/dev/null | wc -l | tr -d ' ')
bp=$(git -C "$RT" show HEAD:services/blueprint-import/dxf_compat.py 2>/dev/null | wc -l | tr -d ' ')
rt_p3=$(git -C "$RT" show HEAD:services/blueprint-import/vectorizer_phase3.py 2>/dev/null | wc -l | tr -d ' ')
sb_p3=$(git -C "$SB" show HEAD:src/incubation/vectorizer_phase3.py 2>/dev/null | wc -l | tr -d ' ')
sb_gate=$(git -C "$SB" show HEAD:src/incubation/vectorizer_phase3.py 2>/dev/null | grep -cE "validate_scale_before_export|_safe_dxf_save" | tr -d ' ')
check "app/util/dxf_compat.py line count"      "$util" "176"
check "blueprint-import/dxf_compat.py line count" "$bp" "200"
echo "        phase3 runtime=$rt_p3  sandbox=$sb_p3  (delta informational), sandbox scale-gate hits=$sb_gate"
hr

if [ "$fail" -eq 0 ]; then
  echo "RESULT: ALL CHECKS PASS — conflation claim is substantiated by primary evidence."
else
  echo "RESULT: ONE OR MORE CHECKS FAILED — re-read output above; numbers may have"
  echo "        moved with new commits. Re-anchor against the current HEAD shown."
fi
exit "$fail"

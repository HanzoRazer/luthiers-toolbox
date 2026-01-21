<script setup lang="ts">
type RiskLevel = "GREEN" | "YELLOW" | "RED";

type HistoryItem = {
  decision: RiskLevel;
  note?: string | null;
  decided_at_utc?: string | null;
  decided_by?: string | null;
};

const props = defineProps<{
  items?: HistoryItem[] | null;
  currentDecision?: RiskLevel | null;
  currentNote?: string | null;
  currentBy?: string | null;
  currentAt?: string | null;
}>();

function fmtTs(ts?: string | null) {
  if (!ts) return "";
  // Keep it simple/robust: show raw ISO-ish; UI can prettify later if desired.
  return ts.replace("T", " ").replace("Z", " UTC");
}

function label(d: RiskLevel) {
  if (d === "GREEN") return "GREEN (Accept)";
  if (d === "YELLOW") return "YELLOW (Caution)";
  return "RED (Reject)";
}
</script>

<template>
  <div class="pop">
    <div class="head">
      <div class="title">
        Decision history
      </div>
      <div
        v-if="currentDecision"
        class="sub"
      >
        Current: <span class="mono">{{ currentDecision }}</span>
      </div>
      <div
        v-else
        class="sub"
      >
        Current: <span class="mono">NEEDS_DECISION</span>
      </div>
    </div>

    <div
      v-if="currentDecision"
      class="current"
    >
      <div class="row">
        <span class="pill">{{ label(currentDecision) }}</span>
        <span
          v-if="currentBy || currentAt"
          class="muted"
        >
          <span v-if="currentBy">{{ currentBy }}</span><span v-if="currentBy && currentAt"> · </span><span v-if="currentAt">{{ fmtTs(currentAt) }}</span>
        </span>
      </div>
      <div
        v-if="currentNote"
        class="note"
      >
        {{ currentNote }}
      </div>
      <div
        v-else
        class="note muted"
      >
        No note.
      </div>
    </div>

    <div
      v-if="items && items.length"
      class="list"
    >
      <div
        v-for="(it, idx) in items"
        :key="idx"
        class="item"
      >
        <div class="row">
          <span class="pill">{{ label(it.decision) }}</span>
          <span
            v-if="it.decided_by || it.decided_at_utc"
            class="muted"
          >
            <span v-if="it.decided_by">{{ it.decided_by }}</span><span v-if="it.decided_by && it.decided_at_utc"> · </span><span v-if="it.decided_at_utc">{{ fmtTs(it.decided_at_utc) }}</span>
          </span>
        </div>
        <div
          v-if="it.note"
          class="note"
        >
          {{ it.note }}
        </div>
        <div
          v-else
          class="note muted"
        >
          No note.
        </div>
      </div>
    </div>
    <div
      v-else
      class="muted"
    >
      No history yet (first decision will populate it).
    </div>
  </div>
</template>

<style scoped>
.pop { width: 420px; max-width: 80vw; padding: 10px; border: 1px solid rgba(0,0,0,0.14); border-radius: 12px; background: white; box-shadow: 0 10px 30px rgba(0,0,0,0.10); }
.head { display: flex; flex-direction: column; gap: 2px; margin-bottom: 8px; }
.title { font-weight: 700; }
.sub { font-size: 12px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.muted { opacity: 0.75; }
.current { border: 1px solid rgba(0,0,0,0.10); border-radius: 10px; padding: 8px; margin-bottom: 8px; background: rgba(0,0,0,0.02); }
.list { display: grid; gap: 8px; }
.item { border-top: 1px dashed rgba(0,0,0,0.14); padding-top: 8px; }
.row { display: flex; gap: 8px; align-items: center; justify-content: space-between; }
.pill { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid rgba(0,0,0,0.14); background: rgba(0,0,0,0.02); white-space: nowrap; }
.note { margin-top: 6px; font-size: 12px; line-height: 1.3; white-space: pre-wrap; }
</style>

/**
 * useIssuesScrubber - Navigation through filtered CAM issues list
 */
import { computed, watch, type Ref, type ComputedRef } from "vue";
import type { SimIssue } from "@/types/cam";
import { type SeverityOption } from "./useSeverityFilter";

export interface IssuesScrubberOptions {
  issues: Ref<SimIssue[]>;
  selectedIndex: Ref<number | null>;
  activeSeveritiesSet: ComputedRef<Set<SeverityOption>>;
  activeSeverities: Ref<SeverityOption[]>;
  onFocusRequest?: (payload: { index: number; issue: SimIssue }) => void;
}

export function useIssuesScrubber(options: IssuesScrubberOptions) {
  const { issues, selectedIndex, activeSeveritiesSet, activeSeverities, onFocusRequest } = options;

  /**
   * Filtered index list: indices into issues that pass current filter.
   */
  const filteredIndices = computed<number[]>(() => {
    const indices: number[] = [];
    const set = activeSeveritiesSet.value;
    issues.value.forEach((iss, idx) => {
      const sev = (iss.severity || "medium") as SeverityOption;
      if (set.has(sev)) indices.push(idx);
    });
    return indices;
  });

  const count = computed(() => filteredIndices.value.length);
  const hasIssues = computed(() => count.value > 0);

  /**
   * Position of current selection within the filtered indices.
   */
  const filteredPosition = computed<number | null>(() => {
    if (!hasIssues.value) return null;
    const idx = selectedIndex.value;
    if (idx == null) return null;
    const list = filteredIndices.value;
    const pos = list.indexOf(idx);
    return pos === -1 ? null : pos;
  });

  const canPrev = computed(() => {
    if (!hasIssues.value) return false;
    const pos = filteredPosition.value;
    if (pos == null) return false;
    return pos > 0;
  });

  const canNext = computed(() => {
    if (!hasIssues.value) return false;
    const pos = filteredPosition.value;
    if (pos == null) return false;
    return pos < count.value - 1;
  });

  const currentLabel = computed(() => {
    if (!hasIssues.value) return "0 / 0";
    const pos = filteredPosition.value ?? 0;
    return `${pos + 1} / ${count.value}`;
  });

  /**
   * Select a given index into issues, optionally emitting a focus-request.
   */
  function selectIndex(idx: number | null, emitFocus: boolean) {
    if (idx == null || idx < 0 || idx >= issues.value.length) {
      selectedIndex.value = null;
      return;
    }
    const issue = issues.value[idx];
    selectedIndex.value = idx;
    if (emitFocus && issue && onFocusRequest) {
      onFocusRequest({ index: idx, issue });
    }
  }

  function handleClick(idx: number) {
    selectIndex(idx, true);
  }

  function jumpPrev() {
    if (!canPrev.value) return;
    const list = filteredIndices.value;
    const pos = filteredPosition.value;
    if (pos == null || pos <= 0) return;
    const nextIdx = list[pos - 1];
    selectIndex(nextIdx, true);
  }

  function jumpNext() {
    if (!canNext.value) return;
    const list = filteredIndices.value;
    const pos = filteredPosition.value;
    if (pos == null || pos >= list.length - 1) return;
    const nextIdx = list[pos + 1];
    selectIndex(nextIdx, true);
  }

  /**
   * If the filter changes and the current selection is outside of the
   * filtered set, gently move the selection to the first filtered item.
   */
  watch(
    () => activeSeverities.value,
    () => {
      if (!hasIssues.value) {
        selectedIndex.value = null;
        return;
      }
      const pos = filteredPosition.value;
      if (pos == null) {
        const firstIdx = filteredIndices.value[0];
        selectIndex(firstIdx, false);
      }
    }
  );

  return {
    filteredIndices,
    count,
    hasIssues,
    filteredPosition,
    canPrev,
    canNext,
    currentLabel,
    selectIndex,
    handleClick,
    jumpPrev,
    jumpNext,
  };
}

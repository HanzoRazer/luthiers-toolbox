import { defineStore } from 'pinia';
import type {
  DxfBatchPreviewResponse,
  DxfGuidedBatchPreviewRequest,
  DxfGuidedSlicePreviewRequest,
} from '@/models/rmos_dxf';

const API = '/rmos/saw-ops';

export const useDxfSliceStore = defineStore('dxfSlices', {
  state: () => ({
    loading: false,
    error: null as string | null,
    lastSlicePreview: null as any,
    lastBatchPreview: null as DxfBatchPreviewResponse | null,
  }),

  actions: {
    async previewSlice(payload: DxfGuidedSlicePreviewRequest) {
      this.loading = true;
      this.error = null;
      try {
        const res = await fetch(`${API}/slice/preview-dxf`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`DXF slice preview failed: ${res.status}`);
        this.lastSlicePreview = await res.json();
        return this.lastSlicePreview;
      } catch (err: any) {
        this.error = err?.message ?? String(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async previewBatch(payload: DxfGuidedBatchPreviewRequest) {
      this.loading = true;
      this.error = null;
      try {
        const res = await fetch(`${API}/batch/preview-dxf`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`DXF batch preview failed: ${res.status}`);
        this.lastBatchPreview = await res.json();
        return this.lastBatchPreview;
      } catch (err: any) {
        this.error = err?.message ?? String(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },
  },
});

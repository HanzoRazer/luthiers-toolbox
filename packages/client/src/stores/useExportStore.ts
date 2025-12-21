import { defineStore } from 'pinia';

const API = '/rmos/exports';
type ExportStoreShape = { loading: boolean; error: string | null };

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function resolveFilename(contentDisposition: string | null, fallback: string) {
  if (!contentDisposition) return fallback;
  const match = /filename="([^"]+)"/.exec(contentDisposition);
  return match?.[1] ?? fallback;
}

export const useExportStore = defineStore('rmosExports', {
  state: () => ({
    loading: false,
    error: null as string | null,
  }),

  actions: {
    async exportPlanJson(payload: any) {
      const store = this as unknown as ExportStoreShape;
      await requestExport(store, `${API}/manufacturing-plan.json`, payload, 'manufacturing_plan.json');
    },

    async exportPlanPdf(payload: any) {
      const store = this as unknown as ExportStoreShape;
      await requestExport(store, `${API}/manufacturing-plan.pdf`, payload, 'manufacturing_plan.pdf');
    },

    async exportBatchGcode(batchOp: any) {
      const store = this as unknown as ExportStoreShape;
      await requestExport(store, `${API}/saw-batch.gcode`, { batch_op: batchOp }, 'saw_batch.gcode');
    },

    async exportJigJson(payload: any) {
      const store = this as unknown as ExportStoreShape;
      await requestExport(store, `${API}/jig-template.json`, payload, 'jig_template.json');
    },

    async exportJigPdf(payload: any) {
      const store = this as unknown as ExportStoreShape;
      await requestExport(store, `${API}/jig-template.pdf`, payload, 'jig_template.pdf');
    },
  },
});

async function requestExport(
  store: ExportStoreShape,
  url: string,
  payload: any,
  fallbackName: string,
) {
  store.loading = true;
  store.error = null;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Export failed (${res.status})`);
    const blob = await res.blob();
    const filename = resolveFilename(res.headers.get('Content-Disposition'), fallbackName);
    downloadBlob(blob, filename);
  } catch (err: any) {
    store.error = err?.message ?? String(err);
    throw err;
  } finally {
    store.loading = false;
  }
}

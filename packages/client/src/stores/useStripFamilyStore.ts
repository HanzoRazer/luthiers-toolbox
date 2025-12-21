/**
 * RMOS Strip Family Store (MM-0)
 * 
 * Manages mixed-material strip families with template instantiation support.
 */
import { defineStore } from 'pinia';
import type { StripFamily } from '@/models/strip_family';

const API = '/api/rmos/strip-families';

export const useStripFamilyStore = defineStore('stripFamilies', {
  state: () => ({
    families: [] as StripFamily[],
    templates: [] as StripFamily[],
    selected: null as StripFamily | null,
    loading: false,
    error: null as string | null,
  }),

  getters: {
    byId: (state) => (id: string) => state.families.find((f) => f.id === id),
  },

  actions: {
    async fetchFamilies() {
      this.loading = true;
      try {
        const res = await fetch(`${API}/`);
        if (!res.ok) throw new Error(`Failed to load strip families: ${res.status}`);
        this.families = await res.json();
        this.error = null;
      } catch (err: any) {
        this.error = err?.message ?? String(err);
      } finally {
        this.loading = false;
      }
    },

    async fetchTemplates() {
      this.loading = true;
      this.error = null;
      try {
        const res = await fetch(`${API}/templates`);
        if (!res.ok) throw new Error(`Fetch templates failed: ${res.status}`);
        this.templates = await res.json();
      } catch (e: any) {
        this.error = e?.message ?? String(e);
      } finally {
        this.loading = false;
      }
    },

    select(f: StripFamily | null) {
      this.selected = f;
    },

    async createFromTemplate(templateId: string) {
      this.loading = true;
      this.error = null;
      try {
        const res = await fetch(`${API}/from-template/${encodeURIComponent(templateId)}`, {
          method: 'POST',
        });
        if (!res.ok) throw new Error(`Create from template failed: ${res.status}`);
        const created = await res.json();
        await this.fetchFamilies();
        this.selected = created;
        return created;
      } catch (e: any) {
        this.error = e?.message ?? String(e);
        throw e;
      } finally {
        this.loading = false;
      }
    },

    async getById(familyId: string) {
      try {
        const res = await fetch(`${API}/${encodeURIComponent(familyId)}`);
        if (!res.ok) throw new Error(`Get strip family failed: ${res.status}`);
        return await res.json();
      } catch (e: any) {
        this.error = e?.message ?? String(e);
        throw e;
      }
    },

    async createFamily(payload: StripFamily) {
      const res = await fetch(`${API}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Failed to create strip family: ${res.status}`);
      const created = await res.json();
      this.families.push(created);
      return created;
    },

    async updateFamily(id: string, payload: Partial<StripFamily>) {
      const res = await fetch(`${API}/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Failed to update strip family: ${res.status}`);
      const updated = await res.json();
      const idx = this.families.findIndex((f) => f.id === id);
      if (idx >= 0) this.families[idx] = updated;
      return updated;
    },

    async deleteFamily(id: string) {
      const res = await fetch(`${API}/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`Failed to delete strip family: ${res.status}`);
      const idx = this.families.findIndex((f) => f.id === id);
      if (idx >= 0) this.families.splice(idx, 1);
    },
  },
});

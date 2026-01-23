import { defineStore } from "pinia";
import { requestAdvisory, AIContextPacket } from "./api";

export const useAiAdvisoryStore = defineStore("aiAdvisory", {
  state: () => ({
    loading: false as boolean,
    error: null as string | null,
    advisory: null as any,
  }),
  actions: {
    async run(packet: AIContextPacket) {
      this.loading = true;
      this.error = null;
      try {
        this.advisory = await requestAdvisory(packet);
      } catch (e: any) {
        this.error = e?.response?.data?.detail?.message ?? String(e);
      } finally {
        this.loading = false;
      }
    },
    clear() {
      this.advisory = null;
      this.error = null;
    },
  },
});

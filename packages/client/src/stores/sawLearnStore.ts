import { defineStore } from 'pinia'

interface SawLearnState {
  runsLoaded: boolean
  insights: string[]
}

export const useSawLearnStore = defineStore('sawLearn', {
  state: (): SawLearnState => ({
    runsLoaded: false,
    insights: [],
  }),
  actions: {
    async refreshInsights(): Promise<void> {
      this.runsLoaded = true
      this.insights = []
    },
  },
})

# AI-CAM Advisor Product Specification

**Product Name:** AI-CAM Advisor
**Tagline:** "The Machinist's Co-Pilot"
**Status:** Concept / Future Product Category
**Last Updated:** 2026-01-30

---

## Executive Summary

AI-CAM Advisor is a proposed product that adds LLM-powered intelligence to the CNC machining workflow. Unlike the current physics-based Calculator Spine (which uses formulas and threshold checks), AI-CAM Advisor provides natural language explanations, context-aware recommendations, and learns from job history.

This is a **separate product category** from the core Luthier's Toolbox - not a build blocker for the current CAM pipeline.

---

## Current State (Wave 11)

The existing `_experimental/ai_cam/` module provides:

```
┌─────────────────────────────────────────────────────────────────┐
│  CURRENT: Calculator Spine + Rule Engine                        │
├─────────────────────────────────────────────────────────────────┤
│  • Chipload calculations (physics formulas)                     │
│  • Heat risk scoring (thermal model)                            │
│  • Tool deflection (beam bending math)                          │
│  • G-code pattern matching (regex rules)                        │
│  • Z-depth warnings (threshold checks)                          │
│                                                                 │
│  NO LLM - just math and conditionals                            │
└─────────────────────────────────────────────────────────────────┘
```

### Current Endpoints

| Endpoint | Function | AI? |
|----------|----------|-----|
| `/api/ai-cam/analyze-operation` | Physics-based risk analysis | No (formulas) |
| `/api/ai-cam/explain-gcode` | Line-by-line G-code annotation | No (regex) |
| `/api/ai-cam/optimize` | Parameter tuning suggestions | No (search) |

---

## Vision: Full AI-CAM Advisor

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI-CAM ADVISOR                               │
│              "The Machinist's Co-Pilot"                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PRE-FLIGHT (Before Cutting)                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  • "This mahogany + 1/4" endmill combo typically        │   │
│  │     burns at 18000 RPM. Try 12000 with 0.003" chip."    │   │
│  │  • "Your DOC is aggressive for this stickout. Here's    │   │
│  │     a 3-pass strategy that's safer."                    │   │
│  │  • "I see you're cutting binding channels - consider    │   │
│  │     climb milling for cleaner edge on maple."           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  IN-FLIGHT (During Operation)                           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  • Real-time spindle load monitoring                    │   │
│  │  • "Load spike at X=145 Y=230 - grain direction?"       │   │
│  │  • Adaptive feed override suggestions                   │   │
│  │  • Tool wear prediction from cut patterns               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  POST-FLIGHT (After Cutting)                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  • "Job completed in 12:34. Similar jobs average 14:00  │   │
│  │     - your feed optimization saved 10%."                │   │
│  │  • "3 near-miss events detected. Review attached."      │   │
│  │  • Learning: "Updating mahogany profile with your       │   │
│  │     successful parameters."                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  KNOWLEDGE MODES                                        │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  🎸 Luthier Mode     - Guitar-specific cutting wisdom   │   │
│  │  🪵 Wood Mode        - Species grain, moisture, etc.    │   │
│  │  🔧 Machinist Mode   - General CNC best practices       │   │
│  │  📚 Learning Mode    - Builds from YOUR job history     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Example Interactions

### Scenario 1: Pre-Cut Advisory

```
User: "Pocket this f-hole in spruce"

AI:   "Spruce tears easily cross-grain. I recommend:
       1. Roughing pass at 40% stepover (conventional)
       2. Finish pass at 10% stepover (climb)
       3. Leave 0.5mm for hand cleanup on treble side
       Want me to generate this toolpath?"
```

### Scenario 2: Troubleshooting

```
User: "Why did my last cut burn?"

AI:   "Looking at job #2847... Your chip load was 0.001"
       (rubbing, not cutting). At 18000 RPM in rosewood,
       you need 1800mm/min feed, not 800. Also, the
       toolpath had 47 direction reversals - try smoother
       spiral entry next time."
```

### Scenario 3: Tool Selection

```
User: "What's the best bit for ebony fretboards?"

AI:   "From 234 jobs in the community database:
       • 2-flute carbide upcut, 3.175mm (73% success)
       • Single-flute O-flute, 3mm (89% success, slower)
       • Diamond-coated compression (96% success, $$$)
       Your machine has the single-flute in slot T3."
```

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI-CAM STACK                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   Claude/   │   │  RAG over   │   │  Physics    │           │
│  │   GPT-4o    │ + │  Job History│ + │  Calculator │           │
│  │  (Reasoning)│   │  (Vector DB)│   │  (Formulas) │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│         │                 │                 │                   │
│         └────────────────┼─────────────────┘                   │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CONTEXT ASSEMBLY                            │   │
│  │  • Current job parameters                                │   │
│  │  • Tool/material profiles                                │   │
│  │  • Machine capabilities                                  │   │
│  │  • Historical similar jobs                               │   │
│  │  • Community wisdom (anonymized)                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ADVISORY OUTPUT                             │   │
│  │  • Natural language explanations                         │   │
│  │  • Specific parameter recommendations                    │   │
│  │  • Risk scores with rationale                            │   │
│  │  • Alternative strategies                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Comparison

| Feature | Current (Physics) | AI-CAM Advisor |
|---------|------------------|----------------|
| Parameter validation | Threshold checks | Context-aware reasoning |
| Recommendations | Generic warnings | Material/tool specific |
| Natural language | Error codes only | "Here's why..." explanations |
| Learning | Static rules | Learns from your jobs |
| Multi-step strategies | Single pass only | "Rough then finish" plans |
| Troubleshooting | N/A | "Why did X happen?" analysis |
| Community knowledge | N/A | Anonymized shared wisdom |

---

## Data Requirements

### Input Data Sources

1. **Job Parameters**
   - Tool ID, material ID, feed, RPM, DOC, WOC
   - Machine profile (travel limits, spindle power)
   - Toolpath geometry (moves, retracts, plunges)

2. **Historical Data (RAG)**
   - Past job logs with outcomes (success/fail/burn/chatter)
   - Parameter combinations that worked
   - User feedback and corrections

3. **Knowledge Base**
   - Wood species properties (hardness, grain, moisture)
   - Tool catalogs with cutting characteristics
   - Machine-specific quirks and limits
   - Luthier-specific cutting techniques

### Output Formats

```json
{
  "advisory_id": "adv-2026-01-30-001",
  "severity": "warning",
  "category": "thermal",
  "message": "This mahogany + 1/4\" endmill combo typically burns at 18000 RPM.",
  "recommendation": {
    "rpm": 12000,
    "feed_mm_min": 1500,
    "chipload_target": 0.076
  },
  "rationale": "Based on 47 similar jobs, reducing RPM by 33% eliminates burn risk while maintaining MRR.",
  "confidence": 0.87,
  "sources": ["job-1234", "job-1567", "community-mahogany-guide"]
}
```

---

## Proposed Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ai-cam/v2/advise` | POST | Get pre-flight advisory for job |
| `/api/ai-cam/v2/explain` | POST | Natural language G-code explanation |
| `/api/ai-cam/v2/troubleshoot` | POST | Analyze why a job failed |
| `/api/ai-cam/v2/suggest-tool` | POST | Recommend tool for operation |
| `/api/ai-cam/v2/optimize` | POST | AI-driven parameter optimization |
| `/api/ai-cam/v2/learn` | POST | Submit job outcome for learning |
| `/api/ai-cam/v2/chat` | POST | Conversational CAM assistant |

---

## Business Model Considerations

### Pricing Tiers

| Tier | Features | Target User |
|------|----------|-------------|
| **Free** | Physics calculator only | Hobbyists |
| **Pro** | + Pre-flight advisories | Small shops |
| **Enterprise** | + Learning + Community | Production facilities |

### Cost Drivers

- LLM API calls (~$0.01-0.05 per advisory)
- Vector DB hosting for RAG
- Job history storage
- Community data aggregation

---

## Implementation Phases

### Phase 1: Foundation (4-6 weeks)
- [ ] Vector DB setup for job history
- [ ] RAG pipeline for similar job retrieval
- [ ] Basic LLM integration for explanations
- [ ] `/api/ai-cam/v2/advise` endpoint

### Phase 2: Intelligence (6-8 weeks)
- [ ] Multi-step strategy generation
- [ ] Tool recommendation engine
- [ ] Troubleshooting from job logs
- [ ] `/api/ai-cam/v2/troubleshoot` endpoint

### Phase 3: Learning (8-10 weeks)
- [ ] Job outcome feedback loop
- [ ] Personal profile refinement
- [ ] Community wisdom aggregation
- [ ] `/api/ai-cam/v2/learn` endpoint

### Phase 4: Real-time (Future)
- [ ] Machine integration (spindle load)
- [ ] In-flight advisories
- [ ] Adaptive feed control
- [ ] Emergency stop recommendations

---

## Dependencies

- **LLM Provider:** Claude Sonnet 4 or GPT-4o
- **Vector DB:** Pinecone, Weaviate, or pgvector
- **Existing Systems:**
  - Calculator Spine (physics formulas)
  - Tool/Material profiles
  - Job logging infrastructure
  - RMOS governance (for safety constraints)

---

## Risk Factors

| Risk | Mitigation |
|------|------------|
| LLM hallucination | Physics calculator as ground truth |
| Liability for bad advice | Clear disclaimers + RMOS safety gates |
| API cost overruns | Caching + rate limiting |
| User trust | Transparency in reasoning sources |

---

## Success Metrics

1. **Adoption:** % of jobs using AI advisory
2. **Accuracy:** Advisory accuracy vs job outcome
3. **Engagement:** Questions asked per user/month
4. **Value:** Reduction in failed cuts / material waste
5. **Learning:** Model improvement over time

---

## References

- Current implementation: `services/api/app/_experimental/ai_cam/`
- Calculator Spine: `services/api/app/_experimental/calculators/`
- RMOS governance: `services/api/app/rmos/`

---

*This document defines a future product category. Implementation is not a blocker for current Luthier's Toolbox releases.*

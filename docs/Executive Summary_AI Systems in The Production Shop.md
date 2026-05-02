Executive Summary: AI Systems in The Production Shop
Vision Generation System — Schema & Script Structure
The Vision Generation Router (generation_router.py) is an AI image generation pipeline for guitar concept art. Its schema chain:

Schema (in schemas.py)	Role
VisionGenerateRequest	Inbound — prompt, provider (openai/stub), model, size, quality, num_images
VisionAsset	Per-image result — sha256, CAS URL, mime, filename, provider, model, revised_prompt
VisionGenerateResponse	Outbound — List[VisionAsset] + request_id
VisionPromptPreviewRequest	Dry-run — prompt + style, no generation
VisionPromptPreviewResponse	Returns raw_prompt, engineered_prompt, photography_style
VisionVocabularyResponse	UI dropdown data (body shapes, finishes, woods, etc.)
Script flow:

prompt_engine.py — expands casual text + photography style (product, dramatic, studio, vintage, etc.) into rendering-ready prompts with universal suffix ("ultra high detail, accurate guitar geometry")
vocabulary.py — pure data: 14 body shapes, 8 finishes, 8 woods, 7 hardware types, 4 inlay types, 7 photography styles
generation_router.py — calls ai.transport.get_image_client() → external AI provider → stores bytes via put_bytes_attachment() into CAS (content-addressed store)
blob_router.py — serves stored images at /api/advisory/blobs/{sha256}/download (browser-loadable, immutable cache)
How the 6 AI Systems Relate
The repo contains 6 distinct AI subsystems with hard boundaries between them:


┌─────────────────────────────────────────────────────────────────┐│                    ai/transport/ (Platform Layer)                ││         LLMClient · ImageClient · VisionClient                  ││         ai/safety/ (content policy RED/YELLOW/GREEN)            ││         ai/observability/ (audit log, X-Request-Id)             ││         ai/cost/ (pre-generation pricing estimates)             ││  ───────────────── HARD WALL: all AI calls go through here ──── │└──────┬──────────┬──────────┬──────────┬────────────┬────────────┘       │          │          │          │            │       ▼          ▼          ▼          ▼            ▼┌──────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────────────┐│  Vision  │ │ Vision  │ │Agentic │ │AI Context│ │ CAM Learning ││Generation│ │Segment- │ │ Spine  │ │ Adapter  │ │              ││          │ │ ation   │ │        │ │          │ │              ││ DALL-E → │ │GPT-4o → │ │Event → │ │Run data →│ │Telemetry →  ││ concept  │ │polygon  │ │moments │ │redacted  │ │feed override││ art      │ │extract  │ │→direct-│ │envelope  │ │scalars      ││          │ │→DXF/SVG │ │ives    │ │for ext AI│ │             │└──────────┘ └─────────┘ └────────┘ └──────────┘ └─────────────┘                                          │                              ┌────────────┘                              ▼                    ┌───────────────────┐                    │ _experimental/    │                    │ ai_cam_router.py  │                    │ (AI-assisted CAM) │                    └───────────────────┘
System	Location	AI Provider	Input → Output	Relationship to Vision Gen
1. Vision Generation	vision/generation_router.py	ImageClient (DALL-E 3)	Text prompt → guitar concept images (CAS)	This system
2. Vision Segmentation	vision/segmentation_router.py	VisionClient (GPT-4o)	Guitar photo → body polygon (mm) → DXF/SVG/G-code	Sibling — same vision/ package, same advisory blob storage, but uses VisionClient not ImageClient. Generation creates images; segmentation analyzes them.
3. Agentic Spine	agentic/spine/	None (rule-based)	Event streams → detected moments → attention directives	Independent — no AI provider calls. Detects user hesitation/overload/decisions and emits UWSM-based directives. Lives in the manufacturing tool, not image generation.
4. AI Context Adapter	ai_context_adapter/	None (data prep)	RMOS run data → redacted envelope for external AI	Downstream consumer — could package Vision assets into context envelopes. Enforces hard manufacturing fence (strips G-code, toolpaths, PII).
5. CAM Learning	routers/cam_learn_router.py	None (statistical)	CAM run telemetry → learned feed/speed overrides	No relationship — pure statistical learning from CNC run logs, no image or language model.
6. Experimental AI CAM	_experimental/ai_cam_router.py	LLMClient	Natural language → CAM operations	No relationship — text-to-CAM, experimental.
Cross-Repo: Smart Guitar Agentic AI (sg-spec)
The sg-spec repo defines a separate 5-agent coaching system for the Smart Guitar product:

Agent	Function
Player State Agent	Tracks physical playing state
Intent Detection Agent	Infers Practice/Performance/Exploration mode
Guidance Strategy Agent	Policy matrix (Mode × Backoff → intervention rules)
Coaching & Feedback Agent	Delivers haptic/visual/audio/text feedback
Memory & Personalization Agent	Long-term progress tracking
Schemas: guidance-policy.schema.json, take-events.schema.json, coach-decision.schema.json, renderer-payloads.schema.json

Boundary: The sg-spec AI system is entirely separate from luthiers-toolbox AI. Per governance rules, no runtime imports cross repo boundaries — only artifact contracts (JSON/DXF). The luthiers-toolbox agentic/spine/ is a manufacturing-tool agent (user workflow moments); the sg-spec agents are instrument-runtime agents (player coaching). They share no code, no providers, and no schemas.

Key Architectural Invariants
All AI calls route through ai/transport/ — no domain module may call OpenAI/Anthropic directly
Safety enforcement is centralized in ai/safety/ — GREEN/YELLOW/RED content policy
Every AI call is audited via ai/observability/audit_log.py with X-Request-Id propagation
Generated assets are content-addressed — sha256 deduplication, immutable blobs
Manufacturing data never leaks — AI Context Adapter strips 30+ forbidden keys before external AI consumption
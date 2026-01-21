/**
 * RMOS Domain Clients
 *
 * Barrel export for all RMOS-related SDK modules.
 */

export * as runs from "./runs";
export * as workflow from "./workflow";
export * as operations from "./operations";
export * as runsAttachments from "./runs_attachments";

// Re-export common types for convenience
export type {
  RunArtifact,
  RunArtifactLite,
  RunAttachment,
  SignedAttachment,
  ListRunsParams,
  ListRunsResponse,
  AdvisoryExplanation,
  ExplainRunResponse,
  RunDiffResult,
  AddOverrideRequest,
  AddOverrideResponse,
} from "./runs";

export type {
  CamIntentV1,
  FeasibilityResult,
  ExecuteOperationRequest,
  ExecuteOperationResponse,
  PlanOperationRequest,
  PlanOperationResponse,
} from "./operations";

export type {
  RunAttachmentRow,
  RunAttachmentsListResponse,
} from "./runs_attachments";

export type {
  WorkflowSessionLite,
  WorkflowSessionState,
  WorkflowEvent,
  WorkflowMode,
  WorkflowState,
  ActorRole,
  RiskBucket,
  GeneratorInfo,
  TransitionResponse,
  ApproveResponse,
} from "./workflow";

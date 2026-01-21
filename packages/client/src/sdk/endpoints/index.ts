/**
 * SDK Endpoints Index (H8.3)
 *
 * Per-endpoint typed helpers that wrap SDK transport.
 * All helpers return consistent shapes with requestId for correlation.
 *
 * Usage:
 *   import { cam } from "@/sdk/endpoints";
 *   
 *   const { gcode, summary, requestId } = await cam.roughingGcode(payload);
 *   const { result, requestId } = await cam.runPipeline(formData);
 */

export * as cam from "./cam/cam";
export * as artDesignFirstWorkflow from "./artDesignFirstWorkflow";
export * as rmosAcoustics from "./rmosAcoustics";
export * as rmosAcousticsIngest from "./rmosAcousticsIngest";

/**
 * H8.3 CAM Endpoint Tests
 *
 * Validates typed helpers:
 * - Header parsing (X-CAM-Summary)
 * - Request-id extraction
 * - Consistent return shapes
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { roughingGcode, roughingGcodeIntent } from "../roughing";
import { runPipeline } from "../pipeline";
import * as apiFetchRaw from "@/sdk/core/apiFetchRaw";

describe("CAM Endpoints (H8.3)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("roughingGcode", () => {
    it("returns gcode + summary + requestId", async () => {
      const mockResponse = new Response("G21\nG90\nM30\n", {
        headers: {
          "x-request-id": "req_test123",
          "X-CAM-Summary": JSON.stringify({
            gcode_lines: 3,
            toolpath_length_mm: 120.5,
          }),
        },
      });

      vi.spyOn(apiFetchRaw, "postRaw").mockResolvedValue({
        data: "G21\nG90\nM30\n",
        response: mockResponse,
      });

      const result = await roughingGcode({
        entities: [],
        tool_diameter: 6,
        depth_per_pass: 2,
        stock_thickness: 10,
        feed_xy: 1200,
        feed_z: 300,
        safe_z: 5,
        tabs_count: 4,
        tab_width: 5,
        tab_height: 1,
        post: "GRBL",
      });

      expect(result.gcode).toBe("G21\nG90\nM30\n");
      expect(result.requestId).toBe("req_test123");
      expect(result.summary).toEqual({
        gcode_lines: 3,
        toolpath_length_mm: 120.5,
      });
    });

    it("handles missing X-CAM-Summary gracefully", async () => {
      const mockResponse = new Response("G21\nM30\n", {
        headers: {
          "x-request-id": "req_test456",
        },
      });

      vi.spyOn(apiFetchRaw, "postRaw").mockResolvedValue({
        data: "G21\nM30\n",
        response: mockResponse,
      });

      const result = await roughingGcode({
        entities: [],
        tool_diameter: 6,
        depth_per_pass: 2,
        stock_thickness: 10,
        feed_xy: 1200,
        feed_z: 300,
        safe_z: 5,
        tabs_count: 4,
        tab_width: 5,
        tab_height: 1,
        post: "GRBL",
      });

      expect(result.summary).toBeNull();
      expect(result.requestId).toBe("req_test456");
    });

    it("handles malformed X-CAM-Summary without crashing", async () => {
      const mockResponse = new Response("G21\nM30\n", {
        headers: {
          "x-request-id": "req_test789",
          "X-CAM-Summary": "not valid json{",
        },
      });

      vi.spyOn(apiFetchRaw, "postRaw").mockResolvedValue({
        data: "G21\nM30\n",
        response: mockResponse,
      });

      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

      const result = await roughingGcode({
        entities: [],
        tool_diameter: 6,
        depth_per_pass: 2,
        stock_thickness: 10,
        feed_xy: 1200,
        feed_z: 300,
        safe_z: 5,
        tabs_count: 4,
        tab_width: 5,
        tab_height: 1,
        post: "GRBL",
      });

      expect(result.summary).toBeNull();
      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining("Failed to parse X-CAM-Summary"),
        expect.any(String)
      );
    });
  });

  describe("roughingGcodeIntent", () => {
    it("appends ?strict=true when strict mode enabled", async () => {
      const mockResponse = new Response("G21\nG90\nM30\n", {
        headers: {
          "x-request-id": "req_strict",
          "X-CAM-Summary": JSON.stringify({ intent_issues: [] }),
        },
      });

      const postRawSpy = vi
        .spyOn(apiFetchRaw, "postRaw")
        .mockResolvedValue({
          data: "G21\nG90\nM30\n",
          response: mockResponse,
        });

      await roughingGcodeIntent({ design: {} }, true);

      expect(postRawSpy).toHaveBeenCalledWith(
        "/cam/roughing_gcode_intent?strict=true",
        { design: {} }
      );
    });

    it("omits ?strict when not enabled", async () => {
      const mockResponse = new Response("G21\nG90\nM30\n", {
        headers: { "x-request-id": "req_nonstrict" },
      });

      const postRawSpy = vi
        .spyOn(apiFetchRaw, "postRaw")
        .mockResolvedValue({
          data: "G21\nG90\nM30\n",
          response: mockResponse,
        });

      await roughingGcodeIntent({ design: {} }, false);

      expect(postRawSpy).toHaveBeenCalledWith(
        "/cam/roughing_gcode_intent",
        { design: {} }
      );
    });
  });

  describe("runPipeline", () => {
    it("returns result + requestId from FormData submission", async () => {
      const mockResponse = new Response(
        JSON.stringify({ status: "success", job_id: "job_123" }),
        {
          headers: {
            "x-request-id": "req_pipeline",
            "content-type": "application/json",
          },
        }
      );

      vi.spyOn(apiFetchRaw, "postFormRaw").mockResolvedValue({
        data: { status: "success", job_id: "job_123" },
        response: mockResponse,
      });

      const form = new FormData();
      form.append("config", "test_config");

      const result = await runPipeline(form);

      expect(result.requestId).toBe("req_pipeline");
      expect(result.result).toEqual({
        status: "success",
        job_id: "job_123",
      });
    });
  });
});

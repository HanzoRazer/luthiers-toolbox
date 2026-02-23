/**
 * useRosetteDesignerExport - Export functions for Rosette Designer
 */
import type { Ref } from "vue";
import type { RosetteDimensions } from "./useRosetteDesignerState";

export function useRosetteDesignerExport(
  dimensions: Ref<RosetteDimensions>,
  status: Ref<string>
) {
  /**
   * Export pattern as SVG image
   */
  function exportPatternImage() {
    try {
      // Wait a moment for canvas to fully render
      setTimeout(() => {
        // Try multiple selectors to find the SVG
        let canvas = document.querySelector(
          ".canvas-workspace svg"
        ) as SVGElement;
        if (!canvas) {
          canvas = document.querySelector(
            ".rosette-canvas-container svg"
          ) as SVGElement;
        }
        if (!canvas) {
          canvas = document.querySelector("svg") as SVGElement;
        }
        if (!canvas) {
          status.value = "❌ Canvas not found - try applying a template first";
          console.error("SVG canvas element not found in DOM");
          console.log("Available elements:", {
            canvasWorkspace: document.querySelector(".canvas-workspace"),
            rosetteContainer: document.querySelector(
              ".rosette-canvas-container"
            ),
            anySvg: document.querySelectorAll("svg").length,
          });
          return;
        }

        // Clone the SVG to avoid modifying the original
        const svgClone = canvas.cloneNode(true) as SVGElement;

        // Ensure proper SVG namespace attributes for standalone file
        svgClone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        svgClone.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
        svgClone.setAttribute("version", "1.1");

        // Get dimensions if not set
        if (!svgClone.getAttribute("width")) {
          svgClone.setAttribute("width", "600");
        }
        if (!svgClone.getAttribute("height")) {
          svgClone.setAttribute("height", "600");
        }

        // Serialize SVG to string
        const svgData = new XMLSerializer().serializeToString(svgClone);

        // Check if SVG has content
        if (svgData.length < 100) {
          status.value = "❌ Canvas appears empty - apply a template first";
          console.error("SVG content too small:", svgData.length, "bytes");
          return;
        }

        const svgBlob = new Blob([svgData], {
          type: "image/svg+xml;charset=utf-8",
        });

        // Create download link
        const url = URL.createObjectURL(svgBlob);
        const link = document.createElement("a");
        link.href = url;
        const timestamp = new Date()
          .toISOString()
          .replace(/[:.]/g, "-")
          .slice(0, -5);
        link.download = `rosette-pattern-${timestamp}.svg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        status.value = "✅ Pattern image exported as SVG";
        console.log("SVG export successful:", svgData.length, "bytes");
      }, 100); // Small delay to ensure rendering is complete
    } catch (error) {
      status.value = `❌ Export failed: ${error instanceof Error ? error.message : String(error)}`;
      console.error("Export error:", error);
    }
  }

  /**
   * Export dimension sheet (placeholder)
   */
  function exportDimensionSheet() {
    status.value = "📄 Dimension sheet export (coming soon)";
    // TODO: Generate PDF with annotations
  }

  /**
   * Export channel path as G-code
   */
  function exportChannelPath() {
    try {
      if (
        !dimensions.value.soundholeDiameter ||
        !dimensions.value.rosetteWidth
      ) {
        status.value = "❌ Please set dimensions first";
        return;
      }

      status.value = "🔧 Generating simple circular channel path...";

      // Calculate channel path (outer radius of rosette)
      const soundholeRadius = dimensions.value.soundholeDiameter / 2;
      const channelRadius = soundholeRadius + dimensions.value.rosetteWidth;
      const depth = dimensions.value.channelDepth || 1.5;
      const feedRate = 800; // mm/min for routing

      // Generate simple circular G-code
      const gcode = [
        "; Rosette Channel Path - Simple Circular Routing",
        `; Generated: ${new Date().toISOString()}`,
        "; WARNING: This is a simplified circular path only",
        "; Rosettes are typically hand-assembled, not CNC-carved",
        "",
        "G21 ; Units in mm",
        "G90 ; Absolute positioning",
        "G17 ; XY plane",
        "",
        "; Safe Z height",
        "G0 Z5.0",
        "",
        "; Move to start position (X positive, Y=0)",
        `G0 X${channelRadius.toFixed(3)} Y0.000`,
        "",
        "; Plunge to depth",
        `G1 Z${(-depth).toFixed(3)} F300`,
        "",
        "; Circular interpolation (full circle)",
        `G2 X${channelRadius.toFixed(3)} Y0.000 I${(-channelRadius).toFixed(3)} J0.000 F${feedRate}`,
        "",
        "; Retract",
        "G0 Z5.0",
        "",
        "M30 ; Program end",
        "",
      ].join("\n");

      // Create download
      const blob = new Blob([gcode], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const timestamp = new Date()
        .toISOString()
        .replace(/[:.]/g, "-")
        .slice(0, -5);
      link.download = `rosette-channel-${timestamp}.nc`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      status.value = "✅ Channel path exported (basic circular toolpath)";
      console.log("G-code export successful:", gcode.length, "bytes");
    } catch (error) {
      status.value = `❌ Channel path export failed: ${error instanceof Error ? error.message : String(error)}`;
      console.error("G-code export error:", error);
    }
  }

  return {
    exportPatternImage,
    exportDimensionSheet,
    exportChannelPath,
  };
}

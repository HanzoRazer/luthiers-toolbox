# End-to-End Dev Flow

1. Start Mock RMOS:
   ```
   ./scripts/ai_dev/run_mock_rmos.sh
   ```

2. Start ToolBox frontend:
   ```
   ./scripts/ai_dev/run_toolbox_dev.sh
   ```

3. Load a sample evidence pack in ToolBox.

4. Click a spectrum peak to set selection.

5. Click **Explain selection**.

6. Advisory should render in ToolBox using AiAdvisoryRenderer.

## Debug tips

- Use curl script to verify Mock RMOS independently.
- Use browser devtools → Network to inspect request/response.
- Mock RMOS supports forced errors via request.request.debug.force_error.

---
name: zai-vision
description: "Analyze images, screenshots, diagrams, charts, and videos using z.ai vision MCP tools. Use when Dan shares an image, screenshot, video, or when visual analysis is needed. Tools: ui_to_artifact, extract_text_from_screenshot, diagnose_error_screenshot, understand_technical_diagram, analyze_data_visualization, ui_diff_check, analyze_image, analyze_video. All 8 tools tested & validated (2026-02-21)."
metadata:
  openclaw:
    emoji: "👁️"
    requires:
      env: ["Z_AI_API_KEY"]
      bins: ["npx"]
    mcp:
      server: "zai-vision"
      command: "npx -y @z_ai/mcp-server@latest"
    notes: "Key goes in ~/.mcporter/mcporter.json under mcpServers.zai-vision.env (NOT ~/.hermes/config.yaml). Env var name is Z_AI_API_KEY (underscore between Z and AI, not ZAI_API_KEY)."
---

# z.ai Vision Tools

Analyze images, screenshots, diagrams, charts, and videos using the z.ai vision MCP server.

**Status:** ✅ All 8 tools tested and validated (2026-02-21)

---

## When to Use

✅ **USE this skill when:**

- Dan shares a screenshot (UI, error, anything visual)
- Dan shares a photo (robot hardware, whiteboard, etc.)
- Dan shares a chart, graph, or data visualization
- Dan shares an architecture or technical diagram
- Dan shares a video or screen recording
- You need text extracted from an image (OCR)
- Comparing two versions of a UI

---

## Tool Selection Guide

| Situation | Tool | What It Does |
|-----------|------|--------------|
| Screenshot of app/UI | `ui_to_artifact` | Generate design spec from UI screenshot |
| Error message/stack trace | `diagnose_error_screenshot` | Debug error with root cause + solutions |
| Chart, graph, plot | `analyze_data_visualization` | Interpret data trends and metrics |
| Architecture/system diagram | `understand_technical_diagram` | Explain components and data flow |
| Need text from screenshot | `extract_text_from_screenshot` | OCR extraction of visible text |
| Comparing UI versions | `ui_diff_check` | Side-by-side diff analysis |
| Photo/scene description | `analyze_image` | General image understanding |
| Video/clip analysis | `analyze_video` | Summarize video content |

---

## How to Invoke

These tools are accessed via the `zai-vision` MCP server through mcporter.

**Example invocations (via mcporter tool calls):**

```
# UI to design spec
ui_to_artifact(image_source="/path/to/screenshot.png", output_type="description", prompt="Describe this UI")

# Diagnose error
diagnose_error_screenshot(image_source="/path/to/error.png", prompt="What's causing this error?")

# Extract text
extract_text_from_screenshot(image_source="/path/to/menu.png", prompt="Extract all visible text")

# Analyze chart
analyze_data_visualization(image_source="/path/to/chart.png", prompt="What trends does this chart show?")

# General image analysis
analyze_image(image_source="/path/to/photo.jpg", prompt="Describe this image in detail")

# Video summary
analyze_video(video_source="/path/to/clip.mp4", prompt="Summarize what happens in this video")
```

---

## Tips

### Don't Just Describe — Extract

When Dan shares a screenshot, don't just say "I see a button and some text." Use the right tool to:

- **Generate actionable output** (design specs, debug steps)
- **Extract structured data** (OCR text, component lists)
- **Provide analysis** (trends in charts, root causes in errors)

### Error Screenshots → Real Debugging

The `diagnose_error_screenshot` tool produces detailed debugging guides with:
- Root cause analysis
- Code examples for fixes
- Prevention strategies

### UI Screenshots → Design Specs

The `ui_to_artifact` tool can generate:
- Component specifications
- Markup examples
- Token/design system mappings

---

## mcporter Server Setup

For persistent zai-vision server (auto-loaded by mcporter), create `~/.mcporter/mcporter.json`:

```json
{
  "mcpServers": {
    "zai-vision": {
      "command": "npx",
      "args": ["-y", "@z_ai/mcp-server@latest"]
    }
  }
}
```

Requires `ZAI_API_KEY` in environment. Then call with:
```
mcporter call zai-vision.analyze_image image_source=/path/to/file.jpg prompt="..."
```

---

## Limitations

- **File paths:** Local file paths work (the MCP server can read them)
- **Large images:** No known size limits, but very large images may be slow
- **Video length:** Longer videos take more time to process

---

## Test Results

All 8 tools validated on 2026-02-21 with synthetic test inputs:

| Tool | Status | Output Quality |
|------|--------|----------------|
| `ui_to_artifact` | ✅ Pass | 176-line design spec |
| `extract_text_from_screenshot` | ✅ Pass | 33 lines extracted text |
| `diagnose_error_screenshot` | ✅ Pass | 5KB debug guide with code |
| `understand_technical_diagram` | ✅ Pass | Architecture explanation |
| `analyze_data_visualization` | ✅ Pass | Chart interpretation |
| `ui_diff_check` | ✅ Pass | Diff analysis |
| `analyze_image` | ✅ Pass | Scene description |
| `analyze_video` | ✅ Pass | Video summary |

Full test suite: `research/2026-02-20-zai-vision-test-suite/`

---

## Related

- **TOOLS.md** — Local notes on MCP server configuration
- **mcporter** — MCP server management CLI
- **z.ai API** — Requires `ZAI_API_KEY` environment variable

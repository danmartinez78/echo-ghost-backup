---
name: zai-web
description: "Search the web and fetch page content using z.ai MCP tools. Use when you need web search or content extraction. Tools: webSearchPrime (search with filters), webReader (fetch and extract page content), zread (search documentation repos)."
metadata:
  {
    "openclaw":
      {
        "emoji": "🌐",
        "requires": { "env": ["ZAI_API_KEY"], "bins": ["npx"] },
        "mcp": { "server": "zai-web", "command": "npx -y @z_ai/mcp-server@latest" },
      },
  }
---

# z.ai Web Tools

Search the web and fetch content using z.ai MCP tools.

**Tools:** `webSearchPrime`, `webReader`, `zread`

---

## When to Use

✅ **USE this skill when:**

- You need to search the web for current information
- You need to fetch and extract content from a URL
- You need to search documentation from popular repos
- Brave Search quota is exhausted (backup option)

---

## Tools

### webSearchPrime

Web search with domain and recency filters.

**Parameters:**
- `search_query` — What to search for
- `search_domain_filter` — Limit to specific domains (optional)
- `search_recency_filter` — Time-based filter (optional)
- `content_size` — Max content to return (optional)
- `location` — Geographic location for results (optional)

**Example:**
```
webSearchPrime(
  search_query="OpenClaw memory systems",
  search_recency_filter="month",
  content_size=5000
)
```

**Gotcha:** Even with `location=us`, results can be China-weighted. Use `search_domain_filter` for English-only sources.

---

### webReader

Fetch and extract readable content from a URL.

**Parameters:**
- `url` — The URL to fetch
- `timeout` — Request timeout (optional)
- `no_cache` — Bypass cache (optional)
- `return_format` — Output format (optional)
- `retain_images` — Keep images in output (optional)

**Example:**
```
webReader(
  url="https://docs.openclaw.ai/memory",
  return_format="markdown"
)
```

**Use when:** You need full page content, not just search snippets.

---

### zread

Search and read documentation from popular repositories.

**Tools:**
- `search_doc(repo_name, query, language?)` — Search documentation
- `get_repo_structure(repo_name, dir_path?)` — Browse repo structure
- `read_file(repo_name, file_path)` — Read specific file

**Supported repos:** Popular documentation repos (check z.ai for current list)

**Example:**
```
search_doc(
  repo_name="openai",
  query="function calling",
  language="en"
)
```

---

## Fallback Strategy

| Primary | Fallback | When to Switch |
|---------|----------|----------------|
| Brave Search (`web_search`) | `webSearchPrime` | Brave quota exhausted |
| `webReader` | `web_fetch` (built-in) | If MCP fails |

---

## Limitations

- **API key required:** `ZAI_API_KEY` must be set
- **Search bias:** Results may be China-weighted; use domain filters
- **Rate limits:** Unknown — haven't hit them yet

---

## Related

- **TOOLS.md** — Local notes on MCP configuration
- **mcporter** — MCP server management
- **web_search** — Built-in Brave Search (primary)
- **web_fetch** — Built-in content fetcher (backup)

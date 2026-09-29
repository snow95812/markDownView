import os
import re
from html import escape
from typing import List, Tuple

import markdown

from markdown_parser import parse_markdown


def render_markdown_html(markdown_text: str, fallback_title: str) -> Tuple[str, str, List[Tuple[int, str, str]], int]:
    md = markdown.Markdown(extensions=["extra", "toc", "sane_lists"])
    body_html = md.convert(markdown_text)
    toc_items = _flatten_toc(getattr(md, "toc_tokens", []))

    document = parse_markdown(markdown_text, fallback_title=fallback_title)
    title = document.title or fallback_title
    meta_count = len(document.blocks)

    html = _build_html(title, body_html)
    return title, html, toc_items, meta_count


def _flatten_toc(tokens, level=1, items=None):
    if items is None:
        items = []
    for token in tokens:
        token_level = int(token.get("level", level))
        items.append((token_level, token.get("name", ""), token.get("id", "")))
        children = token.get("children", [])
        if children:
            _flatten_toc(children, token_level + 1, items)
    return items


def _build_html(title: str, body_html: str) -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fa;
      --card: #ffffff;
      --text: #24292f;
      --muted: #57606a;
      --border: #d0d7de;
      --accent: #0969da;
      --code-bg: #f6f8fa;
      --quote-border: #d0d7de;
    }}
    * {{
      box-sizing: border-box;
    }}
    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      line-height: 1.6;
    }}
    body {{
      overflow: hidden;
    }}
    .preview-shell {{
      height: 100vh;
      padding: 24px;
    }}
    .preview-scroll {{
      height: 100%;
      overflow: auto;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 8px 28px rgba(31, 35, 40, 0.08);
    }}
    .markdown-body {{
      max-width: 980px;
      margin: 0 auto 24px;
      background: var(--card);
      padding: 32px 40px;
    }}
    .markdown-body h1,
    .markdown-body h2,
    .markdown-body h3,
    .markdown-body h4,
    .markdown-body h5,
    .markdown-body h6 {{
      font-weight: 600;
      line-height: 1.25;
      margin-top: 24px;
      margin-bottom: 16px;
      padding-bottom: 0.3em;
      border-bottom: 1px solid var(--border);
      scroll-margin-top: 24px;
    }}
    .markdown-body h1 {{ font-size: 2em; }}
    .markdown-body h2 {{ font-size: 1.5em; }}
    .markdown-body h3 {{ font-size: 1.25em; }}
    .markdown-body p,
    .markdown-body ul,
    .markdown-body ol,
    .markdown-body blockquote,
    .markdown-body table,
    .markdown-body pre {{
      margin-top: 0;
      margin-bottom: 16px;
    }}
    .markdown-body a {{
      color: var(--accent);
      text-decoration: none;
    }}
    .markdown-body a:hover {{
      text-decoration: underline;
    }}
    .markdown-body code {{
      background: rgba(175, 184, 193, 0.2);
      border-radius: 6px;
      padding: 0.18em 0.4em;
      font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, monospace;
      font-size: 0.92em;
    }}
    .markdown-body pre {{
      background: #0d1117;
      color: #e6edf3;
      border-radius: 10px;
      padding: 16px;
      overflow: auto;
    }}
    .markdown-body pre code {{
      background: transparent;
      color: inherit;
      padding: 0;
    }}
    .markdown-body blockquote {{
      margin-left: 0;
      padding: 0 1em;
      color: var(--muted);
      border-left: 0.25em solid var(--quote-border);
    }}
    .markdown-body table {{
      display: block;
      width: max-content;
      max-width: 100%;
      overflow: auto;
      border-spacing: 0;
      border-collapse: collapse;
    }}
    .markdown-body table th,
    .markdown-body table td {{
      border: 1px solid var(--border);
      padding: 6px 13px;
    }}
    .markdown-body table tr:nth-child(2n) {{
      background: #f6f8fa;
    }}
    .markdown-body img {{
      max-width: 100%;
    }}
    .markdown-body hr {{
      height: 0.25em;
      padding: 0;
      margin: 24px 0;
      background: var(--border);
      border: 0;
    }}
    .mermaid {{
      display: flex;
      justify-content: center;
      padding: 16px;
      margin: 16px 0;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: auto;
    }}
  </style>
</head>
<body>
  <div class="preview-shell">
    <div class="preview-scroll">
      <article class="markdown-body">
        {body_html}
      </article>
    </div>
  </div>
  <script src="assets/mermaid.min.js"></script>
  <script>
    function getMermaidApi() {{
      if (window.mermaid) {{
        return window.mermaid;
      }}
      if (window.__esbuild_esm_mermaid_nm && window.__esbuild_esm_mermaid_nm.mermaid) {{
        return window.__esbuild_esm_mermaid_nm.mermaid;
      }}
      return null;
    }}

    function convertMermaidBlocks() {{
      const blocks = document.querySelectorAll('pre code.language-mermaid, pre code.lang-mermaid, pre code.mermaid, pre.mermaid code');
      blocks.forEach(function(code, index) {{
        const container = document.createElement('div');
        container.className = 'mermaid';
        container.id = 'mermaid-block-' + index;
        container.textContent = code.textContent;
        const pre = code.parentElement;
        pre.parentElement.replaceChild(container, pre);
      }});
      const mermaidApi = getMermaidApi();
      if (mermaidApi) {{
        mermaidApi.initialize({{
          startOnLoad: false,
          securityLevel: 'loose',
          theme: 'default',
          flowchart: {{
            htmlLabels: true,
            useMaxWidth: true
          }}
        }});
        mermaidApi.run({{ querySelector: '.mermaid' }});
      }}
    }}

    function scrollToHeading(id) {{
      const target = document.getElementById(id);
      if (target) {{
        target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }}

    if (document.readyState === 'loading') {{
      document.addEventListener('DOMContentLoaded', convertMermaidBlocks);
    }} else {{
      convertMermaidBlocks();
    }}
  </script>
</body>
</html>
""".format(title=escape(title), body_html=body_html)

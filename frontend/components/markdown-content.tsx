"use client";

import type { KatexOptions } from "katex";
import { memo } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

const katexOptions: KatexOptions = {
  throwOnError: false,
  strict: "ignore"
};

/**
 * Characters that signal genuine TeX/LaTeX syntax inside a `$...$` span.
 * If the content between two `$` contains any of these, we treat it as math
 * (e.g. `$2^n$`, `$3 \times 4$`). Otherwise a `$` immediately followed by a
 * digit is treated as currency (e.g. `$100`) and escaped so remark-math
 * does not mis-pair it.
 */
const MATH_CHARS = /[\\^_{}]/;

/**
 * Pre-processes raw markdown so that currency amounts like `$100` are not
 * misinterpreted by remark-math as inline-math delimiters, while genuine
 * digit-leading math like `$2^n$` is preserved.
 *
 * Rules (scanned left-to-right, skipping code spans / fenced code / block math):
 *  - `$$...$$`  → block math, left untouched.
 *  - `` `...` `` / ``` ```...``` ``` → code, left untouched.
 *  - `$` + digit, with a later `$` whose intervening content has a math char
 *    → genuine inline math (e.g. `$2^n$`), kept verbatim.
 *  - `$` + digit, with a later `$` whose content has NO math char
 *    → currency; escape only this opening `$` (the later `$` is left for
 *      remark-math to use as a new delimiter or literal).
 *  - `$` + digit, no later `$` → lone currency `$`, escape it.
 *  - `$` not followed by a digit → untouched (remark-math handles it).
 */
const escapeCurrency = (input: string): string => {
  const out: string[] = [];
  let i = 0;
  const n = input.length;
  while (i < n) {
    // Skip fenced code blocks (```)
    if (input.startsWith("```", i)) {
      const close = input.indexOf("```", i + 3);
      const end = close === -1 ? n : close + 3;
      out.push(input.slice(i, end));
      i = end;
      continue;
    }
    // Skip inline code spans (`)
    if (input[i] === "`") {
      const close = input.indexOf("`", i + 1);
      const end = close === -1 ? n : close + 1;
      out.push(input.slice(i, end));
      i = end;
      continue;
    }
    // Skip block math $$...$$
    if (input[i] === "$" && input[i + 1] === "$") {
      const close = input.indexOf("$$", i + 2);
      const end = close === -1 ? n : close + 2;
      out.push(input.slice(i, end));
      i = end;
      continue;
    }
    // $ followed by a digit → potential currency
    if (input[i] === "$" && /\d/.test(input[i + 1] ?? "")) {
      const closeIdx = input.indexOf("$", i + 1);
      if (closeIdx !== -1) {
        const content = input.slice(i + 1, closeIdx);
        if (MATH_CHARS.test(content)) {
          // genuine inline math (e.g. $2^n$) — keep verbatim
          out.push(input.slice(i, closeIdx + 1));
          i = closeIdx + 1;
          continue;
        }
        // currency — escape only the opening $, leave the rest for remark-math
        out.push("\\$");
        i += 1;
        continue;
      }
      // lone $ before digits with no closing $ — escape it
      out.push("\\$");
      i += 1;
      continue;
    }
    out.push(input[i]);
    i += 1;
  }
  return out.join("");
};

export const MarkdownContent = memo(({ content }: { content: string }) => (
  <div className="markdown-body">
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[[rehypeKatex, katexOptions], rehypeHighlight]}
    >
      {escapeCurrency(content)}
    </ReactMarkdown>
  </div>
));

MarkdownContent.displayName = "MarkdownContent";

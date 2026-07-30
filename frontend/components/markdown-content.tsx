"use client";

import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import type { KatexOptions } from "katex";

const katexOptions: KatexOptions = {
  throwOnError: false,
  strict: "ignore"
};

export const MarkdownContent = memo(({ content }: { content: string }) => (
  <div className="markdown-body">
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[[rehypeKatex, katexOptions], rehypeHighlight]}
    >
      {content}
    </ReactMarkdown>
  </div>
));

MarkdownContent.displayName = "MarkdownContent";

# Markdown + KaTeX Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render Markdown + KaTeX math in chat messages and a new /markdown-demo page in the Next.js 15 frontend.

**Architecture:** Shared client component `MarkdownContent` (react-markdown + remark-gfm + remark-math + rehype-katex + rehype-highlight, memo'd) consumed by `app/page.tsx` (chat) and `app/markdown-demo/page.tsx` (server component reading `sample.md` via fs). KaTeX/highlight.js CSS imported in `app/layout.tsx` (NOT the component) so node:test/tsx can import the component without a CSS loader and because `components/` is outside the `app/` global-CSS boundary.

**Tech Stack:** Next.js 15.5.14, React 18.2, react-markdown 10.1.0, remark-gfm 4.0.1, remark-math 6.0.0, rehype-katex 7.0.1, rehype-highlight 7.0.2, katex 0.18.1, highlight.js 11.11.1, node:test + tsx (existing repo test pattern).

**Spec:** `docs/superpowers/specs/2026-07-30-markdown-katex-rendering-design.md`

## Global Constraints

- NO git commits anywhere in this plan (repo AGENTS.md: never commit unless the user explicitly asks).
- No `as any` / `@ts-ignore` / `@ts-expect-error`.
- Function components + arrow functions; named exports; no Tailwind (plain CSS in `app/globals.css`).
- Test pattern: `node:test` + `assert/strict` via tsx (see `frontend/lib/user-id.test.ts`).
- KB convention: update `frontend/ai/currentTask.md` (MISSING — create), `handoff/latest.md`, `decisions.md` after major changes.
- TDD: RED (stub, assertion failure) → GREEN (full impl) → SURFACE (Playwright DOM counts + screenshot).

## Scenario Contract

- **S1 happy**: `npm run build` exit 0; dev server GET /markdown-demo 200; Playwright DOM counts exactly 9 `.katex-display`, 18 `.katex`, ≥1 `code.hljs`; screenshot `/tmp/markdown-demo.png`.
- **S2 edge**: invalid TeX `$\frac$` renders `katex-error`, no throw (streaming-safe).
- **S3 regression**: GET / 200, 0 console errors, feature-flag admin panel renders.
- **S4 test-first**: `npm test` RED→GREEN logs captured; existing `lib/user-id.test.ts` still passes (15 tests total GREEN).

## Task Dependency Graph

| Task | Depends On | Reason |
|------|------------|--------|
| T1 package.json: 7 deps + test script | None | Foundation; `npm install` unblocks tests/build |
| T2 app/markdown-demo/sample.md | None | Pure content file (verbatim from spec) |
| T3 components/markdown-content.tsx (RED stub) | None | Stub first so RED fails on assertion, not import |
| T4 components/markdown-content.test.tsx (RED tests) | None | Test harness file |
| T5 RED gate: `npm test` | T1 install, T2, T3, T4 | Confirm RED = assertion failures |
| T6 components/markdown-content.tsx (GREEN full) | T5 | Implement only after RED confirmed |
| T7 app/layout.tsx CSS imports | T1 | node_module CSS must resolve |
| T8 app/globals.css .markdown-body | None | Pure CSS append |
| T9 app/markdown-demo/page.tsx | T6, T2 | Imports component, reads sample |
| T10 app/page.tsx swap + import | T6 | Imports component |
| T11 GREEN gate: `npm test` + `npm run build` | T6–T10 | Verify GREEN + type-safe build |
| T12 S1: /markdown-demo Playwright + screenshot | T11 | Needs built/renderable app |
| T13 S3 regression: GET / + feature-flag panel | T11 | Uses T10 swap |
| T14 KB update | T12, T13 | Document final state |
| T15 Reviewer gate | T14 | Final go/no-go |

## Wave Execution

- **Wave 1** (parallel): T1, T2, T3, T4
- **Wave 2**: T5 (RED gate)
- **Wave 3** (parallel): T6, T7, T8, T9, T10
- **Wave 4**: T11 (GREEN gate: tests + build)
- **Wave 5** (parallel): T12, T13 (Playwright scenarios)
- **Wave 6**: T14 → T15 (KB → reviewer gate)

Critical path: T1 → T5 → T6 → T11 → T12 → T15.

## Tasks

### Task 1: package.json — add 7 deps + "test" script

**File:** `frontend/package.json` — replace whole file with:

```json
{
  "name": "fast-minio-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "tsx --test lib/user-id.test.ts components/markdown-content.test.tsx"
  },
  "dependencies": {
    "highlight.js": "^11.11.1",
    "katex": "^0.18.1",
    "next": "^15.5.14",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "react-markdown": "^10.1.0",
    "rehype-highlight": "^7.0.2",
    "rehype-katex": "^7.0.1",
    "remark-gfm": "^4.0.1",
    "remark-math": "^6.0.0"
  },
  "devDependencies": {
    "@types/node": "20.14.9",
    "@types/react": "18.2.79",
    "@types/react-dom": "18.2.25",
    "tsx": "^4.16.0",
    "typescript": "5.5.4"
  }
}
```

Then `npm install`. **Verify:** `npm ls react-markdown remark-math rehype-katex rehype-highlight katex highlight.js` resolves, no peer error on react 18.2.

### Task 2: app/markdown-demo/sample.md (verbatim acceptance doc)

**File:** `frontend/app/markdown-demo/sample.md` — write byte-for-byte the "驗收用測試文件" from the spec (the full markdown document with 9 `$$` blocks, 9 inline `$...$`, ```ts fence, blockquote). Source of truth: spec section "驗收用測試文件（sample.md 原文）".

**Verify:** file contains `const area`, 9 `$$`-opening lines, `\boxed{\nabla\cdot\vec{E}`.

### Task 3: components/markdown-content.tsx — RED stub

**File:** `frontend/components/markdown-content.tsx`:

```tsx
"use client";

import ReactMarkdown from "react-markdown";

export const MarkdownContent = ({ content }: { content: string }) => (
  <div className="markdown-body">
    <ReactMarkdown>{content}</ReactMarkdown>
  </div>
);
```

### Task 4: components/markdown-content.test.tsx — RED tests

**File:** `frontend/components/markdown-content.test.tsx`:

```tsx
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { MarkdownContent } from "./markdown-content";

const render = (content: string): string =>
  renderToStaticMarkup(createElement(MarkdownContent, { content }));

describe("MarkdownContent", () => {
  it("renders inline math with the katex class", () => {
    assert.match(render("$E = mc^2$"), /class="katex"/);
  });

  it("renders block math with katex-display", () => {
    const md = "$$\n\\int_0^1 x^2\\,dx=\\frac13\n$$";
    assert.match(render(md), /katex-display/);
  });

  it("renders GFM strikethrough as <del>", () => {
    assert.match(render("~~struck~~"), /<del>/);
  });

  it("highlights a ts code fence with hljs", () => {
    const md = "```ts\nconst area = (r: number) => Math.PI * r ** 2;\n```";
    assert.match(render(md), /hljs/);
  });

  it("renders invalid TeX as katex-error without crashing", () => {
    assert.doesNotThrow(() => render("$\\frac$"));
    assert.match(render("$\\frac$"), /katex-error/);
  });

  it("renders the acceptance sample.md with expected feature counts", () => {
    const sample = readFileSync(
      join(process.cwd(), "app/markdown-demo/sample.md"),
      "utf-8"
    );
    const html = render(sample);
    const displayCount = (html.match(/katex-display/g) ?? []).length;
    const katexCount = (html.match(/class="katex"/g) ?? []).length;
    assert.equal(displayCount, 9, "expected exactly 9 katex-display blocks");
    assert.equal(katexCount, 18, 'expected exactly 18 class="katex" spans');
    assert.match(html, /hljs/);
    assert.match(html, /<blockquote/);
    assert.match(html, /const area/);
  });
});
```

### Task 5: RED gate

`cd frontend && npm test 2>&1 | tee /tmp/red.txt` — expect exit ≠ 0, assertion failures on katex/hljs/`<del>`/sample-counts, ZERO `Cannot find module`/`ERR_MODULE_NOT_FOUND`, user-id tests PASS.

### Task 6: components/markdown-content.tsx — GREEN full impl

**File:** `frontend/components/markdown-content.tsx` — overwrite with:

```tsx
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
```

### Task 7: app/layout.tsx — CSS imports

Replace lines 1–3 of `frontend/app/layout.tsx` with:

```tsx
import "./globals.css";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";
import type { Metadata } from "next";
```

### Task 8: app/globals.css — append .markdown-body block

Append at end of `frontend/app/globals.css`:

```css

/* ── Markdown + KaTeX rendering (.markdown-body) ── */
.markdown-body {
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
}
.markdown-body > *:first-child { margin-top: 0; }
.markdown-body > *:last-child { margin-bottom: 0; }

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin: 1.2em 0 0.5em;
  font-weight: 600;
  line-height: 1.25;
}
.markdown-body h1 { font-size: 1.7em; }
.markdown-body h2 { font-size: 1.4em; }
.markdown-body h3 { font-size: 1.2em; }

.markdown-body p { margin: 0.6em 0; }

.markdown-body ul,
.markdown-body ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}
.markdown-body li { margin: 0.25em 0; }

.markdown-body blockquote {
  margin: 0.8em 0;
  padding: 0.4em 1em;
  border-left: 3px solid var(--accent-2);
  background: rgba(247, 183, 49, 0.08);
  color: var(--muted);
  border-radius: 0 8px 8px 0;
}
.markdown-body blockquote p { margin: 0.3em 0; }

.markdown-body hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1.2em 0;
}

.markdown-body code {
  font-family: "SFMono-Regular", "Consolas", "Liberation Mono", monospace;
  font-size: 0.9em;
  padding: 0.15em 0.4em;
  border-radius: 4px;
  background: #0e1118;
  border: 1px solid var(--border);
}
.markdown-body pre {
  margin: 0.8em 0;
  padding: 12px 14px;
  border-radius: 10px;
  background: #0e1118;
  border: 1px solid var(--border);
  overflow-x: auto;
}
.markdown-body pre code {
  padding: 0;
  background: none;
  border: none;
  font-size: 0.88em;
  line-height: 1.5;
}

.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8em 0;
  display: block;
  overflow-x: auto;
}
.markdown-body th,
.markdown-body td {
  border: 1px solid var(--border);
  padding: 6px 12px;
  text-align: left;
}
.markdown-body th { background: var(--panel-2); font-weight: 600; }

.markdown-body a { color: var(--accent); text-decoration: underline; }
.markdown-body img { max-width: 100%; }
.markdown-body del { color: var(--muted); }

.markdown-body .katex-display {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 4px 0;
  margin: 0.8em 0;
}
```

### Task 9: app/markdown-demo/page.tsx — server demo page

**File:** `frontend/app/markdown-demo/page.tsx`:

```tsx
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { MarkdownContent } from "../../components/markdown-content";

const sample = readFileSync(
  join(process.cwd(), "app/markdown-demo/sample.md"),
  "utf-8"
);

export default function MarkdownDemoPage() {
  return (
    <div className="container">
      <MarkdownContent content={sample} />
    </div>
  );
}
```

### Task 10: app/page.tsx — swap + import

- Add after line 7 (`import { resolveUserId } from "../lib/user-id";`): `import { MarkdownContent } from "../components/markdown-content";`
- Replace line 418 `<div>{msg.content}</div>` with `<MarkdownContent content={msg.content} />`.

### Task 11: GREEN gate

- `cd frontend && npm test 2>&1 | tee /tmp/green.txt` → exit 0, 15 pass (9 user-id + 6 MarkdownContent), 0 fail.
- `cd frontend && npm run build 2>&1 | tee /tmp/build.txt` → exit 0, `/markdown-demo` listed as Static.

### Task 12: S1 — Playwright /markdown-demo

Dev server → `page.goto("http://localhost:3000/markdown-demo")` → assert `.katex-display` count === 9, `.katex` count === 18, `code.hljs` ≥ 1 → `page.screenshot({ path: "/tmp/markdown-demo.png", fullPage: true })` → 0 pageerrors.

### Task 13: S3 — regression on /

`NEXT_PUBLIC_FEATURE_FLAG_ADMIN=true npm run dev` → `page.goto("http://localhost:3000")` → status 200, 0 console errors / 0 pageerrors, FeatureFlagAdminPanel DOM present.

### Task 14: KB update

Read `frontend/ai/decisions.md` + `handoff/latest.md` → append decision entry (CSS-in-layout rationale: node:test/tsx can't load CSS; `components/` outside `app/` global-CSS boundary) → create `frontend/ai/currentTask.md` → update `handoff/latest.md`. Match existing Chinese/English mixed style.

### Task 15: Reviewer gate

Verify S1–S4 with captured artifacts (`/tmp/red.txt`, `/tmp/green.txt`, `/tmp/build.txt`, `/tmp/markdown-demo.png`); grep diff for `as any`/`@ts-ignore`/`@ts-expect-error` (expect none); verify sample.md byte-identical to spec; emit PASS/FAIL verdict. NO commits.

## Success Criteria

- `npm test` GREEN: 15 passing, 0 failing; RED at `/tmp/red.txt`, GREEN at `/tmp/green.txt`.
- `npm run build` exit 0; `/markdown-demo` prerendered.
- S1: counts 9 / 18 / ≥1 hljs; screenshot exists.
- S2: invalid TeX → `katex-error`, no throw.
- S3: GET / 200, 0 console errors, feature-flag panel renders.
- S4: user-id tests still pass under new script.
- KB files updated; zero type suppression; no commits.

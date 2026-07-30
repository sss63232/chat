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
    const text = html.replace(/<[^>]+>/g, "");
    assert.match(text, /const area/);
  });
});

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, it } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
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

  // ── Currency vs. math disambiguation (financial / academic paper style) ──

  it("does not treat currency amounts $100 + $100 = $200 as math", () => {
    const html = render("$100 + $100 = $200");
    assert.doesNotMatch(html, /class="katex"/);
    assert.match(html, /\$100/);
  });

  it("preserves digit-leading inline math $2^{10} = 1024$", () => {
    assert.match(render("$2^{10} = 1024$"), /class="katex"/);
  });

  it("preserves digit-leading inline math with LaTeX command", () => {
    assert.match(render(`$3 \\times 4 = 12$`), /class="katex"/);
  });

  it("renders Black-Scholes d1 formula", () => {
    const md = `$d_1 = \\frac{\\ln(S/K) + (r + \\sigma^2/2)T}{\\sigma\\sqrt{T}}$`;
    assert.match(render(md), /class="katex"/);
  });

  it("renders Black-Scholes call price formula", () => {
    const md = `$C = S_0 N(d_1) - Ke^{-rT}N(d_2)$`;
    assert.match(render(md), /class="katex"/);
  });

  it("renders CAPM formula", () => {
    const md = `$E(R_i) = r_f + \\beta_i [E(R_m) - r_f]$`;
    assert.match(render(md), /class="katex"/);
  });

  it("renders present value summation formula", () => {
    const md = `$PV = \\sum_{t=1}^{n} \\frac{CF_t}{(1+r)^t}$`;
    assert.match(render(md), /class="katex"/);
  });

  it("renders volatility formula", () => {
    const md = `$\\sigma^2 = \\frac{1}{n-1}\\sum_{i=1}^{n}(R_i - \\bar{R})^2$`;
    assert.match(render(md), /class="katex"/);
  });

  it("renders CRRA utility formula", () => {
    const md = `$U(x) = \\frac{x^{1-\\gamma}}{1-\\gamma}$`;
    assert.match(render(md), /class="katex"/);
  });

  it("renders Black-Scholes block math", () => {
    const md = `$$\nC = S_0 N(d_1) - Ke^{-rT}N(d_2)\n$$`;
    assert.match(render(md), /katex-display/);
  });

  it("does not treat bond price currency as math", () => {
    const html = render("The bond trades at $1,050 with face value $1,000.");
    assert.doesNotMatch(html, /class="katex"/);
    assert.match(html, /\$1,050/);
    assert.match(html, /\$1,000/);
  });

  it("does not treat GDP currency as math", () => {
    const html = render("GDP grew from $1.2 trillion to $1.5 trillion.");
    assert.doesNotMatch(html, /class="katex"/);
    assert.match(html, /\$1\.2 trillion/);
    assert.match(html, /\$1\.5 trillion/);
  });

  it("renders mixed currency and option payoff math", () => {
    const html = render(
      "The premium is $5.25 for an option with payoff $max(S_T - K, 0)$."
    );
    assert.match(html, /class="katex"/);
    assert.match(html, /\$5\.25/);
  });

  it("renders economics budget constraint with multiple inline math spans", () => {
    const html = render(
      "Given $p_1 = 10$ and $p_2 = 20$, the budget is $p_1 x_1 + p_2 x_2 = m$."
    );
    assert.match(html, /class="katex"/);
  });

  it("does not escape currency inside code spans", () => {
    const html = render("`price=$100`");
    assert.match(html, /\$100/);
    assert.doesNotMatch(html, /\\\$100/);
  });
});

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

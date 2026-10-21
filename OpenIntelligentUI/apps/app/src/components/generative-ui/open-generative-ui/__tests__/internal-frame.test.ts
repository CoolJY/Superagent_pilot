import { expect, it, vi } from "vitest";
vi.mock("@/lib/deployment", () => ({ AIR_GAP_MODE: true }));
import { buildFinalFrameContent, buildPreviewHeadContent } from "../frame-content";
it("blocks network resources in both preview and final frames and omits CDN imports", () => {
  const final = buildFinalFrameContent('<body><div>Local UI</div></body>');
  const preview = buildPreviewHeadContent();
  for (const content of [final, preview]) {
    expect(content).toContain("connect-src 'none'");
    expect(content).toContain("default-src 'none'");
    expect(content).not.toContain('https://esm.sh');
    expect(content).not.toContain('type="importmap"');
  }
});

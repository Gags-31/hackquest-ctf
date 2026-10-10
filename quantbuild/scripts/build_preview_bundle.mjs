/**
 * Builds the QuantBuild live-preview bundle.
 *
 * All generated frontends share the same component code (backend/app/templates/frontend),
 * so ONE bundle serves every project's live preview — the per-project entity
 * configuration and API base are injected by the server at page-render time.
 *
 *   node scripts/build_preview_bundle.mjs
 *
 * Outputs: backend/app/static/preview/bundle.js  (+ preview.css via tailwind CLI)
 */
import { build } from "../frontend/node_modules/esbuild/lib/main.js";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TEMPLATES = path.join(ROOT, "backend", "app", "templates");
const NODE_MODULES = path.join(ROOT, "frontend", "node_modules");
const OUT_DIR = path.join(ROOT, "backend", "app", "static", "preview");

// Redirect generated-config imports to the runtime shim.
const configShimPlugin = {
  name: "config-shim",
  setup(buildApi) {
    buildApi.onResolve({ filter: /(^|\/)(entityConfig|appInfo)$/ }, () => ({
      path: path.join(TEMPLATES, "preview", "runtimeShim.ts"),
    }));
  },
};

await build({
  entryPoints: [path.join(TEMPLATES, "preview", "main_preview.tsx")],
  bundle: true,
  outfile: path.join(OUT_DIR, "bundle.js"),
  format: "iife",
  jsx: "automatic",
  minify: true,
  target: ["es2020"],
  nodePaths: [NODE_MODULES],
  plugins: [configShimPlugin],
  define: { "process.env.NODE_ENV": '"production"' },
  logLevel: "info",
});

// Tailwind CSS for the preview (same theme as generated apps).
const tailwindCli = path.join(NODE_MODULES, "tailwindcss", "lib", "cli.js");
execFileSync(process.execPath, [
  tailwindCli,
  "-c", path.join(TEMPLATES, "preview", "tailwind.preview.config.js"),
  "-i", path.join(TEMPLATES, "frontend", "src", "index.css"),
  "-o", path.join(OUT_DIR, "preview.css"),
  "--minify",
], { cwd: path.join(TEMPLATES, "preview"), stdio: "inherit" });

console.log("✔ preview bundle written to", OUT_DIR);

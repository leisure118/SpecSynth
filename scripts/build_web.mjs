import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const outdir = path.join(repoRoot, "apps", "web", "dist");
const entryFile = path.join(repoRoot, "apps", "web", "src", "main.js");

let esbuild;
try {
  ({ default: esbuild } = await import("esbuild"));
} catch (error) {
  if (error?.code === "ERR_MODULE_NOT_FOUND") {
    console.error("Missing dependency 'esbuild'. Run 'npm install' in the repository root and retry.");
    process.exit(1);
  }
  throw error;
}

await mkdir(outdir, { recursive: true });

await esbuild.build({
  entryPoints: [entryFile],
  outdir,
  bundle: true,
  external: ["/fonts/*"],
  format: "esm",
  splitting: false,
  sourcemap: process.env.ACSL_WEB_DEBUG === "1",
  minify: process.env.ACSL_WEB_DEBUG !== "1",
  target: ["es2022"],
  loader: {
    ".css": "css",
  },
  alias: {
    vue: "vue/dist/vue.esm-browser.prod.js",
  },
  define: {
    __VUE_OPTIONS_API__: "true",
    __VUE_PROD_DEVTOOLS__: "false",
  },
  logLevel: "info",
});

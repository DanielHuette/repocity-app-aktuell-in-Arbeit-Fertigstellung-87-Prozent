import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://speedofthespirit.dev",
  output: "static",
  build: { format: "directory" },
});
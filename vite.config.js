import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  // Expose GREETING_* (and VITE_*) vars to the SPA at build time.
  envPrefix: ["GREETING_", "VITE_"],
});

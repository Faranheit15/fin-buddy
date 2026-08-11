import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Bklit is registry-vended source. Validate it with TypeScript/build; do not
    // apply project-authored React Compiler lint rules to its generated internals.
    "src/components/charts/**",
    "src/components/shimmering-text.tsx",
  ]),
]);

export default eslintConfig;

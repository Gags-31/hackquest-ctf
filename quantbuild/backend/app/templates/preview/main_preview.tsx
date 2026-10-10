/**
 * QuantBuild live-preview entry point.
 *
 * Identical to the generated app's src/main.tsx except it uses a HashRouter
 * (so refreshes work when served from the QuantBuild server) and resolves
 * entityConfig / appInfo from the injected runtime configuration instead of
 * the generated static modules (see the esbuild shim plugin in
 * scripts/build_preview_bundle.mjs).
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "../frontend/src/App";
import { AuthProvider } from "../frontend/src/auth/AuthContext";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <HashRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </HashRouter>
  </React.StrictMode>
);

import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./styles.css";
import { ModelRunsView } from "./views/ModelRunsView";

function AppWithMlDashboard() {
  if (window.location.pathname === "/model-runs") {
    return <ModelRunsView />;
  }

  return (
    <>
      <a
        href="/model-runs"
        style={{
          position: "fixed",
          right: 24,
          bottom: 24,
          zIndex: 1000,
          minHeight: 40,
          display: "inline-flex",
          alignItems: "center",
          padding: "0 16px",
          border: "1px solid var(--primary)",
          borderRadius: 999,
          background: "var(--primary)",
          color: "#fff",
          fontSize: 13,
          fontWeight: 800,
          textDecoration: "none",
          boxShadow: "0 10px 26px rgba(17, 63, 103, 0.25)",
        }}
      >
        Pruebas ML
      </a>
      <App />
    </>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppWithMlDashboard />
  </React.StrictMode>,
);

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
      <a className="model-runs-floating-link" href="/model-runs">
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

import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./App.jsx";
import "./index.css";

// HashRouter (not BrowserRouter): GitHub Pages serves static files only
// and will 404 on deep links like /documind/chat. Hash-based routing
// keeps the URL fragment client-side so every route works on refresh.
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>
);

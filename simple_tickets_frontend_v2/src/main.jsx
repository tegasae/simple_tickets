import { createRoot } from "react-dom/client";
import App from "./app/App.jsx";
import { createApi } from "./api/transport.js";
import { createSession } from "./app/session/session.js";
import { t } from "./shared/i18n/messages.js";
import "./shared/styles/base.css";

let storage;
try {
  storage = window.sessionStorage;
} catch {
  // A browser with storage disabled can still use the current page.
}

const session = createSession({ api: createApi(), storage });
document.title = t("app.name");
createRoot(document.getElementById("root")).render(<App session={session} />);

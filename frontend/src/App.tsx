import { useEffect } from "react";
import { Spinner } from "./components/Badges";
import { Layout, PageState } from "./components/Layout";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { CoveragePage } from "./pages/CoveragePage";
import { CasePage } from "./pages/CasePage";
import { LoginPage } from "./pages/LoginPage";
import { NewCasePage } from "./pages/NewCasePage";
import { QueuePage } from "./pages/QueuePage";
import { ReportPage } from "./pages/ReportPage";
import { navigate, useRoute } from "./lib/router";
import { useSession } from "./lib/session";

export function App() {
  const route = useRoute();
  const { user, ready } = useSession();

  useEffect(() => {
    if (ready && !user && route.name !== "login") navigate("/login");
    if (ready && user && route.name === "login") navigate("/cases");
  }, [ready, user, route.name]);

  if (!ready) return <div className="center full"><Spinner /></div>;
  if (!user) return <LoginPage />;

  switch (route.name) {
    case "queue": return <QueuePage />;
    case "analytics": return <AnalyticsPage />;
    case "coverage": return <CoveragePage />;
    case "new": return <NewCasePage />;
    case "case": return <CasePage key={route.id} id={route.id} />;
    case "report": return <ReportPage id={route.id} />;
    case "login": return null;
    default: return <Layout><PageState title="Page not found" action={<a className="btn" href="#/cases">Go to the queue</a>}>That address does not match any page.</PageState></Layout>;
  }
}

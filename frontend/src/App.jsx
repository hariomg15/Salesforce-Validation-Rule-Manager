import { useEffect, useState } from "react";

const apiBaseUrl = "http://localhost:8000";

async function readJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || "Request failed");
  }
  return data;
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("app_token") || "");
  const [sessionInfo, setSessionInfo] = useState(null);
  const [rulesResponse, setRulesResponse] = useState(null);
  const [pendingChanges, setPendingChanges] = useState({});
  const [status, setStatus] = useState("Ready to connect and review validation rules.");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get("token");

    if (urlToken) {
      localStorage.setItem("app_token", urlToken);
      setToken(urlToken);
      params.delete("token");
      params.delete("session_id");
      const nextSearch = params.toString();
      const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ""}`;
      window.history.replaceState({}, "", nextUrl);
      setStatus("Salesforce session connected successfully.");
    }
  }, []);

  useEffect(() => {
    if (!token) {
      setSessionInfo(null);
      setRulesResponse(null);
      setPendingChanges({});
      return;
    }

    const loadSession = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        const data = await readJson(response);
        setSessionInfo(data);
      } catch (error) {
        localStorage.removeItem("app_token");
        setToken("");
        setStatus(error.message);
      }
    };

    loadSession();
  }, [token]);

  const displayedRules = (rulesResponse?.items || []).map((rule) => ({
    ...rule,
    active: pendingChanges[rule.id] !== undefined ? pendingChanges[rule.id] : rule.active
  }));

  const pendingCount = Object.entries(pendingChanges).filter(([ruleId, nextValue]) => {
    const originalRule = rulesResponse?.items?.find((item) => item.id === ruleId);
    return originalRule && originalRule.active !== nextValue;
  }).length;

  const handleSalesforceLogin = () => {
    window.location.href = `${apiBaseUrl}/api/auth/salesforce/login`;
  };

  const handleDevLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/dev-login`, {
        method: "POST"
      });
      const data = await readJson(response);
      localStorage.setItem("app_token", data.access_token);
      setToken(data.access_token);
      setStatus("Local session started successfully.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFetchRules = async () => {
    if (!token) {
      setStatus("Please log in first.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/validation-rules`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      const data = await readJson(response);
      setRulesResponse(data);
      setPendingChanges({});
      setStatus("Validation rules loaded.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRule = (ruleId, nextValue) => {
    setPendingChanges((current) => ({
      ...current,
      [ruleId]: nextValue
    }));
  };

  const handleSetAll = (nextValue) => {
    const nextChanges = {};
    for (const rule of rulesResponse?.items || []) {
      nextChanges[rule.id] = nextValue;
    }
    setPendingChanges(nextChanges);
  };

  const handleDeploy = async () => {
    if (!token || !rulesResponse?.items?.length) {
      setStatus("Fetch validation rules before deploying.");
      return;
    }

    const changedItems = rulesResponse.items
      .filter((rule) => pendingChanges[rule.id] !== undefined && pendingChanges[rule.id] !== rule.active)
      .map((rule) => ({
        id: rule.id,
        rule_name: rule.rule_name,
        active: pendingChanges[rule.id]
      }));

    if (!changedItems.length) {
      setStatus("No pending changes to deploy.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/validation-rules/deploy`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ changes: changedItems })
      });
      const data = await readJson(response);
      setStatus(`Changes deployed. Updated ${data.updated_count} validation rules.`);
      await handleFetchRules();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("app_token");
    setToken("");
    setSessionInfo(null);
    setRulesResponse(null);
    setPendingChanges({});
    setStatus("Session cleared.");
  };

  return (
    <main className="page">
      <section className="card">
        <div className="hero">
          <div className="hero-copy">
            <p className="eyebrow">Account Object Controls</p>
            <h1>Salesforce Validation Rule Manager</h1>
            <p className="lead">
              Review active rules, make quick status changes, and deploy updates
              from one place.
            </p>
            <div className="hero-summary">
              <div>
                <span className="summary-label">Session</span>
                <strong>{sessionInfo ? "Connected" : "Not Connected"}</strong>
              </div>
              <div>
                <span className="summary-label">Rules Loaded</span>
                <strong>{displayedRules.length}</strong>
              </div>
              <div>
                <span className="summary-label">Pending</span>
                <strong>{pendingCount}</strong>
              </div>
            </div>
          </div>

          <div className="actions">
            <button className="primary" onClick={handleSalesforceLogin} disabled={loading}>
              Connect Salesforce
            </button>
            <button className="secondary" onClick={handleDevLogin} disabled={loading}>
              Use Local Session
            </button>
            <button className="ghost" onClick={handleFetchRules} disabled={loading || !token}>
              Load Validation Rules
            </button>
            <button className="primary" onClick={handleDeploy} disabled={loading || !token}>
              Deploy Updates
            </button>
            <button className="ghost" onClick={handleLogout}>
              Clear Session
            </button>
          </div>
        </div>

        <p className="status">{status}</p>

        <div className="panel-grid">
          <section className="panel">
            <div className="panel-heading">
              <h2>Current Session</h2>
              <span className={`session-badge ${sessionInfo ? "session-live" : "session-idle"}`}>
                {sessionInfo ? "Active" : "Idle"}
              </span>
            </div>
            {sessionInfo ? (
              <dl className="detail-list">
                <div>
                  <dt>Session ID</dt>
                  <dd>{sessionInfo.session_id}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{sessionInfo.status}</dd>
                </div>
                <div>
                  <dt>Salesforce User</dt>
                  <dd>{sessionInfo.salesforce_user_id || "Pending OAuth profile fetch"}</dd>
                </div>
                <div>
                  <dt>Org Id</dt>
                  <dd>{sessionInfo.salesforce_org_id || "Pending OAuth org fetch"}</dd>
                </div>
                <div>
                  <dt>Instance URL</dt>
                  <dd>{sessionInfo.salesforce_instance_url || "Not available yet"}</dd>
                </div>
              </dl>
            ) : (
              <p className="empty">Connect Salesforce or use a local session to continue.</p>
            )}
          </section>

          <section className="panel">
            <div className="panel-heading">
              <h2>Validation Rules</h2>
              <span className="rules-count">{displayedRules.length} items</span>
            </div>
            {displayedRules.length ? (
              <>
                <div className="toolbar">
                  <span>{displayedRules.length} rules loaded</span>
                  <span>{pendingCount} pending updates</span>
                </div>

                <div className="bulk-actions">
                  <button className="ghost" onClick={() => handleSetAll(true)}>
                    Enable All
                  </button>
                  <button className="ghost" onClick={() => handleSetAll(false)}>
                    Disable All
                  </button>
                </div>

                <div className="rules">
                  {displayedRules.map((rule) => (
                    <article className="rule-row" key={rule.id}>
                      <div>
                        <strong>{rule.rule_name}</strong>
                        <p>{rule.object_name}</p>
                      </div>
                      <label className={`toggle ${rule.active ? "toggle-on" : "toggle-off"}`}>
                        <input
                          type="checkbox"
                          checked={rule.active}
                          onChange={(event) => handleToggleRule(rule.id, event.target.checked)}
                        />
                        <span>{rule.active ? "Active" : "Inactive"}</span>
                      </label>
                    </article>
                  ))}
                </div>
              </>
            ) : (
              <p className="empty">
                Load validation rules after login to review and update their status.
              </p>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}

import {useEffect, useState} from "react";

type Prediction = {
  home_team: string; away_team: string; predicted_outcome: string;
  probabilities: {home_win: number; draw: number; away_win: number};
  explanation: string; statistics: string[]; model_version: string; data_origin: string; data_as_of: string;
};
type Analysis = {status: string; message: string; agent_commentary: string; predictions: Prediction[];
  tool_calls: string[]; request_id: string; input_tokens: number; output_tokens: number};
type Health = {agent_enabled: boolean; gemini_model: string; data_origin: string};

function Card({p}: {p: Prediction}) {
  const rows: [string, number, string][] = [[p.home_team, p.probabilities.home_win, "home"],
    ["Draw", p.probabilities.draw, "draw"], [p.away_team, p.probabilities.away_win, "away"]];
  return <article className="card prediction">
    <div className="card-top"><span className="eyebrow">Classifier result</span><span className="badge">{p.data_origin}</span></div>
    <h2>{p.home_team} <span className="muted">vs</span> {p.away_team}</h2>
    <p className="leader">Leading outcome · <strong>{p.predicted_outcome}</strong></p>
    {rows.map(([label, value, cls]) => <div className="probability" key={cls}>
      <div><span>{label}</span><strong>{(value * 100).toFixed(1)}%</strong></div>
      <div className="track"><div className={`fill ${cls}`} style={{width: `${value*100}%`}} /></div>
    </div>)}
    <p className="explanation">{p.explanation}</p>
    <ul>{p.statistics.map(s => <li key={s}>{s}</li>)}</ul>
    <footer><span>Snapshot: {p.data_as_of}</span><span>{p.model_version}</span></footer>
  </article>;
}

export default function App() {
  const [message, setMessage] = useState("Predict Arsenal at home against Liverpool. Explain the limitations.");
  const [mode, setMode] = useState<"agent"|"direct">("agent");
  const [teams, setTeams] = useState<string[]>([]);
  const [health, setHealth] = useState<Health|null>(null);
  const [home, setHome] = useState("Arsenal"), [away, setAway] = useState("Liverpool");
  const [analysis, setAnalysis] = useState<Analysis|null>(null);
  const [cards, setCards] = useState<Prediction[]>([]);
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  useEffect(() => {
    Promise.all([fetch("/api/teams").then(r => {if(!r.ok) throw Error(); return r.json();}),
      fetch("/health").then(r => {if(!r.ok) throw Error(); return r.json();})])
      .then(([t, h]) => {setTeams(t.teams); setHealth(h);})
      .catch(() => setError("Cannot reach the API. Start the backend and train the model first."));
  }, []);
  async function run() {
    setBusy(true); setError(""); setCards([]); setAnalysis(null);
    try {
      const response = await fetch(mode === "agent" ? "/api/analyse" : "/api/predict", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(mode === "agent" ? {message} : {home_team: home, away_team: away}),
        signal: AbortSignal.timeout(70000),
      });
      const data = await response.json();
      if (!response.ok) throw Error(typeof data.detail === "string" ? data.detail : "Check the request fields.");
      if (mode === "agent") {setAnalysis(data); setCards(data.predictions);} else setCards([data]);
    } catch (err) {setError(err instanceof Error ? err.message : "Request failed");}
    finally {setBusy(false);}
  }
  return <main>
    <nav><div className="brand">◉ MatchMind <em>AI</em></div><span className="badge">{health ? "API connected" : "Connecting…"}</span></nav>
    <header><p className="eyebrow">Football · agents · machine learning</p><h1>Ask the agent.<br/><span>Inspect the prediction.</span></h1>
      <p>An ADK analyst calls a trained model to estimate match outcomes. Explore the probabilities and the evidence behind the request.</p></header>
    <div className="notice">Educational demo · Historical snapshot: {health?.data_origin || "loading"} · No live fixtures or team news</div>
    <section className="workspace">
      <div className="card controls">
        <div className="tabs"><button className={mode === "agent" ? "active" : ""} onClick={() => setMode("agent")} disabled={busy}>ADK agent</button><button className={mode === "direct" ? "active" : ""} onClick={() => setMode("direct")} disabled={busy}>Direct model</button></div>
        {mode === "agent" ? <>
          <label htmlFor="message">Your football question</label>
          <textarea id="message" maxLength={800} value={message} onChange={e => setMessage(e.target.value)} disabled={busy}/>
          <small>One request at a time. Include both teams and the home side.</small>
          {!health?.agent_enabled && <p className="warning">Agent is disabled. Configure Vertex AI, or try Direct model.</p>}
          <div className="examples"><button disabled={busy} onClick={() => setMessage("Predict Arsenal at home against Liverpool. Explain the limitations.")}>Arsenal vs Liverpool</button><button disabled={busy} onClick={() => setMessage("Compare Arsenal at home against Liverpool and Man City at home against Chelsea.")}>Compare two matches</button><button disabled={busy} onClick={() => setMessage("Predict United against City.")}>Try an ambiguous request</button></div>
        </> : <><label htmlFor="home">Home team</label><select id="home" value={home} onChange={e => setHome(e.target.value)}>{teams.map(t => <option key={t}>{t}</option>)}</select><label htmlFor="away">Away team</label><select id="away" value={away} onChange={e => setAway(e.target.value)}>{teams.map(t => <option key={t}>{t}</option>)}</select></>}
        <button className="run" onClick={run} disabled={busy || !health || (mode === "agent" ? !health.agent_enabled || message.trim().length < 5 : home === away)}>{busy ? "Working…" : mode === "agent" ? "Ask the ADK agent →" : "Run the classifier →"}</button>
        <p className="small muted">Probabilities are estimates, not guarantees. Synthetic-data scores do not establish real-world accuracy.</p>
      </div>
      <div className="results" aria-live="polite">
        {error && <div role="alert" className="card warning">{error}</div>}
        {busy && <div className="card empty"><span className="pulse">◉</span><h2>{mode === "agent" ? "Agent is working" : "Running inference"}</h2><p>{mode === "agent" ? "Interpreting the question and calling approved tools…" : "Calculating outcome probabilities…"}</p></div>}
        {!busy && !error && cards.length === 0 && !analysis && <div className="card empty"><span className="pulse">◉</span><h2>A fixture, three possibilities.</h2><p>Start with a question or select two teams.</p></div>}
        {analysis && <div className="card activity"><p className="eyebrow">Observed tool activity</p><p>{analysis.tool_calls.join(" → ") || "No tools called"}</p><small>{analysis.message}</small></div>}
        {cards.map((p, i) => <Card key={`${p.home_team}-${p.away_team}-${i}`} p={p}/>)}
        {analysis?.agent_commentary && <div className="card commentary"><p className="eyebrow">Gemini commentary</p><p className="agent-text">{analysis.agent_commentary}</p><small>Generated commentary can be mistaken. The classifier cards are the authoritative numerical output.</small></div>}
        {analysis && <details className="card"><summary>Inspect request telemetry</summary><pre>{JSON.stringify({request_id: analysis.request_id, status: analysis.status, model: health?.gemini_model, input_tokens: analysis.input_tokens, output_tokens: analysis.output_tokens}, null, 2)}</pre></details>}
      </div>
    </section>
  </main>;
}

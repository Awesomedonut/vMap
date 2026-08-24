import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, GenerateParams, JobStatus, WorldManifest } from "../api";

const PRESETS = ["continents", "pangaea", "archipelago"];

export default function Home() {
  const [worlds, setWorlds] = useState<WorldManifest[]>([]);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<GenerateParams>({
    preset: "continents",
    grid_n: 96,
    ocean_fraction: 0.62,
    world_km: 3000,
  });
  const [seedText, setSeedText] = useState("");
  const pollRef = useRef<number>();

  const refresh = () => api.listWorlds().then(setWorlds).catch((e) => setError(String(e)));
  useEffect(() => {
    refresh();
    return () => window.clearInterval(pollRef.current);
  }, []);

  const generating = job?.status === "running";

  async function onGenerate() {
    setError(null);
    try {
      const seed = seedText.trim() === "" ? undefined : Number(seedText.trim());
      const started = await api.generate({ ...params, seed });
      setJob(started);
      pollRef.current = window.setInterval(async () => {
        const s = await api.jobStatus(started.id);
        setJob(s);
        if (s.status !== "running") {
          window.clearInterval(pollRef.current);
          if (s.status === "done") refresh();
          if (s.status === "error") setError(s.error ?? "generation failed");
        }
      }, 400);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="home">
      <h1>vMap</h1>
      <p className="tagline">
        Google Maps for fictional worlds — generate a world model and explore it like a real place.
      </p>

      <div className="gen-panel">
        <label>
          Preset
          <select
            value={params.preset}
            onChange={(e) => setParams({ ...params, preset: e.target.value })}
          >
            {PRESETS.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </label>
        <label>
          Seed (blank = random)
          <input
            value={seedText}
            onChange={(e) => setSeedText(e.target.value)}
            placeholder="e.g. 12345"
            inputMode="numeric"
          />
        </label>
        <label>
          Ocean {Math.round(params.ocean_fraction * 100)}%
          <input
            type="range"
            min="0.2"
            max="0.85"
            step="0.01"
            value={params.ocean_fraction}
            onChange={(e) => setParams({ ...params, ocean_fraction: Number(e.target.value) })}
          />
        </label>
        <label>
          World width (km)
          <input
            type="number"
            min="200"
            max="40000"
            value={params.world_km}
            onChange={(e) => setParams({ ...params, world_km: Number(e.target.value) })}
          />
        </label>
        <button className="go" disabled={generating} onClick={onGenerate}>
          {generating ? "Generating…" : "Generate world"}
        </button>

        {job && job.status === "running" && (
          <div className="gen-progress">
            {job.stage}…
            <div className="bar">
              <div style={{ width: `${job.progress * 100}%` }} />
            </div>
          </div>
        )}
        {error && <div className="gen-error">{error}</div>}
      </div>

      <div className="world-grid">
        {worlds.map((w) => (
          <Link key={w.slug} className="world-card" to={`/w/${w.slug}`}>
            <img src={`/tiles/${w.slug}/0/0/0.png`} alt={w.name} loading="lazy" />
            <div className="meta">
              <strong>{w.name}</strong>
              <span>
                seed {w.seed} · {w.settings.preset} · {w.n_settlements} settlements
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

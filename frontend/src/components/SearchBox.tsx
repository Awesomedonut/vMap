import { useEffect, useState } from "react";
import { api } from "../api";

interface Props {
  slug: string;
  onPick: (f: GeoJSON.Feature) => void;
}

export default function SearchBox({ slug, onPick }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GeoJSON.Feature[]>([]);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    const t = window.setTimeout(
      () => api.search(slug, query).then((fc) => setResults(fc.features)),
      200
    );
    return () => window.clearTimeout(t);
  }, [query, slug]);

  function pick(f: GeoJSON.Feature): void {
    onPick(f);
    setResults([]);
    setQuery("");
  }

  return (
    <div className="searchbox">
      <input
        placeholder="Search places…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {results.length > 0 && (
        <div className="results">
          {results.map((f, i) => (
            <button key={i} onClick={() => pick(f)}>
              {(f.properties as { name: string }).name}
              <span>{(f.properties as { kind: string }).kind}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

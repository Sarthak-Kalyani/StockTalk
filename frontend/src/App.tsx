import { useState, useEffect } from "react";
import { api } from "./services/api";

function App() {
  const [health, setHealth] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.health()
      .then((data) => {
        setHealth(data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message);
        setHealth(null);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-white text-gray-800 p-6 md:p-12">
      <header className="mb-12">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">StockTalk</h1>
        <p className="mt-2 text-gray-600">
          B2B Inventory and Supplier Communication Platform
        </p>
      </header>

      <section className="max-w-2xl">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Backend connection</h2>
        <div className="rounded-lg border p-4 bg-gray-50">
          <p className="text-sm font-mono text-gray-700 mb-2">
            GET <span className="text-indigo-600">/api/v1/health</span>
          </p>
          {loading ? (
            <p className="text-sm text-gray-500 italic">Connecting…</p>
          ) : error ? (
            <p className="text-sm text-red-600">
              Unable to reach backend: {error}
            </p>
          ) : (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-sm font-medium text-green-700">Backend reachable</span>
              </span>
              <pre className="ml-4 text-xs text-gray-500 bg-white p-2 rounded border border-gray-100">
                {JSON.stringify(health, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </section>

      <footer className="mt-12 pt-6 border-t border-gray-200 text-xs text-gray-500">
        StockTalk · Group GC_2026_018 · Frontend calls FastAPI backend
      </footer>
    </div>
  );
}

export default App;

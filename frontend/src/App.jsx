import { useCallback, useEffect, useState } from "react";

import { API_BASE_URL, decrementCounter, getCounter, incrementCounter } from "./api";
import "./App.css";

export default function App() {
  const [value, setValue] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);

  const loadCounter = useCallback(async () => {
    try {
      const counter = await getCounter();
      setValue(counter.value);
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCounter();
  }, [loadCounter]);

  async function update(action) {
    setIsBusy(true);
    setError("");

    try {
      const counter = await action();
      setValue(counter.value);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsBusy(false);
    }
  }

  const actionsDisabled = isBusy || isLoading;

  return (
    <main className="page">
      <section className="card">
        <header className="card__header">
          <span className="eyebrow">Docker + CI/CD playground</span>
          <h1>Counter</h1>
          <p>FastAPI in the back, React in the front.</p>
        </header>

        <div className="counter" aria-live="polite" aria-label="Current counter value">
          {isLoading ? "…" : value}
        </div>

        <div className="actions">
          <button
            type="button"
            className="button button--secondary"
            onClick={() => update(decrementCounter)}
            disabled={actionsDisabled}
          >
            <span aria-hidden="true">−</span> Decrement
          </button>
          <button
            type="button"
            className="button button--primary"
            onClick={() => update(incrementCounter)}
            disabled={actionsDisabled}
          >
            <span aria-hidden="true">+</span> Increment
          </button>
        </div>

        {error ? (
          <p className="message message--error" role="alert">
            {error}
          </p>
        ) : (
          <p className="message">The decrement endpoint is a TODO for the lecture.</p>
        )}

        <footer className="card__footer">
          API: <code>{API_BASE_URL || "same origin (Vite proxy)"}</code>
        </footer>
      </section>
    </main>
  );
}

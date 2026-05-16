import { useState } from "react";
import "./App.css";

const DEFAULTS = {
  address: "U",
  famsize: "GT3",
  Pstatus: "T",
  Medu: 3,
  Fedu: 3,
  Mjob: "other",
  Fjob: "other",
  reason: "course",
  guardian: "mother",
  traveltime: 2,
  famsup: "yes",
  paid: "no",
  activities: "yes",
  nursery: "yes",
  higher: "yes",
  internet: "yes",
  romantic: "no",
  famrel: 4,
  freetime: 3,
  goout: 3,
  Dalc: 1,
  Walc: 1,
  health: 3,
  schoolsup: "no",
};

function App() {
  const [form, setForm] = useState({
    school: "GP",
    sex: "F",
    age: 17,
    G1: 12,
    G2: 12,
    studytime: 2,
    failures: 0,
    absences: 4,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "number" || type === "select-one" && !isNaN(value)
        ? (value === "" ? "" : Number(value))
        : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    const payload = { ...DEFAULTS, ...form };

    try {
      const res = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || `Server error (${res.status})`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Failed to connect to the prediction server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Student Performance Predictor</h1>
          <p className="subtitle">
            Predict whether a student will pass or fail based on key factors
          </p>
        </header>

        <form onSubmit={handleSubmit} className="form-card">
          <div className="form-grid">
            <div className="field">
              <label htmlFor="school">School</label>
              <select id="school" name="school" value={form.school} onChange={handleChange}>
                <option value="GP">GP — Gabriel Pereira</option>
                <option value="MS">MS — Mousinho da Silveira</option>
              </select>
            </div>

            <div className="field">
              <label htmlFor="sex">Sex</label>
              <select id="sex" name="sex" value={form.sex} onChange={handleChange}>
                <option value="F">Female</option>
                <option value="M">Male</option>
              </select>
            </div>

            <div className="field">
              <label htmlFor="age">Age</label>
              <input
                id="age" type="number" name="age"
                min={15} max={22}
                value={form.age} onChange={handleChange}
              />
              <span className="hint">15 – 22</span>
            </div>

            <div className="field">
              <label htmlFor="studytime">Study Time</label>
              <select id="studytime" name="studytime" value={form.studytime} onChange={handleChange}>
                <option value={1}>1 — &lt; 2 hours</option>
                <option value={2}>2 — 2 to 5 hours</option>
                <option value={3}>3 — 5 to 10 hours</option>
                <option value={4}>4 — &gt; 10 hours</option>
              </select>
            </div>

            <div className="field">
              <label htmlFor="failures">Past Failures</label>
              <select id="failures" name="failures" value={form.failures} onChange={handleChange}>
                <option value={0}>0</option>
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={3}>3+</option>
              </select>
            </div>

            <div className="field">
              <label htmlFor="absences">Absences</label>
              <input
                id="absences" type="number" name="absences"
                min={0} max={93}
                value={form.absences} onChange={handleChange}
              />
              <span className="hint">0 – 93</span>
            </div>

            <div className="field">
              <label htmlFor="G1">G1 (1st Period Grade)</label>
              <input
                id="G1" type="number" name="G1"
                min={0} max={20}
                value={form.G1} onChange={handleChange}
              />
              <span className="hint">0 – 20</span>
            </div>

            <div className="field">
              <label htmlFor="G2">G2 (2nd Period Grade)</label>
              <input
                id="G2" type="number" name="G2"
                min={0} max={20}
                value={form.G2} onChange={handleChange}
              />
              <span className="hint">0 – 20</span>
            </div>
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? (
              <span className="spinner-wrap">
                <span className="spinner" />
                Predicting...
              </span>
            ) : (
              "Predict"
            )}
          </button>
        </form>

        {error && (
          <div className="result-card error-card">
            <div className="result-icon">!</div>
            <h2>Error</h2>
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className={`result-card ${result.prediction === 1 ? "pass-card" : "fail-card"}`}>
            <div className="result-icon">{result.prediction === 1 ? "✓" : "✗"}</div>
            <h2 className="result-label">{result.label}</h2>
            <p className="result-prob">
              {(result.probability * 100).toFixed(1)}% probability of passing
            </p>
            <div className="prob-bar-track">
              <div
                className="prob-bar-fill"
                style={{ width: `${(result.probability * 100).toFixed(1)}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

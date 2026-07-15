import { useState } from 'react';
import { uploadDocument } from '../api/client';

const STRATEGIES = [
  { value: 'sentence', label: 'Sentence (5 sentences/chunk)' },
  { value: 'fixed', label: 'Fixed (500 chars, 50 overlap)' },
];

export default function UploadPanel() {
  const [file, setFile] = useState(null);
  const [strategy, setStrategy] = useState('sentence');
  const [status, setStatus] = useState('idle'); // idle | uploading | done | error
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;

    setStatus('uploading');
    setProgress(0);
    setError(null);
    setResult(null);

    try {
      const data = await uploadDocument(file, strategy, setProgress);
      setResult(data);
      setStatus('done');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Document Ingestion</h2>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        <label className="file-drop">
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          {file ? file.name : 'Choose a PDF or TXT file'}
        </label>

        <div className="strategy-row">
          {STRATEGIES.map((s) => (
            <label key={s.value} className={`strategy-option ${strategy === s.value ? 'active' : ''}`}>
              <input
                type="radio"
                name="strategy"
                value={s.value}
                checked={strategy === s.value}
                onChange={() => setStrategy(s.value)}
              />
              {s.label}
            </label>
          ))}
        </div>

        <button type="submit" disabled={!file || status === 'uploading'}>
          {status === 'uploading' ? `Uploading… ${progress}%` : 'Ingest document'}
        </button>

        {status === 'uploading' && (
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        )}
      </form>

      {status === 'done' && result && (
        <p className="upload-result">
          <strong>{result.filename}</strong> ingested — {result.total_chunks_stored} chunks
          ({result.strategy_used}).
        </p>
      )}
      {status === 'error' && <p className="error-text">{error}</p>}
    </section>
  );
}

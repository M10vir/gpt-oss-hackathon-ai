import { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

export default function App() {
  const [file, setFile] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [anonymize, setAnonymize] = useState(false);

  const [loading, setLoading] = useState(false);
  const [warming, setWarming] = useState(false);
  const [result, setResult] = useState(null);
  const [compare, setCompare] = useState(null);
  const [err, setErr] = useState(null);
  const [model, setModel] = useState(null);

  const warmUpModel = async () => {
    setErr(null);
    setWarming(true);
    setResult(null);
    setCompare(null);
    try {
      const res = await fetch(`${API_BASE}/resume/warmup`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || `Warmup failed (${res.status})`);
      setModel(data?.model || null);
    } catch (e) {
      setErr(e.message || 'Warmup failed');
    } finally {
      setWarming(false);
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr(null);
    setResult(null);
    setCompare(null);

    if (!file) return setErr('Please choose a PDF resume.');
    if (!file.type?.includes('pdf') && file.type !== 'application/pdf') {
      return setErr('File must be a PDF.');
    }
    if (file.size > 10 * 1024 * 1024) return setErr('PDF too large (>10MB).');
    if (!jobTitle.trim()) return setErr('Please enter a job title.');
    if (!jobDescription.trim()) return setErr('Please paste a job description.');

    const form = new FormData();
    form.append('file', file);
    form.append('job_title', jobTitle.trim());
    form.append('job_description', jobDescription.trim());
    form.append('anonymize', anonymize ? 'true' : 'false');

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/resume/upload`, { method: 'POST', body: form });
      const text = await res.text();
      if (!res.ok) throw new Error(`Upload failed (${res.status}): ${text}`);
      const data = JSON.parse(text);
      setResult(data);
      setModel(data?.model || model);
    } catch (e) {
      setErr(e.message || 'Failed to score resume');
    } finally {
      setLoading(false);
    }
  };

  const runCompare = async () => {
    setErr(null);
    setCompare(null);
    if (!file) return setErr('Choose a PDF first.');

    const form = new FormData();
    form.append('file', file);
    form.append('job_title', jobTitle.trim() || 'Unknown');
    form.append('job_description', jobDescription.trim() || '');

    try {
      const res = await fetch(`${API_BASE}/resume/compare`, { method: 'POST', body: form });
      const text = await res.text();
      if (!res.ok) throw new Error(`Compare failed (${res.status}): ${text}`);
      const data = JSON.parse(text);
      setCompare(data);
      setModel(data?.model || model);
    } catch (e) {
      setErr(e.message || 'Compare failed');
    }
  };

  return (
    <div style={{maxWidth: 900, margin: '40px auto', padding: 16, fontFamily: 'system-ui'}}>
      <h1 style={{marginBottom: 4}}>GPT-OSS Resume Scorer</h1>
      <div style={{color:'#666', marginBottom: 16}}>
        Local inference via Ollama · FastAPI backend
      </div>

      <form onSubmit={onSubmit} style={{display:'grid', gap: 12}}>
        <label>
          <div>Upload PDF Resume</div>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </label>

        <label>
          <div>Job Title</div>
          <input
            type="text"
            placeholder="Senior DevOps Engineer"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            style={{padding:8, width:'100%'}}
          />
        </label>

        <label>
          <div>Job Description</div>
          <textarea
            placeholder="Paste JD here…"
            rows={8}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            style={{padding:8, width:'100%'}}
          />
        </label>

        <label style={{display:'flex', gap:8, alignItems:'center'}}>
          <input
            type="checkbox"
            checked={anonymize}
            onChange={(e) => setAnonymize(e.target.checked)}
          />
          Anonymize before scoring (bias-aware)
        </label>

        <div style={{display:'flex', gap:12, marginTop:4}}>
          <button
            type="submit"
            disabled={loading}
            style={{
              padding:'10px 14px',
              border:'1px solid #ccc',
              borderRadius:8,
              background: loading ? '#eaeaea' : '#fff',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Scoring…' : 'Upload & Score'}
          </button>

          <button
            type="button"
            onClick={warmUpModel}
            disabled={warming}
            style={{
              padding:'10px 14px',
              border:'1px solid #ccc',
              borderRadius:8,
              background: warming ? '#eaeaea' : '#fff',
              cursor: warming ? 'not-allowed' : 'pointer'
            }}
          >
            {warming ? 'Warming…' : 'Warm Up Model'}
          </button>

          <button
            type="button"
            onClick={runCompare}
            disabled={!file}
            title="Compare original vs anonymized scoring"
            style={{
              padding:'10px 14px',
              border:'1px solid #ccc',
              borderRadius:8,
              background: '#fff',
              cursor: !file ? 'not-allowed' : 'pointer'
            }}
          >
            Bias Compare
          </button>
        </div>
      </form>

      {err && (
        <div style={{marginTop:16, padding:12, border:'1px solid #f5c2c7', background:'#fff5f6', color:'#b4232c', borderRadius:8}}>
          <b>Error:</b> {err}
        </div>
      )}

      {result && (
        <div style={{marginTop:24, padding:16, border:'1px solid #ddd', borderRadius:8}}>
          <h3 style={{marginTop:0}}>Result</h3>
          <div><b>File:</b> {result.filename}</div>
          <div><b>Job Title:</b> {result.job_title}</div>
          <div><b>Score:</b> {result.relevance_score}</div>
          <div><b>Summary:</b> {result.summary}</div>

          {Array.isArray(result.evidence) && result.evidence.length > 0 && (
            <div style={{marginTop:16}}>
              <b>Evidence</b>
              <ul>
                {result.evidence.map((ev, i) => (
                  <li key={i} style={{marginTop:4}}>
                    ✅ <i>{ev.requirement || 'Requirement'}</i> — {ev.match || ''}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {Array.isArray(result.risks) && result.risks.length > 0 && (
            <div style={{marginTop:12}}>
              <b>Risks / Missing</b>
              <ul>
                {result.risks.map((r, i) => (
                  <li key={i} style={{color:'#b4232c', marginTop:4}}>⚠️ {r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {compare && (
        <div style={{marginTop:24, padding:16, border:'1px solid #ddd', borderRadius:8}}>
          <h3 style={{marginTop:0}}>Bias Compare</h3>
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
            <div>
              <b>Original</b>
              <div>Score: {compare.original?.score}</div>
              <div style={{color:'#555'}}>{compare.original?.summary}</div>
            </div>
            <div>
              <b>Anonymized</b>
              <div>Score: {compare.anonymized?.score}</div>
              <div style={{color:'#555'}}>{compare.anonymized?.summary}</div>
            </div>
          </div>
          <div style={{marginTop:8}}>
            <b>Delta:</b> {compare.delta} (original - anonymized)
          </div>
        </div>
      )}

      <div style={{marginTop:32, fontSize:14, color:'#666'}}>
        Backend health: <a href={`${API_BASE}/health`} target="_blank" rel="noreferrer">{API_BASE}/health</a>
        {model && <span style={{marginLeft:12}}>• Model: <code>{model}</code></span>}
      </div>
    </div>
  );
} 

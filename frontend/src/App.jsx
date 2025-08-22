import { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

export default function App() {
  const [file, setFile] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr(null);
    setResult(null);

    if (!file) return setErr('Please choose a PDF resume.');
    if (!file.type.includes('pdf')) return setErr('File must be a PDF.');
    if (file.size > 10 * 1024 * 1024) return setErr('PDF too large (>10MB).');
    if (!jobTitle.trim()) return setErr('Please enter a job title.');
    if (!jobDescription.trim()) return setErr('Please paste a job description.');

    const form = new FormData();
    form.append('file', file);
    form.append('job_title', jobTitle.trim());
    form.append('job_description', jobDescription.trim());

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/resume/upload`, { method: 'POST', body: form });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`Upload failed (${res.status}): ${msg}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setErr(e.message || 'Failed to score resume');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{maxWidth: 840, margin: '40px auto', padding: 16, fontFamily: 'system-ui'}}>
      <h1 style={{marginBottom: 4}}>GPT‑OSS Resume Scorer</h1>
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

        <button
          type="submit"
          disabled={loading}
          style={{
            padding:'10px 14px',
            border:'1px solid #ccc',
            borderRadius:8,
            background: loading ? '#eaeaea' : '#fff',
            cursor: loading ? 'not-allowed' : 'pointer',
            width: 180
          }}
        >
          {loading ? 'Scoring…' : 'Upload & Score'}
        </button>
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
        </div>
      )}

      <div style={{marginTop:32, fontSize:14, color:'#666'}}>
        Backend health: <a href={`${API_BASE}/health`} target="_blank">{API_BASE}/health</a>
      </div>
    </div>
  );
}

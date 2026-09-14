import React, { useState } from 'react';
import { Copy, Check, Terminal, FileCode } from 'lucide-react';
import { AgentPipelineResponse } from '../types/clinical';

interface AuditJSONProps {
  pipelineData: AgentPipelineResponse | null;
}

export const AuditJSON: React.FC<AuditJSONProps> = ({ pipelineData }) => {
  const [copied, setCopied] = useState(false);
  const [selectedSection, setSelectedSection] = useState<'all' | 'evidence' | 'reconciliation' | 'documentation' | 'validation'>('all');

  if (!pipelineData) {
    return (
      <div className="card">
        <div className="card-body" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          No agent execution data available yet. Click "Run Clinical Agent" to execute the pipeline.
        </div>
      </div>
    );
  }

  let displayData: any = pipelineData;
  if (selectedSection === 'evidence') displayData = pipelineData.evidence_summary;
  else if (selectedSection === 'reconciliation') displayData = pipelineData.reconciliation_summary;
  else if (selectedSection === 'documentation') displayData = pipelineData.documentation;
  else if (selectedSection === 'validation') displayData = pipelineData.validation;

  const jsonString = JSON.stringify(displayData, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card">
      <div className="card-header" style={{ background: '#0f172a', color: 'white' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Terminal size={18} color="#38bdf8" />
          <span style={{ fontSize: '0.95rem', fontWeight: 700 }}>
            Audit View: Live Backend JSON Payload
          </span>
          <span className="badge badge-demo" style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #0284c7' }}>
            POST /patients/{pipelineData.patient_id}/run-agent
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-sm"
            onClick={handleCopy}
            style={{
              background: '#1e293b',
              color: copied ? '#4ade80' : '#f8fafc',
              border: '1px solid #334155'
            }}
          >
            {copied ? (
              <>
                <Check size={12} color="#4ade80" /> Copied!
              </>
            ) : (
              <>
                <Copy size={12} /> Copy JSON
              </>
            )}
          </button>
        </div>
      </div>

      <div style={{ background: '#1e293b', padding: '10px 16px', borderBottom: '1px solid #334155', display: 'flex', gap: '8px' }}>
        {(['all', 'evidence', 'reconciliation', 'documentation', 'validation'] as const).map((sec) => (
          <button
            key={sec}
            onClick={() => setSelectedSection(sec)}
            style={{
              background: selectedSection === sec ? '#3b82f6' : 'transparent',
              color: selectedSection === sec ? 'white' : '#94a3b8',
              border: 'none',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              textTransform: 'capitalize'
            }}
          >
            {sec === 'all' ? 'Full Response' : sec}
          </button>
        ))}
      </div>

      <div className="card-body" style={{ background: '#090d16', padding: 0 }}>
        <pre className="json-viewer">
          {jsonString}
        </pre>
      </div>
    </div>
  );
};

import React from 'react';
import { X, ExternalLink, Calendar, Database, FileText } from 'lucide-react';
import { EvidenceLink } from '../types/clinical';

interface EvidenceModalProps {
  isOpen: boolean;
  title: string;
  evidenceLinks: EvidenceLink[];
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  isOpen,
  title,
  evidenceLinks,
  onClose
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="card-header" style={{ background: '#f8fafc' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color="#2563eb" />
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>
              Evidence Provenance: {title}
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: '#64748b',
              padding: '4px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        <div className="card-body" style={{ maxHeight: '65vh', overflowY: 'auto' }}>
          <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '16px' }}>
            Full grounding references extracted from patient medical sources verifying this clinical claim:
          </p>

          {evidenceLinks && evidenceLinks.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {evidenceLinks.map((ev, idx) => (
                <div
                  key={idx}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '12px 14px',
                    background: '#ffffff'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span className="badge badge-demo" style={{ textTransform: 'capitalize' }}>
                      <Database size={11} /> {ev.source.replace('_', ' ')}
                    </span>
                    {ev.source_date && (
                      <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Calendar size={12} /> {ev.source_date}
                      </span>
                    )}
                  </div>

                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b', marginBottom: '6px' }}>
                    {ev.claim}
                  </div>

                  <div style={{
                    background: '#f8fafc',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    borderLeft: '3px solid #3b82f6',
                    fontFamily: 'inherit',
                    fontSize: '0.78rem',
                    color: '#334155',
                    fontStyle: 'italic'
                  }}>
                    "{ev.raw_excerpt}"
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>
              No explicit evidence links recorded.
            </div>
          )}
        </div>

        <div style={{
          padding: '12px 20px',
          background: '#f8fafc',
          borderTop: '1px solid #e2e8f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <ExternalLink size={12} /> Deterministic traceability preserved across encounters
          </span>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

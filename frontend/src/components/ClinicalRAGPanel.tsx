import React from 'react';
import { BookOpen, ShieldAlert, ExternalLink, Bookmark } from 'lucide-react';
import { ClinicalReferenceLink } from '../types/clinical';

interface ClinicalRAGPanelProps {
  references: ClinicalReferenceLink[];
}

export const ClinicalRAGPanel: React.FC<ClinicalRAGPanelProps> = ({
  references
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card" style={{ borderTop: '4px solid #9333ea' }}>
        <div className="card-header" style={{ background: '#ffffff' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <BookOpen size={22} color="#9333ea" />
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>
                Clinical Reference Context (RAG)
              </h2>
              <span className="badge" style={{ background: '#f5f3ff', color: '#7e22ce', border: '1px solid #ddd6fe' }}>
                Phase 4 Vector Retrieval
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
              External guideline evidence retrieved for contextual evaluation | {references.length} references linked
            </p>
          </div>

          <div>
            <span className="rag-warning-tag">
              REFERENCE CONTEXT — NOT PATIENT FACT
            </span>
          </div>
        </div>

        <div className="card-body">
          {/* Segregation Warning Box */}
          <div style={{
            background: '#faf5ff',
            border: '1px solid #e9d5ff',
            borderRadius: '10px',
            padding: '14px 18px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px'
          }}>
            <ShieldAlert size={20} color="#9333ea" style={{ marginTop: '2px', flexShrink: 0 }} />
            <div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#6b21a8' }}>
                Strict Patient Fact vs Clinical Guideline Segregation
              </h4>
              <p style={{ fontSize: '0.8rem', color: '#581c87', marginTop: '2px', lineHeight: 1.45 }}>
                A clinical practice guideline must <strong>never</strong> be treated as evidence that a patient has a condition, takes a medication, or had a test performed. The system quarantines reference material in this section to prevent guideline hallucination into patient medical records.
              </p>
            </div>
          </div>

          {/* Reference Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {references.map((ref, idx) => (
              <div key={idx} className="rag-card">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="badge badge-demo" style={{ fontFamily: 'monospace' }}>
                      {ref.document_id}
                    </span>
                    <span style={{ fontSize: '0.82rem', fontWeight: 800, color: '#1e293b' }}>
                      {ref.entity}
                    </span>
                  </div>

                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7e22ce' }}>
                    Score: {ref.relevance_score.toFixed(3)}
                  </span>
                </div>

                <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#0f172a', marginBottom: '4px' }}>
                  {ref.title}
                </div>

                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Bookmark size={12} />
                  <span>Section: {ref.section} | Source: {ref.source_organization}</span>
                </div>

                <div style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  padding: '10px 12px',
                  fontSize: '0.8rem',
                  color: '#334155',
                  lineHeight: 1.45
                }}>
                  "{ref.snippet}"
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

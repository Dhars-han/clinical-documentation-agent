import React, { useState } from 'react';
import {
  GitCompare,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Database,
  MessageSquare,
  ShieldAlert,
  ExternalLink,
  Search,
  Filter
} from 'lucide-react';
import { ReconciliationReport, ReconciliationResult, EvidenceLink } from '../types/clinical';

interface ReconciledProfileDiffProps {
  reconciliationReport: ReconciliationReport | null;
  onViewEvidenceModal?: (title: string, references: EvidenceLink[]) => void;
}

export const ReconciledProfileDiff: React.FC<ReconciledProfileDiffProps> = ({
  reconciliationReport,
  onViewEvidenceModal
}) => {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  // Hardened mock rows if reconciliation report is null
  const defaultResults: ReconciliationResult[] = [
    {
      patient_id: 'P001',
      entity: 'Drug B',
      category: 'medication',
      status: 'resolved' as any,
      current_state: 'discontinued (10 mg)',
      confidence: 0.96,
      reason: 'Patient reported cessation of Drug B due to nausea; matches EHR database discontinued status (2026-09-10), superseding prior 2026-08-20 note.',
      supporting_evidence: [
        { source: 'consultation', source_date: '2026-09-13', raw_excerpt: 'I stopped taking Drug B approximately one week ago because it caused nausea.', attributes: { action: 'stopped' } },
        { source: 'medication_database', source_date: '2026-09-10', raw_excerpt: 'Drug B 10 mg once daily (status: discontinued)', attributes: { status: 'discontinued' } }
      ],
      conflicting_evidence: [
        { source: 'previous_note', source_date: '2026-08-20', raw_excerpt: 'Patient taking Metformin 500mg daily and Drug B 10mg daily.', attributes: { status: 'active' } }
      ],
      requires_human_review: false
    },
    {
      patient_id: 'P001',
      entity: 'Penicillin',
      category: 'allergy',
      status: 'conflict' as any,
      current_state: null,
      confidence: 0.45,
      reason: 'CONSEQUENTIAL CONFLICT: EHR registry records active Penicillin allergy (2026-09-08), but patient denied drug allergies in consultation (2026-09-13). Flagged for mandatory clinician verification before beta-lactam prescribing.',
      supporting_evidence: [
        { source: 'allergy_database', source_date: '2026-09-08', raw_excerpt: 'Allergen: Penicillin, Reaction: Unknown', attributes: { allergen: 'Penicillin' } }
      ],
      conflicting_evidence: [
        { source: 'consultation', source_date: '2026-09-13', raw_excerpt: 'Patient reports no known drug allergies.', attributes: { status: 'denied' } }
      ],
      requires_human_review: true
    },
    {
      patient_id: 'P001',
      entity: 'Metformin',
      category: 'medication',
      status: 'consistent' as any,
      current_state: 'active (500 mg once daily)',
      confidence: 0.98,
      reason: 'Concordant across hospital database, prior clinic notes, and patient consultation testimony.',
      supporting_evidence: [
        { source: 'medication_database', source_date: '2026-09-10', raw_excerpt: 'Metformin 500 mg once daily (status: active)', attributes: { status: 'active' } },
        { source: 'consultation', source_date: '2026-09-13', raw_excerpt: 'Patient reports taking Metformin 500 mg once daily with meals.', attributes: { status: 'active' } }
      ],
      conflicting_evidence: [],
      requires_human_review: false
    },
    {
      patient_id: 'P001',
      entity: 'Hemoglobin A1c (HbA1c)',
      category: 'lab',
      status: 'consistent' as any,
      current_state: '7.1 % (2026-09-10)',
      confidence: 0.95,
      reason: 'Recent metabolic lab record verified in laboratory database.',
      supporting_evidence: [
        { source: 'laboratory_database', source_date: '2026-09-10', raw_excerpt: 'HbA1c: 7.1 %', attributes: { value: '7.1' } }
      ],
      conflicting_evidence: [],
      requires_human_review: false
    },
    {
      patient_id: 'P001',
      entity: 'Serum Creatinine',
      category: 'lab',
      status: 'consistent' as any,
      current_state: '1.0 mg/dL (2026-09-10)',
      confidence: 0.95,
      reason: 'Renal safety baseline stable at 1.0 mg/dL (eGFR 78 mL/min).',
      supporting_evidence: [
        { source: 'laboratory_database', source_date: '2026-09-10', raw_excerpt: 'Serum Creatinine: 1.0 mg/dL', attributes: { value: '1.0' } }
      ],
      conflicting_evidence: [],
      requires_human_review: false
    }
  ];

  const results = reconciliationReport?.results && reconciliationReport.results.length > 0
    ? reconciliationReport.results
    : defaultResults;

  const filteredResults = results.filter((r) => {
    if (filterCategory === 'ALL') return true;
    if (filterCategory === 'CONFLICTS' && r.requires_human_review) return true;
    if (filterCategory === 'MEDICATIONS' && r.category.toLowerCase().includes('med')) return true;
    if (filterCategory === 'ALLERGIES' && r.category.toLowerCase().includes('all')) return true;
    if (filterCategory === 'LABS' && r.category.toLowerCase().includes('lab')) return true;
    return false;
  });

  return (
    <div className="card" style={{ marginBottom: '24px' }}>
      <div className="card-header" style={{ background: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: '#eff6ff',
              color: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <GitCompare size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Reconciled Clinical Profile (Source Diff Table)
            </h3>
            <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '2px 0 0 0' }}>
              Multi-source cross-comparison: Raw Evidence Facts vs Resolved Clinical State & Grounding Confidence
            </p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {[
            { id: 'ALL', label: 'All Entities' },
            { id: 'CONFLICTS', label: 'Conflicts Only (Escalated)' },
            { id: 'MEDICATIONS', label: 'Medications' },
            { id: 'ALLERGIES', label: 'Allergies' },
            { id: 'LABS', label: 'Labs' }
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilterCategory(f.id)}
              style={{
                background: filterCategory === f.id ? '#2563eb' : '#f1f5f9',
                color: filterCategory === f.id ? '#ffffff' : '#475569',
                border: 'none',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="card-body" style={{ padding: 0 }}>
        <table className="clinical-table">
          <thead>
            <tr>
              <th style={{ width: '18%' }}>Clinical Entity</th>
              <th style={{ width: '30%' }}>Raw Multi-Source Evidence</th>
              <th style={{ width: '22%' }}>Resolved Fact & State</th>
              <th style={{ width: '15%' }}>Confidence Score</th>
              <th style={{ width: '15%' }}>Audit Provenance</th>
            </tr>
          </thead>
          <tbody>
            {filteredResults.map((r, idx) => {
              const isConflict = r.requires_human_review || r.status.toLowerCase() === 'conflict';
              const confidencePercent = Math.round((r.confidence ?? 0.85) * 100);

              return (
                <tr
                  key={idx}
                  style={{
                    background: isConflict ? '#fffdf7' : 'transparent',
                    borderLeft: isConflict ? '4px solid #d97706' : '4px solid transparent'
                  }}
                >
                  {/* Entity & Category */}
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <span style={{ fontWeight: 800, color: '#0f172a', fontSize: '0.88rem' }}>
                        {r.entity}
                      </span>
                      <span className="badge badge-info" style={{ width: 'fit-content', fontSize: '0.68rem' }}>
                        {r.category.toUpperCase()}
                      </span>
                    </div>
                  </td>

                  {/* Raw Sources Diff */}
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.75rem' }}>
                      {r.supporting_evidence.map((ev, sIdx) => (
                        <div
                          key={sIdx}
                          style={{
                            background: '#f8fafc',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            border: '1px solid #e2e8f0'
                          }}
                        >
                          <span style={{ fontWeight: 700, color: '#2563eb' }}>
                            [{ev.source} {ev.source_date || ''}]:
                          </span>{' '}
                          <span style={{ color: '#334155' }}>"{ev.raw_excerpt}"</span>
                        </div>
                      ))}

                      {r.conflicting_evidence.map((ev, cIdx) => (
                        <div
                          key={cIdx}
                          style={{
                            background: '#fef2f2',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            border: '1px solid #fecaca'
                          }}
                        >
                          <span style={{ fontWeight: 700, color: '#dc2626' }}>
                            [CONFLICT {ev.source} {ev.source_date || ''}]:
                          </span>{' '}
                          <span style={{ color: '#991b1b' }}>"{ev.raw_excerpt}"</span>
                        </div>
                      ))}
                    </div>
                  </td>

                  {/* Resolved Fact & Status */}
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {isConflict ? (
                        <span className="badge badge-warning">
                          <AlertTriangle size={12} /> UNRESOLVED CONFLICT
                        </span>
                      ) : (
                        <span className="badge badge-success">
                          <CheckCircle2 size={12} /> {r.status.toUpperCase()}
                        </span>
                      )}

                      <div style={{ fontWeight: 700, color: isConflict ? '#92400e' : '#0f172a', fontSize: '0.8rem' }}>
                        {r.current_state || 'Indeterminate (Human Review Mandatory)'}
                      </div>

                      <div style={{ fontSize: '0.7rem', color: '#64748b', lineHeight: 1.3 }}>
                        {r.reason}
                      </div>
                    </div>
                  </td>

                  {/* Confidence Score */}
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span
                          style={{
                            fontWeight: 800,
                            fontSize: '0.82rem',
                            color: isConflict ? '#d97706' : '#059669'
                          }}
                        >
                          {confidencePercent}%
                        </span>
                        <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                          {isConflict ? 'Uncertainty' : 'Verified'}
                        </span>
                      </div>
                      <div
                        style={{
                          height: '6px',
                          borderRadius: '9999px',
                          background: '#e2e8f0',
                          overflow: 'hidden'
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${confidencePercent}%`,
                            background: isConflict ? '#d97706' : '#10b981'
                          }}
                        />
                      </div>
                    </div>
                  </td>

                  {/* Provenance Link */}
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => {
                        if (onViewEvidenceModal) {
                          const links: EvidenceLink[] = [...r.supporting_evidence, ...r.conflicting_evidence].map((ev) => ({
                            source: ev.source,
                            source_date: ev.source_date || null,
                            raw_excerpt: ev.raw_excerpt,
                            attributes: ev.attributes,
                            claim: ev.raw_excerpt
                          }));
                          onViewEvidenceModal(`Source Evidence: ${r.entity}`, links);
                        }
                      }}
                      style={{ fontSize: '0.72rem', padding: '4px 8px', gap: '4px' }}
                    >
                      <ExternalLink size={12} />
                      <span>Audit ({(r.supporting_evidence?.length || 0) + (r.conflicting_evidence?.length || 0)})</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

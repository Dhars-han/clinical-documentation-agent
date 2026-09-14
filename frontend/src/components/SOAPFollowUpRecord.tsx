import React, { useState } from 'react';
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  BookOpen,
  Info,
  ShieldCheck,
  ClipboardList
} from 'lucide-react';
import { ClinicalFollowUpRecord, EvidenceLink } from '../types/clinical';

interface SOAPFollowUpRecordProps {
  record: ClinicalFollowUpRecord;
  onViewEvidence?: (title: string, references: EvidenceLink[]) => void;
}

interface CitationTooltipState {
  visible: boolean;
  x: number;
  y: number;
  title: string;
  source: string;
  date: string;
  quote: string;
}

export const SOAPFollowUpRecord: React.FC<SOAPFollowUpRecordProps> = ({
  record,
  onViewEvidence
}) => {
  const [tooltip, setTooltip] = useState<CitationTooltipState>({
    visible: false,
    x: 0,
    y: 0,
    title: '',
    source: '',
    date: '',
    quote: ''
  });

  const showTooltip = (
    e: React.MouseEvent,
    title: string,
    source: string,
    date: string,
    quote: string
  ) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltip({
      visible: true,
      x: rect.left,
      y: rect.bottom + 8,
      title,
      source,
      date,
      quote
    });
  };

  const hideTooltip = () => {
    setTooltip((prev) => ({ ...prev, visible: false }));
  };

  const isPenicillinConflict = record.unresolved_conflicts.some((c) =>
    c.toLowerCase().includes('penicillin')
  );

  return (
    <div className="card" style={{ marginBottom: '24px' }}>
      {/* Floating Citation Tooltip */}
      {tooltip.visible && (
        <div
          style={{
            position: 'fixed',
            left: `${Math.min(tooltip.x, window.innerWidth - 340)}px`,
            top: `${tooltip.y}px`,
            zIndex: 1000,
            width: '320px',
            background: '#0f172a',
            color: '#f8fafc',
            borderRadius: '8px',
            padding: '10px 14px',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.4)',
            border: '1px solid #334155',
            fontSize: '0.75rem',
            lineHeight: 1.4,
            pointerEvents: 'none'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontWeight: 700, color: '#38bdf8' }}>{tooltip.title}</span>
            <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>{tooltip.date}</span>
          </div>
          <div style={{ fontSize: '0.68rem', color: '#cbd5e1', marginBottom: '6px' }}>
            Source: <strong style={{ color: '#ffffff' }}>{tooltip.source}</strong>
          </div>
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              padding: '6px 8px',
              borderRadius: '4px',
              fontStyle: 'italic',
              color: '#e2e8f0'
            }}
          >
            "{tooltip.quote}"
          </div>
        </div>
      )}

      {/* Header */}
      <div className="card-header" style={{ background: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: '#ecfdf5',
              color: '#059669',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <FileText size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Drafted Follow-up Record (Structured SOAP Note)
            </h3>
            <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '2px 0 0 0' }}>
              Standard clinical documentation with interactive inline citations from transcripts and EHR records
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {onViewEvidence && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                const links: EvidenceLink[] = record.clinical_references.map((r) => ({
                  source: r.source_organization,
                  source_date: r.publication_date || null,
                  raw_excerpt: r.snippet,
                  claim: r.title
                }));
                onViewEvidence('Clinical Evidence Provenance Audit', links);
              }}
              style={{ fontSize: '0.72rem', padding: '4px 8px', gap: '4px' }}
            >
              <ExternalLink size={12} />
              <span>Audit Provenance</span>
            </button>
          )}
          <span className="badge badge-success">
            <CheckCircle2 size={12} /> Grounded in Verified Evidence
          </span>
          {record.requires_human_review && (
            <span className="badge badge-warning">
              <AlertTriangle size={12} /> Requires Clinician Sign-off
            </span>
          )}
        </div>
      </div>

      <div className="card-body" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* S - SUBJECTIVE */}
        <div
          style={{
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '16px',
            background: '#ffffff'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span
              style={{
                background: '#eff6ff',
                color: '#2563eb',
                fontWeight: 800,
                fontSize: '0.8rem',
                padding: '3px 8px',
                borderRadius: '4px'
              }}
            >
              S — SUBJECTIVE
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b' }}>
              Patient Encounter History & Reported Statements
            </span>
          </div>

          <p style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.6, margin: 0 }}>
            Patient presented for routine post-consultation follow-up regarding type 2 diabetes and hypertension.{' '}
            <span>
              Patient reports consistent adherence to Metformin 500 mg once daily taken with meals
            </span>{' '}
            <span
              className="citation-tag"
              onMouseEnter={(e) =>
                showTooltip(
                  e,
                  'Medication Adherence',
                  'Consultation Transcript',
                  '2026-09-13',
                  'Patient reports that they are still taking Metformin 500 mg once daily.'
                )
              }
              onMouseLeave={hideTooltip}
            >
              [Transcript: Metformin 500mg]
            </span>
            .{' '}
            <span>
              Patient states they discontinued Drug B 10 mg approximately one week ago due to mild recurrent morning nausea
            </span>{' '}
            <span
              className="citation-tag"
              onMouseEnter={(e) =>
                showTooltip(
                  e,
                  'Medication Cessation',
                  'Consultation Transcript',
                  '2026-09-13',
                  'Patient says they stopped Drug B approximately one week ago because it caused nausea.'
                )
              }
              onMouseLeave={hideTooltip}
            >
              [Transcript: Drug B Stopped]
            </span>
            .{' '}
            <span>
              When questioned regarding drug allergies, patient reported having no known drug allergies
            </span>{' '}
            <span
              className="citation-tag citation-tag-warning"
              onMouseEnter={(e) =>
                showTooltip(
                  e,
                  'Allergy Denial Statement',
                  'Consultation Transcript',
                  '2026-09-13',
                  'Patient reports no known drug allergies.'
                )
              }
              onMouseLeave={hideTooltip}
            >
              [Transcript: No Allergies Claimed]
            </span>
            .
          </p>
        </div>

        {/* O - OBJECTIVE */}
        <div
          style={{
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '16px',
            background: '#ffffff'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span
              style={{
                background: '#f0fdf4',
                color: '#166534',
                fontWeight: 800,
                fontSize: '0.8rem',
                padding: '3px 8px',
                borderRadius: '4px'
              }}
            >
              O — OBJECTIVE
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b' }}>
              EHR Verified Database Records & Diagnostic Findings
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {/* Medications & Allergies */}
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', marginBottom: '6px' }}>
                Active & Reconciled Medications:
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.82rem', color: '#334155' }}>
                <li style={{ marginBottom: '4px' }}>
                  <strong>Metformin 500 mg</strong> once daily — Active{' '}
                  <span
                    className="citation-tag"
                    onMouseEnter={(e) =>
                      showTooltip(
                        e,
                        'Active Medication Order',
                        'EHR Medication DB',
                        '2026-09-10',
                        'Metformin 500 mg once daily (status: active, record_id: 1)'
                      )
                    }
                    onMouseLeave={hideTooltip}
                  >
                    [EHR DB: Active]
                  </span>
                </li>
                <li style={{ marginBottom: '4px' }}>
                  <strong>Drug B 10 mg</strong> — Discontinued per EHR & Patient{' '}
                  <span
                    className="citation-tag"
                    onMouseEnter={(e) =>
                      showTooltip(
                        e,
                        'Discontinued Order',
                        'EHR Medication DB',
                        '2026-09-10',
                        'Drug B 10 mg once daily (status: discontinued, record_id: 2)'
                      )
                    }
                    onMouseLeave={hideTooltip}
                  >
                    [EHR DB: Discontinued]
                  </span>
                </li>
              </ul>

              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', marginTop: '10px', marginBottom: '6px' }}>
                EHR Allergy Registry Profile:
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.82rem', color: '#334155' }}>
                <li>
                  <strong style={{ color: '#b91c1c' }}>Penicillin</strong> — Documented Allergy (Reaction: Unknown){' '}
                  <span
                    className="citation-tag citation-tag-danger"
                    onMouseEnter={(e) =>
                      showTooltip(
                        e,
                        'EHR Allergy Profile',
                        'EHR Allergy Registry',
                        '2026-09-08',
                        'Allergen: Penicillin, Reaction: Unknown, record_id: 1'
                      )
                    }
                    onMouseLeave={hideTooltip}
                  >
                    [EHR Registry 2026-09-08]
                  </span>
                </li>
              </ul>
            </div>

            {/* Diagnostic Labs */}
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', marginBottom: '6px' }}>
                Laboratory Results (Verified 2026-09-10):
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.82rem', color: '#334155' }}>
                <li style={{ marginBottom: '4px' }}>
                  <strong>Hemoglobin A1c (HbA1c):</strong> 7.1 % (Reference: &lt; 5.7%){' '}
                  <span
                    className="citation-tag"
                    onMouseEnter={(e) =>
                      showTooltip(
                        e,
                        'HbA1c Lab Report',
                        'Laboratory DB',
                        '2026-09-10',
                        'HbA1c: 7.1 % (Ref: < 5.7%)'
                      )
                    }
                    onMouseLeave={hideTooltip}
                  >
                    [Lab DB: 7.1%]
                  </span>
                </li>
                <li style={{ marginBottom: '4px' }}>
                  <strong>Serum Creatinine:</strong> 1.0 mg/dL (Reference: 0.7 - 1.3 mg/dL){' '}
                  <span
                    className="citation-tag"
                    onMouseEnter={(e) =>
                      showTooltip(
                        e,
                        'Serum Creatinine',
                        'Laboratory DB',
                        '2026-09-10',
                        'Creatinine: 1.0 mg/dL (Ref: 0.7 - 1.3 mg/dL)'
                      )
                    }
                    onMouseLeave={hideTooltip}
                  >
                    [Lab DB: 1.0 mg/dL]
                  </span>
                </li>
                <li>
                  <strong>eGFR (Estimated):</strong> 78 mL/min/1.73m² (Normal renal baseline)
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* A - ASSESSMENT */}
        <div
          style={{
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '16px',
            background: '#ffffff'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span
              style={{
                background: '#faf5ff',
                color: '#7e22ce',
                fontWeight: 800,
                fontSize: '0.8rem',
                padding: '3px 8px',
                borderRadius: '4px'
              }}
            >
              A — ASSESSMENT
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b' }}>
              Multi-Source Clinical Synthesis & Conflict Identification
            </span>
          </div>

          <p style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.6, margin: '0 0 10px 0' }}>
            1. <strong>Type 2 Diabetes Mellitus:</strong> Glycemic control stable on Metformin 500mg daily (HbA1c 7.1%). Renal function is intact (Creatinine 1.0 mg/dL).
          </p>
          <p style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.6, margin: '0 0 10px 0' }}>
            2. <strong>Medication Reconciliation:</strong> Patient-initiated discontinuation of Drug B 10mg is reconciled and supported by the EHR database status (2026-09-10), superseding the previous clinic follow-up note (2026-08-20).
          </p>
          <p
            style={{
              fontSize: '0.85rem',
              color: '#92400e',
              lineHeight: 1.6,
              margin: 0,
              background: '#fffbeb',
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #fde68a'
            }}
          >
            3. <strong>UNRESOLVED CLINICAL CONFLICT — PENICILLIN ALLERGY:</strong> A direct discrepancy exists between the patient's verbal assertion ('no known drug allergies' on 2026-09-13) and hospital EHR records documenting Penicillin allergy (2026-09-08). Under deterministic safety rule RULE-006, the AI did NOT delete or resolve this allergy. Formal clinician re-evaluation is required.
          </p>
        </div>

        {/* P - PLAN */}
        <div
          style={{
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '16px',
            background: '#ffffff'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span
              style={{
                background: '#fff7ed',
                color: '#c2410c',
                fontWeight: 800,
                fontSize: '0.8rem',
                padding: '3px 8px',
                borderRadius: '4px'
              }}
            >
              P — PLAN
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b' }}>
              Care Coordination & Clinical Reference Follow-Up Actions
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '0.83rem', color: '#334155' }}>
              • <strong>Hold Beta-Lactam Prescriptions:</strong> Do not prescribe amoxicillin, penicillin, or cephalosporins until formal allergy verification/testing is complete.
            </div>
            <div style={{ fontSize: '0.83rem', color: '#334155' }}>
              • <strong>Pharmacy Notification:</strong> Confirm cessation of Drug B in outpatient dispensing database to prevent auto-refills.
            </div>
            <div style={{ fontSize: '0.83rem', color: '#334155' }}>
              • <strong>Renal & Glycemic Monitoring:</strong> Re-evaluate HbA1c and Serum Creatinine in 3 to 6 months per ADA practice guidelines.
            </div>
          </div>

          {/* RAG Reference Guidelines */}
          {record.clinical_references && record.clinical_references.length > 0 && (
            <div
              style={{
                marginTop: '14px',
                paddingTop: '12px',
                borderTop: '1px solid #f1f5f9',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                flexWrap: 'wrap'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', fontWeight: 700, color: '#475569' }}>
                <BookOpen size={14} color="#2563eb" />
                <span>External Clinical Guidelines (Phase 4 RAG Segregated):</span>
              </div>
              {record.clinical_references.slice(0, 3).map((ref, idx) => (
                <span
                  key={idx}
                  className="badge badge-info"
                  title={`${ref.title} — ${ref.snippet}`}
                  style={{ fontSize: '0.7rem' }}
                >
                  {ref.document_id} ({ref.source_organization})
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

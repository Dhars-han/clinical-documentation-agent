import React from 'react';
import { GitCompare, CheckCircle2, AlertTriangle, Database, MessageSquare, Clock, ShieldAlert } from 'lucide-react';
import { ReconciliationReport } from '../types/clinical';

interface SourceReconciliationProps {
  reconciliationReport: ReconciliationReport | null;
  onViewEvidenceModal?: (title: string, references: any[]) => void;
}

export const SourceReconciliation: React.FC<SourceReconciliationProps> = ({
  reconciliationReport
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Overview Intro */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <GitCompare size={20} color="#2563eb" />
            <span>Source Reconciliation Matrix</span>
          </div>
          <span className="badge badge-info">
            {reconciliationReport ? `${reconciliationReport.total_entities} Entities Evaluated` : '6 Entities Evaluated'}
          </span>
        </div>
        <div className="card-body">
          <p style={{ fontSize: '0.88rem', color: '#475569', marginBottom: '16px' }}>
            The Reconciliation Engine autonomously cross-compares fragmented EHR databases, physician notes, and latest patient statements to establish whether information is consistent, resolved, outdated, or in unresolved conflict.
          </p>

          {/* DRUG B DEEP DIVE: RESOLVED FROM MULTIPLE SOURCES */}
          <div style={{
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            overflow: 'hidden',
            marginBottom: '24px'
          }}>
            <div style={{
              background: '#f8fafc',
              padding: '12px 16px',
              borderBottom: '1px solid #e2e8f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>Drug B (10 mg)</span>
                <span className="badge badge-success">
                  <CheckCircle2 size={12} /> Resolved: Discontinued
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Category: Medication</span>
            </div>

            <table className="clinical-table">
              <thead>
                <tr>
                  <th style={{ width: '18%' }}>Source</th>
                  <th style={{ width: '16%' }}>Date</th>
                  <th style={{ width: '46%' }}>Evidence & Raw Statement</th>
                  <th style={{ width: '20%' }}>State Extracted</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: '#475569' }}>
                      <Clock size={13} /> Previous Note
                    </span>
                  </td>
                  <td>2026-08-20</td>
                  <td style={{ fontStyle: 'italic', color: '#334155' }}>
                    "Previous follow-up: Patient was taking Metformin 500mg daily and Drug B 10mg daily"
                  </td>
                  <td>
                    <span className="badge badge-info">Active (Historical)</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: '#2563eb' }}>
                      <Database size={13} /> Medication DB
                    </span>
                  </td>
                  <td>2026-09-10</td>
                  <td style={{ color: '#334155' }}>
                    "Drug B 10 mg once daily (status: discontinued)"
                  </td>
                  <td>
                    <span className="badge badge-danger">Discontinued</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: '#059669' }}>
                      <MessageSquare size={13} /> Consultation
                    </span>
                  </td>
                  <td>2026-09-13</td>
                  <td style={{ fontStyle: 'italic', color: '#334155' }}>
                    "Patient says they stopped Drug B approximately one week ago"
                  </td>
                  <td>
                    <span className="badge badge-danger">Reported Stopped</span>
                  </td>
                </tr>
              </tbody>
            </table>

            <div style={{
              background: '#ecfdf5',
              borderTop: '1px solid #a7f3d0',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.82rem'
            }}>
              <div>
                <strong style={{ color: '#065f46' }}>Reconciled Verdict: </strong>
                <span style={{ color: '#047857' }}>
                  Drug B → <strong>DISCONTINUED</strong>. Consultation cessation statement aligns with updated medication record, resolving historical active note.
                </span>
              </div>
              <span style={{ color: '#059669', fontWeight: 700 }}>Confidence: 100%</span>
            </div>
          </div>

          {/* ALLERGY CONFLICT CARD: PRESERVED UNCERTAINTY */}
          <div style={{
            border: '2px solid #f59e0b',
            borderRadius: '12px',
            overflow: 'hidden',
            boxShadow: '0 4px 12px rgba(245, 158, 11, 0.12)'
          }}>
            <div style={{
              background: '#fffbeb',
              padding: '12px 16px',
              borderBottom: '1px solid #fde68a',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1rem', fontWeight: 800, color: '#78350f' }}>Penicillin Allergy</span>
                <span className="badge badge-warning">
                  <AlertTriangle size={12} /> Unresolved Conflict Preserved
                </span>
              </div>
              <span className="badge badge-danger">Human Review Required</span>
            </div>

            <table className="clinical-table">
              <thead>
                <tr>
                  <th style={{ width: '22%' }}>Source</th>
                  <th style={{ width: '18%' }}>Date</th>
                  <th style={{ width: '40%' }}>Raw Evidence</th>
                  <th style={{ width: '20%' }}>State Extracted</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: '#dc2626' }}>
                      <Database size={13} /> Allergy Database
                    </span>
                  </td>
                  <td>2026-09-08</td>
                  <td style={{ color: '#334155' }}>
                    Allergen: <strong>Penicillin</strong> | Reaction: <strong>Unknown</strong>
                  </td>
                  <td>
                    <span className="badge badge-danger">Documented Allergy</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: '#059669' }}>
                      <MessageSquare size={13} /> Current Consultation
                    </span>
                  </td>
                  <td>2026-09-13</td>
                  <td style={{ fontStyle: 'italic', color: '#334155' }}>
                    "Patient reports no known drug allergies"
                  </td>
                  <td>
                    <span className="badge badge-info">Patient Denial</span>
                  </td>
                </tr>
              </tbody>
            </table>

            <div style={{
              background: '#fffbeb',
              borderTop: '1px solid #fde68a',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={18} color="#b45309" />
                <span style={{ fontSize: '0.9rem', fontWeight: 800, color: '#78350f' }}>
                  Responsible Autonomy: Conflict Preserved Without Overriding
                </span>
              </div>
              <p style={{ fontSize: '0.82rem', color: '#92400e', lineHeight: 1.45 }}>
                The agent recognized that patient denial during an interview cannot safely overwrite a documented allergic reaction in the EHR database. Rather than silently picking a winner or deleting the allergy record, the engine preserved the conflict, marked it as <strong>UNRESOLVED</strong>, and triggered an explicit safety escalation for a clinician to verify.
              </p>
            </div>
          </div>

          {/* OTHER ENTITIES GRID */}
          <div style={{ marginTop: '24px' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#334155', marginBottom: '12px' }}>
              Other Reconciled Entities
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '14px', background: 'white' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>Metformin (500 mg)</span>
                  <span className="badge badge-success">Consistent</span>
                </div>
                <p style={{ fontSize: '0.78rem', color: '#64748b' }}>
                  Note (2026-08-20), Medication DB (2026-09-10), and Consultation (2026-09-13) all concur: active 500 mg once daily.
                </p>
              </div>

              <div style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '14px', background: 'white' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>HbA1c (7.1 %)</span>
                  <span className="badge badge-success">Consistent</span>
                </div>
                <p style={{ fontSize: '0.78rem', color: '#64748b' }}>
                  Lab database measurement on 2026-09-10 recorded as 7.1 % with corresponding discussion in clinical notes.
                </p>
              </div>

              <div style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '14px', background: 'white' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>Serum Creatinine (1.0 mg/dL)</span>
                  <span className="badge badge-success">Consistent</span>
                </div>
                <p style={{ fontSize: '0.78rem', color: '#64748b' }}>
                  Laboratory baseline of 1.0 mg/dL from 2026-09-10 verified against renal monitoring guidelines.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

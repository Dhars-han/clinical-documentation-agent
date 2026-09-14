import React from 'react';
import { FileText, CheckCircle2, AlertTriangle, Eye, ArrowRight, ShieldCheck, Activity } from 'lucide-react';
import { ClinicalFollowUpRecord, EvidenceLink } from '../types/clinical';

interface VerifiedRecordProps {
  record: ClinicalFollowUpRecord;
  onViewEvidence: (title: string, references: EvidenceLink[]) => void;
}

export const VerifiedRecord: React.FC<VerifiedRecordProps> = ({
  record,
  onViewEvidence
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Note Document Container */}
      <div className="card" style={{ borderTop: '4px solid #2563eb' }}>
        <div className="card-header" style={{ background: '#ffffff' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FileText size={20} color="#2563eb" />
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>
                Verified Clinical Follow-up Record
              </h2>
              <span className="badge badge-success">
                <ShieldCheck size={12} /> Grounded in Evidence
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
              Generated: {new Date(record.generated_at).toLocaleString()} | Patient: {record.patient_name || record.patient_id} (Age: {record.patient_age})
            </p>
          </div>

          <div>
            {record.requires_human_review ? (
              <span className="badge badge-warning" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
                <AlertTriangle size={13} /> Requires Human Review
              </span>
            ) : (
              <span className="badge badge-success">
                <CheckCircle2 size={13} /> Accepted Automatically
              </span>
            )}
          </div>
        </div>

        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Consultation Summary */}
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#1e293b', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Consultation Encounter Summary
            </h3>
            <div style={{
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '14px 16px',
              fontSize: '0.84rem',
              color: '#334155',
              whiteSpace: 'pre-line',
              lineHeight: 1.55
            }}>
              {record.consultation_summary}
            </div>
          </div>

          {/* Medications Section */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Reconciled Medications ({record.medications.length})
              </h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {record.medications.map((med, idx) => {
                const isDiscontinued = med.status.toLowerCase() === 'discontinued';
                return (
                  <div
                    key={idx}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '12px 16px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: isDiscontinued ? '#fef2f2' : '#ffffff'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>
                          {med.name}
                        </span>
                        <span className={`badge ${isDiscontinued ? 'badge-danger' : 'badge-success'}`}>
                          {med.status.toUpperCase()}
                        </span>
                        <span className="badge badge-info">
                          Reconciliation: {med.reconciliation_status}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '3px' }}>
                        Regimen: <strong>{med.regimen || 'N/A'}</strong>
                      </div>
                    </div>

                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => onViewEvidence(`Medication: ${med.name}`, med.evidence_references)}
                    >
                      <Eye size={12} />
                      View Evidence ({med.evidence_references.length})
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Allergies Section */}
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#1e293b', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Allergies & Adverse Reactions ({record.allergies.length})
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {record.allergies.map((alg, idx) => {
                const isConflict = alg.status.toLowerCase() === 'conflicting';
                return (
                  <div
                    key={idx}
                    style={{
                      border: isConflict ? '1.5px solid #f59e0b' : '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '12px 16px',
                      background: isConflict ? '#fffbeb' : '#ffffff'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.95rem', fontWeight: 800, color: isConflict ? '#92400e' : '#0f172a' }}>
                          {alg.allergen}
                        </span>
                        <span className={`badge ${isConflict ? 'badge-warning' : 'badge-success'}`}>
                          {isConflict ? 'CONFLICTING' : alg.status.toUpperCase()}
                        </span>
                        {alg.requires_human_review && (
                          <span className="badge badge-danger">
                            <AlertTriangle size={11} /> Review Required
                          </span>
                        )}
                      </div>

                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onViewEvidence(`Allergy: ${alg.allergen}`, alg.evidence_references)}
                      >
                        <Eye size={12} />
                        View Evidence ({alg.evidence_references.length})
                      </button>
                    </div>

                    {alg.conflict_details && (
                      <div style={{
                        marginTop: '8px',
                        fontSize: '0.78rem',
                        color: '#b45309',
                        lineHeight: 1.4,
                        borderTop: '1px solid #fde68a',
                        paddingTop: '6px'
                      }}>
                        <strong>Discrepancy Details: </strong>{alg.conflict_details}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Relevant Labs Section */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Observed Diagnostic Measurements ({record.relevant_labs.length})
              </h3>
              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Strictly factual records — non-diagnostic
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
              {record.relevant_labs.map((lab, idx) => (
                <div
                  key={idx}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '12px 14px',
                    background: '#ffffff',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a' }}>{lab.test_name}</span>
                      <span style={{ fontSize: '1rem', fontWeight: 800, color: '#2563eb' }}>
                        {lab.value} <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>{lab.unit}</span>
                      </span>
                    </div>
                    <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '4px' }}>
                      Measured: {lab.date || 'Recent'} | Source: {lab.source.replace('_', ' ')}
                    </div>
                  </div>

                  <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: '0.72rem', padding: '4px 8px' }}
                      onClick={() => onViewEvidence(`Lab: ${lab.test_name}`, lab.evidence_references)}
                    >
                      <Eye size={11} /> Evidence ({lab.evidence_references.length})
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Documented Changes */}
          {record.documented_changes && record.documented_changes.length > 0 && (
            <div>
              <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#1e293b', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Documented Clinical Changes ({record.documented_changes.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {record.documented_changes.map((chg, idx) => (
                  <div
                    key={idx}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      background: '#f8fafc',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <span className="badge badge-demo" style={{ textTransform: 'capitalize', marginRight: '8px' }}>
                        {chg.change_type.replace('_', ' ')}
                      </span>
                      <span style={{ fontSize: '0.84rem', color: '#334155' }}>{chg.description}</span>
                    </div>
                    <button
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: '0.72rem' }}
                      onClick={() => onViewEvidence(`Change: ${chg.entity}`, chg.evidence_references)}
                    >
                      <Eye size={11} /> Evidence
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Follow-Up Coordination Actions */}
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#1e293b', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Follow-Up Coordination Actions ({record.follow_up_actions.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {record.follow_up_actions.map((act, idx) => (
                <div
                  key={idx}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderLeft: act.requires_human_review ? '4px solid #f59e0b' : '4px solid #3b82f6',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    background: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className={`badge ${act.urgency === 'high' ? 'badge-danger' : 'badge-info'}`}>
                      {act.urgency.toUpperCase()}
                    </span>
                    <span style={{ fontSize: '0.84rem', color: '#1e293b', fontWeight: 600 }}>
                      {act.description}
                    </span>
                  </div>

                  {act.requires_human_review && (
                    <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>
                      Human Review
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

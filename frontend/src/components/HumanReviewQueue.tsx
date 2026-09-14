import React from 'react';
import { AlertTriangle, UserCheck, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { ClinicalFollowUpRecord } from '../types/clinical';

interface HumanReviewQueueProps {
  record: ClinicalFollowUpRecord;
}

export const HumanReviewQueue: React.FC<HumanReviewQueueProps> = ({ record }) => {
  if (!record.requires_human_review) {
    return (
      <div className="card" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '24px', textAlign: 'center' }}>
        <CheckCircle2 size={36} color="#16a34a" style={{ margin: '0 auto 8px' }} />
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#166534' }}>
          No Pending Human Reviews Required
        </h3>
        <p style={{ fontSize: '0.84rem', color: '#15803d', marginTop: '4px' }}>
          All clinical information for this encounter was consistently established without consequential discrepancies.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div className="card" style={{ border: '2px solid #f59e0b', background: '#fffbeb' }}>
        <div className="card-header" style={{ background: '#fef3c7', borderBottom: '1px solid #fde68a' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={22} color="#b45309" />
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#78350f' }}>
                Clinical Review Queue: Immediate Action Required
              </h3>
              <p style={{ fontSize: '0.75rem', color: '#92400e' }}>
                Consequential uncertainty flagged by Autonomous Documentation Agent
              </p>
            </div>
          </div>
          <span className="badge badge-danger">
            High Clinical Priority
          </span>
        </div>

        <div className="card-body">
          <div style={{
            background: 'white',
            borderRadius: '10px',
            border: '1px solid #fde68a',
            padding: '18px',
            marginBottom: '16px'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', rowGap: '10px', fontSize: '0.85rem' }}>
              <span style={{ fontWeight: 700, color: '#64748b' }}>Patient:</span>
              <span style={{ fontWeight: 800, color: '#0f172a' }}>
                {record.patient_id} — {record.patient_name || 'Synthetic Patient 001'} (Age: {record.patient_age})
              </span>

              <span style={{ fontWeight: 700, color: '#64748b' }}>Discrepancy:</span>
              <span style={{ fontWeight: 800, color: '#b91c1c' }}>
                Penicillin Allergy Conflict (Database Record vs Consultation Denial)
              </span>

              <span style={{ fontWeight: 700, color: '#64748b' }}>Clinical Context:</span>
              <span style={{ color: '#334155', lineHeight: 1.45 }}>
                Allergy database documents an active Penicillin allergy label (reaction recorded as "Unknown" on 2026-09-08), while the patient verbally denied having any drug allergies during the consultation interview on 2026-09-13.
              </span>

              <span style={{ fontWeight: 700, color: '#64748b' }}>Recommended Action:</span>
              <span style={{ color: '#92400e', fontWeight: 700 }}>
                Perform formal allergy reconciliation and verification before prescribing or administering any beta-lactam antibiotics.
              </span>
            </div>
          </div>

          <div style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.8rem',
            color: '#991b1b'
          }}>
            <ShieldAlert size={18} color="#dc2626" style={{ flexShrink: 0 }} />
            <span>
              <strong>Safety Guardrail Notice:</strong> The agent does not autonomously diagnose allergy status or prescribe alternative antibiotics. Human clinical verification is required to update allergy records safely.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

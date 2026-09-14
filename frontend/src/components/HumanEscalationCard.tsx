import React, { useState } from 'react';
import {
  AlertTriangle,
  ShieldCheck,
  UserCheck,
  CheckCircle2,
  XCircle,
  FileCheck,
  RotateCcw,
  ArrowRight
} from 'lucide-react';
import { ClinicalFollowUpRecord } from '../types/clinical';

interface HumanEscalationCardProps {
  record: ClinicalFollowUpRecord;
}

export const HumanEscalationCard: React.FC<HumanEscalationCardProps> = ({ record }) => {
  const [clinicianAction, setClinicianAction] = useState<string | null>(null);
  const [actionTimestamp, setActionTimestamp] = useState<string | null>(null);
  const conflicts = record.unresolved_conflicts || [];
  const hasPenicillin = conflicts.some((c) => c.toLowerCase().includes('penicillin'));

  const handleAction = (action: string) => {
    const time = new Date().toLocaleTimeString();
    setClinicianAction(action);
    setActionTimestamp(time);
  };

  const handleReset = () => {
    setClinicianAction(null);
    setActionTimestamp(null);
  };

  return (
    <div
      style={{
        background: '#fffdf5',
        border: '1px solid #fde68a',
        borderRadius: '12px',
        padding: '20px',
        boxShadow: '0 4px 12px rgba(217, 119, 6, 0.08)',
        marginBottom: '24px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', flex: 1 }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: '#fef3c7',
              color: '#d97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            <AlertTriangle size={24} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#92400e', margin: 0 }}>
                Escalated Uncertainty: Consequential Clinical Discrepancy Flagged
              </h3>
              <span className="badge badge-warning">
                Clinician Sign-off Required
              </span>
            </div>

            <p style={{ fontSize: '0.86rem', color: '#78350f', lineHeight: 1.5, margin: '0 0 10px 0' }}>
              <strong>The autonomous agent refused to resolve this conflict:</strong> Medical database records documented an active Penicillin allergy (2026-09-08), while current consultation notes indicate the patient verbally denied drug allergies (2026-09-13). Rather than guessing or deleting the allergy profile, the agent preserved the conflict and escalated it to human review under Safety Rule RULE-006.
            </p>

            <div
              style={{
                background: '#ffffff',
                border: '1px solid #fef08a',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '0.78rem',
                color: '#854d0e',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <ShieldCheck size={16} color="#d97706" />
              <span>
                <strong>Clinical Guardrail:</strong> AI is strictly prohibited from deleting allergy records or administering beta-lactams based solely on verbal denial.
              </span>
            </div>
          </div>
        </div>

        {/* Action Signature Box */}
        <div
          style={{
            minWidth: '280px',
            background: '#ffffff',
            border: clinicianAction ? '1px solid #86efac' : '1px solid #fde68a',
            borderRadius: '10px',
            padding: '14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b' }}>
            Clinician Action Sign-off:
          </div>

          {clinicianAction ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#f0fdf4',
                  color: '#15803d',
                  padding: '8px 10px',
                  borderRadius: '6px',
                  border: '1px solid #bbf7d0',
                  fontSize: '0.78rem',
                  fontWeight: 700
                }}
              >
                <UserCheck size={16} />
                <span>{clinicianAction}</span>
              </div>
              <div style={{ fontSize: '0.7rem', color: '#64748b', display: 'flex', justifyContent: 'space-between' }}>
                <span>Signed by Attending Clinician</span>
                <span>{actionTimestamp}</span>
              </div>
              <button
                onClick={handleReset}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.7rem', padding: '3px 8px', marginTop: '4px' }}
              >
                <RotateCcw size={11} /> Reset Decision
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <button
                onClick={() => handleAction('Escalation Approved: Hold Beta-Lactams')}
                className="btn btn-primary btn-sm"
                style={{
                  background: '#d97706',
                  borderColor: '#b45309',
                  fontSize: '0.75rem',
                  justifyContent: 'flex-start'
                }}
              >
                <CheckCircle2 size={13} />
                <span>Approve Escalation (Hold Beta-Lactams)</span>
              </button>

              <button
                onClick={() => handleAction('Override: Allergy Formally Confirmed in EHR')}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.75rem', justifyContent: 'flex-start' }}
              >
                <FileCheck size={13} />
                <span>Override: Confirm Penicillin Allergy</span>
              </button>

              <button
                onClick={() => handleAction('Override: Delabel Allergy (Negative Skin Test)')}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.75rem', justifyContent: 'flex-start' }}
              >
                <XCircle size={13} />
                <span>Override: Delabel (Negative Skin Test)</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

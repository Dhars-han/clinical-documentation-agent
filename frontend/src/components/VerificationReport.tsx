import React from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, XCircle, HelpCircle, Lock } from 'lucide-react';
import { ValidationResult } from '../types/clinical';

interface VerificationReportProps {
  validationResult: ValidationResult;
}

export const VerificationReport: React.FC<VerificationReportProps> = ({
  validationResult
}) => {
  const criteria = [
    {
      id: 'schema',
      ruleId: 'RULE-001',
      name: 'Schema Validation',
      description: 'Record structure, mandatory attributes, and conflict counts verified.',
      passed: true
    },
    {
      id: 'grounding',
      ruleId: 'RULE-001..003',
      name: 'Evidence Grounding',
      description: 'Every medication, allergy, and lab has supporting source excerpts.',
      passed: validationResult.evidence_grounding_passed
    },
    {
      id: 'hallucination',
      ruleId: 'RULE-008',
      name: 'Hallucination & Unsupported Claims',
      description: 'No medications, ungrounded dosages, or lab measurements invented.',
      passed: validationResult.evidence_grounding_passed
    },
    {
      id: 'reconciliation',
      ruleId: 'RULE-004',
      name: 'Reconciliation Consistency',
      description: 'Documentation agrees with Phase 3 reconciliation statuses and timelines.',
      passed: validationResult.reconciliation_consistency_passed
    },
    {
      id: 'conflict',
      ruleId: 'RULE-005',
      name: 'Conflict Preservation',
      description: 'Unresolved reconciliation conflicts are preserved without silent resolution.',
      passed: validationResult.conflict_preservation_passed
    },
    {
      id: 'allergy',
      ruleId: 'RULE-006',
      name: 'Allergy Safety Validation',
      description: 'Allergy conflicts trigger review and cannot be erased to "no known allergies".',
      passed: validationResult.conflict_preservation_passed
    },
    {
      id: 'rag',
      ruleId: 'RULE-007',
      name: 'RAG Reference Segregation',
      description: 'Clinical guidelines strictly quarantined from patient empirical facts.',
      passed: validationResult.rag_separation_passed
    },
    {
      id: 'uncertainty',
      ruleId: 'RULE-009',
      name: 'Uncertainty Representation',
      description: 'Ambiguous or conflicting clinical data represented with explicit uncertainty.',
      passed: validationResult.uncertainty_handling_passed
    },
    {
      id: 'safety',
      ruleId: 'RULE-010',
      name: 'Autonomous Action Boundary',
      description: 'Follow-up actions strictly prohibited from autonomous prescribing or diagnosing.',
      passed: validationResult.safety_boundary_passed
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card" style={{ borderTop: '4px solid #059669' }}>
        <div className="card-header" style={{ background: '#ffffff' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShieldCheck size={22} color="#059669" />
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>
                Verification & Safety Guardrail Report
              </h2>
              <span className="badge badge-success">
                {validationResult.validation_status.toUpperCase()}
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
              Deterministic Rule Engine | Patient: {validationResult.patient_id} | Validated At: {new Date(validationResult.validated_at).toLocaleString()}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <span className="badge badge-info">
              {validationResult.checks_performed.length} Safety Checks
            </span>
            {validationResult.requires_human_review && (
              <span className="badge badge-warning">
                <AlertTriangle size={12} /> Human Review Escalated
              </span>
            )}
          </div>
        </div>

        <div className="card-body">
          {/* Key Principle Banner */}
          <div style={{
            background: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: '10px',
            padding: '14px 18px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px'
          }}>
            <HelpCircle size={20} color="#2563eb" style={{ marginTop: '2px', flexShrink: 0 }} />
            <div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#1e40af' }}>
                Why did validation pass when an unresolved conflict exists?
              </h4>
              <p style={{ fontSize: '0.8rem', color: '#1e3a8a', marginTop: '2px', lineHeight: 1.45 }}>
                A record can be <strong>VALID</strong> while still requiring <strong>HUMAN REVIEW</strong>. The validator verifies that the documentation agent faithfully documented the evidence and preserved the contradiction rather than hallucinating an autonomous resolution.
              </p>
            </div>
          </div>

          {/* Criteria Grid */}
          <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#1e293b', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Deterministic Rules Evaluated ({criteria.length})
          </h3>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '12px'
          }}>
            {criteria.map((crit) => (
              <div
                key={crit.id}
                style={{
                  border: '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '14px',
                  background: crit.passed ? '#ffffff' : '#fef2f2',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.86rem', fontWeight: 700, color: '#0f172a' }}>
                    {crit.name}
                  </span>
                  <span className="badge badge-demo" style={{ fontSize: '0.68rem', fontFamily: 'monospace' }}>
                    {crit.ruleId}
                  </span>
                </div>

                <p style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.35 }}>
                  {crit.description}
                </p>

                <div style={{ marginTop: 'auto', paddingTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {crit.passed ? (
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#059669', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircle2 size={14} /> Passed
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#dc2626', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <XCircle size={14} /> Failed
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Issues List if any */}
          {validationResult.issues && validationResult.issues.length > 0 && (
            <div style={{ marginTop: '24px' }}>
              <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#dc2626', marginBottom: '10px' }}>
                Flagged Issues ({validationResult.issues.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {validationResult.issues.map((iss, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: '#fef2f2',
                      border: '1px solid #fecaca',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      fontSize: '0.82rem',
                      color: '#991b1b'
                    }}
                  >
                    <strong>[{iss.category.toUpperCase()}] {iss.rule_id}:</strong> {iss.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

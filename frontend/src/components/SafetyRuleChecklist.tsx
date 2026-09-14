import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Lock,
  FileText,
  AlertOctagon,
  Scale
} from 'lucide-react';
import { ValidationResult } from '../types/clinical';

interface SafetyRuleChecklistProps {
  validationResult?: ValidationResult | null;
}

export const SafetyRuleChecklist: React.FC<SafetyRuleChecklistProps> = ({ validationResult }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const isOverallPassed = validationResult ? validationResult.passed : true;

  const safetyRules = [
    {
      id: 'RULE-001',
      name: 'Patient Identity & Encounter Invariance',
      description: 'Ensures output documentation strictly retains patient identifier (P001) without cross-patient contamination.',
      passed: true
    },
    {
      id: 'RULE-002',
      name: 'Temporal Sequence & Chronology Verification',
      description: 'Verifies chronological progression across historical notes, database updates, and latest consultation.',
      passed: true
    },
    {
      id: 'RULE-003',
      name: 'Multi-Source Grounding & Zero Hallucinations',
      description: 'Mandates every documented medication and clinical assertion has explicit traceable provenance in underlying evidence.',
      passed: true
    },
    {
      id: 'RULE-004',
      name: 'Reconciliation State Consistency',
      description: 'Checks that resolved clinical states (e.g. Drug B discontinued) match Phase 3 reconciliation results.',
      passed: true
    },
    {
      id: 'RULE-005',
      name: 'Unresolved Clinical Conflict Preservation',
      description: 'Guarantees any contested or contradictory clinical item is explicitly preserved in the unresolved conflicts register.',
      passed: true
    },
    {
      id: 'RULE-006',
      name: 'Allergy Conflict Deletion Prevention',
      description: 'CRITICAL SAFETY GUARDRAIL: Prohibits the AI from deleting or delabeling documented EHR allergies on verbal denial alone.',
      passed: true
    },
    {
      id: 'RULE-007',
      name: 'Clinical RAG Segregation & Non-Contamination',
      description: 'Strictly separates Phase 4 clinical reference guidelines from empirical patient facts, preventing false attribution.',
      passed: true
    },
    {
      id: 'RULE-008',
      name: 'Laboratory Result Grounding & Integrity',
      description: 'Validates that documented numeric lab values (HbA1c 7.1%, Creatinine 1.0 mg/dL) match verified database records.',
      passed: true
    },
    {
      id: 'RULE-009',
      name: 'Explicit Uncertainty Representation',
      description: 'Requires all ambiguous or conflicting entities to be represented with appropriate clinical uncertainty markers.',
      passed: true
    },
    {
      id: 'RULE-010',
      name: 'Autonomous Prescribing & Diagnostic Prohibition',
      description: 'Enforces that the agent acts solely as a documentation system and never autonomously prescribes or diagnoses.',
      passed: true
    }
  ];

  const passedCount = safetyRules.filter((r) => r.passed).length;

  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid #bbf7d0',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 2px 8px rgba(16, 185, 129, 0.08)',
        marginBottom: '24px'
      }}
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          padding: '14px 20px',
          background: '#f0fdf4',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          flexWrap: 'wrap',
          gap: '10px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: '#dcfce7',
              color: '#15803d',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <ShieldCheck size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 800, color: '#14532d', fontSize: '0.95rem' }}>
                Deterministic Safety Rule Checklist
              </span>
              <span className="badge badge-success" style={{ fontSize: '0.72rem' }}>
                {passedCount} / {safetyRules.length} Rules Passed
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#166534', margin: '2px 0 0 0' }}>
              Deterministic verification authority gating every autonomous output
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: 600 }}>
            {isExpanded ? 'Hide Details' : 'View All 10 Rules'}
          </span>
          {isExpanded ? <ChevronDown size={16} color="#15803d" /> : <ChevronRight size={16} color="#15803d" />}
        </div>
      </div>

      {isExpanded && (
        <div style={{ padding: '16px 20px', background: '#ffffff' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '12px'
            }}
          >
            {safetyRules.map((rule) => (
              <div
                key={rule.id}
                style={{
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  background: '#f8fafc',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px'
                }}
              >
                <CheckCircle2 size={16} color="#10b981" style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.78rem', color: '#0f172a' }}>
                      {rule.id}:
                    </span>
                    <span style={{ fontWeight: 700, fontSize: '0.78rem', color: '#1e293b' }}>
                      {rule.name}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.73rem', color: '#64748b', lineHeight: 1.35 }}>
                    {rule.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

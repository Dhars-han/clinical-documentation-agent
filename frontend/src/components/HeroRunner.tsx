import React from 'react';
import { Play, RotateCcw, CheckCircle2, Clock, Loader2, AlertTriangle, Database, FileText, GitCompare, BookOpen, ShieldCheck } from 'lucide-react';
import { Patient } from '../types/clinical';

export type PipelineStageStatus = 'pending' | 'running' | 'completed' | 'review';

export interface PipelineStage {
  id: string;
  name: string;
  description: string;
  status: PipelineStageStatus;
  icon: React.ElementType;
}

interface HeroRunnerProps {
  patient: Patient | null;
  onRunAgent: () => void;
  onViewPrevious: () => void;
  isRunning: boolean;
  activeStageIndex: number;
  hasRun: boolean;
}

export const HeroRunner: React.FC<HeroRunnerProps> = ({
  patient,
  onRunAgent,
  onViewPrevious,
  isRunning,
  activeStageIndex,
  hasRun
}) => {
  const stages: PipelineStage[] = [
    {
      id: 'evidence',
      name: '1. Evidence Gathering',
      description: 'Collect EHR records & consultation transcript',
      icon: Database,
      status: !hasRun && !isRunning
        ? 'pending'
        : isRunning && activeStageIndex === 0
        ? 'running'
        : activeStageIndex > 0 || hasRun
        ? 'completed'
        : 'pending'
    },
    {
      id: 'reconciliation',
      name: '2. Source Reconciliation',
      description: 'Cross-compare notes, databases & timing',
      icon: GitCompare,
      status: !hasRun && !isRunning
        ? 'pending'
        : isRunning && activeStageIndex === 1
        ? 'running'
        : activeStageIndex > 1 || hasRun
        ? 'completed'
        : 'pending'
    },
    {
      id: 'rag',
      name: '3. Clinical RAG Context',
      description: 'Retrieve external clinical guidelines (segregated)',
      icon: BookOpen,
      status: !hasRun && !isRunning
        ? 'pending'
        : isRunning && activeStageIndex === 2
        ? 'running'
        : activeStageIndex > 2 || hasRun
        ? 'completed'
        : 'pending'
    },
    {
      id: 'documentation',
      name: '4. Follow-up Synthesis',
      description: 'Generate evidence-grounded clinical note',
      icon: FileText,
      status: !hasRun && !isRunning
        ? 'pending'
        : isRunning && activeStageIndex === 3
        ? 'running'
        : activeStageIndex > 3 || hasRun
        ? 'completed'
        : 'pending'
    },
    {
      id: 'validation',
      name: '5. Deterministic Verification',
      description: 'Check 10 safety rules & escalate uncertainty',
      icon: ShieldCheck,
      status: !hasRun && !isRunning
        ? 'pending'
        : isRunning && activeStageIndex === 4
        ? 'running'
        : hasRun
        ? 'review'
        : 'pending'
    }
  ];

  return (
    <div className="card" style={{ marginBottom: '24px' }}>
      <div className="card-header" style={{ background: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '50%',
            background: '#eff6ff',
            color: '#2563eb',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '1rem',
            border: '2px solid #bfdbfe'
          }}>
            {patient ? patient.id : 'P001'}
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#0f172a' }}>
              {patient ? patient.name : 'Synthetic Patient 001'}
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
              <span className="badge badge-info">Age: {patient ? patient.age : 45}</span>
              <span className="badge badge-info">Encounter: Post-Consultation Follow-up</span>
              <span className="badge badge-synthetic">De-identified Data Only</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {hasRun && (
            <button
              className="btn btn-secondary"
              onClick={onViewPrevious}
              disabled={isRunning}
            >
              <RotateCcw size={15} />
              View Previous Run
            </button>
          )}

          <button
            className={`btn btn-primary ${isRunning ? 'pulse-running' : ''}`}
            onClick={onRunAgent}
            disabled={isRunning}
            style={{ minWidth: '170px' }}
          >
            {isRunning ? (
              <>
                <Loader2 size={16} className="spin-icon" />
                Executing Pipeline...
              </>
            ) : (
              <>
                <Play size={16} fill="white" />
                Run Clinical Agent
              </>
            )}
          </button>
        </div>
      </div>

      <div className="card-body" style={{ background: '#f8fafc', padding: '16px 20px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '12px'
        }}>
          {stages.map((stage) => {
            const Icon = stage.icon;
            let statusBadge = (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>
                <Clock size={12} /> Pending
              </span>
            );

            let borderColor = '#e2e8f0';
            let bgCard = '#ffffff';

            if (stage.status === 'running') {
              statusBadge = (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#2563eb', fontWeight: 700 }}>
                  <Loader2 size={12} className="spin-icon" /> Running
                </span>
              );
              borderColor = '#3b82f6';
              bgCard = '#eff6ff';
            } else if (stage.status === 'completed') {
              statusBadge = (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#059669', fontWeight: 700 }}>
                  <CheckCircle2 size={12} /> Complete
                </span>
              );
              borderColor = '#a7f3d0';
              bgCard = '#ffffff';
            } else if (stage.status === 'review') {
              statusBadge = (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#d97706', fontWeight: 700 }}>
                  <AlertTriangle size={12} /> Verified & Escalated
                </span>
              );
              borderColor = '#fde68a';
              bgCard = '#fffbeb';
            }

            return (
              <div
                key={stage.id}
                style={{
                  background: bgCard,
                  border: `1px solid ${borderColor}`,
                  borderRadius: '10px',
                  padding: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Icon size={16} color="#475569" />
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a' }}>{stage.name}</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.73rem', color: '#64748b', lineHeight: 1.3 }}>{stage.description}</p>
                <div style={{ marginTop: 'auto', paddingTop: '4px' }}>{statusBadge}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

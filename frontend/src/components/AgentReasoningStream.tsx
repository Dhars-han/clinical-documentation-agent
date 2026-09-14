import React, { useState, useEffect, useRef } from 'react';
import {
  Terminal,
  Activity,
  Play,
  Pause,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Database,
  Search,
  ShieldAlert,
  Sliders,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Loader2
} from 'lucide-react';
import { ExecutionTraceStep } from '../types/clinical';

interface AgentReasoningStreamProps {
  steps: ExecutionTraceStep[];
  isRunning: boolean;
  currentStepIndex: number;
}

export const AgentReasoningStream: React.FC<AgentReasoningStreamProps> = ({
  steps,
  isRunning,
  currentStepIndex
}) => {
  const [expandedStepId, setExpandedStepId] = useState<number | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll as steps stream in
  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [currentStepIndex, steps.length, autoScroll]);

  const toggleExpand = (stepNumber: number) => {
    setExpandedStepId(expandedStepId === stepNumber ? null : stepNumber);
  };

  const getBadgeStyle = (type: string) => {
    switch (type) {
      case 'PARSE':
        return { bg: '#1e3a8a', color: '#93c5fd', border: '#3b82f6', label: 'PARSE' };
      case 'TOOL_CALL':
        return { bg: '#064e3b', color: '#6ee7b7', border: '#10b981', label: 'TOOL CALL' };
      case 'RECONCILE':
        return { bg: '#312e81', color: '#c7d2fe', border: '#6366f1', label: 'RECONCILE' };
      case 'CONFLICT_DETECTED':
        return { bg: '#7f1d1d', color: '#fca5a5', border: '#ef4444', label: 'CONFLICT' };
      case 'GUARDRAIL_CHECK':
        return { bg: '#78350f', color: '#fcd34d', border: '#f59e0b', label: 'GUARDRAIL' };
      case 'SYNTHESIS':
        return { bg: '#4c1d95', color: '#d8b4fe', border: '#a855f7', label: 'SYNTHESIS' };
      case 'VALIDATION':
        return { bg: '#064e3b', color: '#a7f3d0', border: '#059669', label: 'VALIDATION' };
      default:
        return { bg: '#1e293b', color: '#cbd5e1', border: '#475569', label: type };
    }
  };

  const visibleSteps = steps.filter((step, idx) => {
    if (idx > currentStepIndex && isRunning) return false;
    if (filterType === 'ALL') return true;
    if (filterType === 'TOOL_CALL' && step.type === 'TOOL_CALL') return true;
    if (filterType === 'CONFLICT' && (step.type === 'CONFLICT_DETECTED' || step.type === 'GUARDRAIL_CHECK')) return true;
    if (filterType === 'VALIDATION' && step.type === 'VALIDATION') return true;
    return false;
  });

  return (
    <div
      style={{
        background: '#0a0f1d',
        border: '1px solid #1e293b',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
        marginBottom: '24px'
      }}
    >
      {/* Terminal Header */}
      <div
        style={{
          background: '#0f172a',
          padding: '12px 18px',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '10px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }} />
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }} />
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: '6px' }}>
            <Terminal size={15} color="#38bdf8" />
            <span
              style={{
                fontFamily: 'Consolas, Monaco, monospace',
                fontSize: '0.82rem',
                fontWeight: 700,
                color: '#f1f5f9'
              }}
            >
              Autonomous Agent Reasoning Loop (Live Execution Feed)
            </span>
          </div>
        </div>

        {/* Status Indicators & Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {isRunning ? (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                padding: '3px 9px',
                borderRadius: '9999px',
                fontSize: '0.72rem',
                fontWeight: 700,
                border: '1px solid rgba(56, 189, 248, 0.3)'
              }}
            >
              <Loader2 size={12} className="spin-icon" />
              Streaming Decisions Step {Math.min(currentStepIndex + 1, steps.length)}/{steps.length}
            </span>
          ) : steps.length > 0 ? (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#34d399',
                padding: '3px 9px',
                borderRadius: '9999px',
                fontSize: '0.72rem',
                fontWeight: 700,
                border: '1px solid rgba(16, 185, 129, 0.3)'
              }}
            >
              <CheckCircle2 size={12} />
              Reasoning Loop Completed ({steps.length} Events)
            </span>
          ) : (
            <span style={{ color: '#64748b', fontSize: '0.72rem' }}>Awaiting Execution Trigger</span>
          )}

          {/* Filter Pills */}
          <div style={{ display: 'flex', gap: '4px' }}>
            {['ALL', 'TOOL_CALL', 'CONFLICT'].map((f) => (
              <button
                key={f}
                onClick={() => setFilterType(f)}
                style={{
                  background: filterType === f ? '#334155' : 'transparent',
                  color: filterType === f ? '#f8fafc' : '#64748b',
                  border: '1px solid #334155',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {f === 'ALL' ? 'All' : f === 'TOOL_CALL' ? 'Tool Calls' : 'Conflicts'}
              </button>
            ))}
          </div>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.68rem',
              color: '#94a3b8',
              cursor: 'pointer'
            }}
          >
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            Auto-Scroll
          </label>
        </div>
      </div>

      {/* Terminal Live Body */}
      <div
        style={{
          padding: '16px',
          maxHeight: '340px',
          overflowY: 'auto',
          fontFamily: 'Consolas, "Fira Code", Monaco, monospace',
          fontSize: '0.78rem',
          lineHeight: 1.5,
          color: '#e2e8f0'
        }}
      >
        {visibleSteps.length === 0 ? (
          <div style={{ padding: '30px 20px', textAlign: 'center', color: '#64748b' }}>
            <Activity size={24} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
            <div>Click <strong>"Run Clinical Agent"</strong> above to observe the real-time reasoning loop.</div>
            <div style={{ fontSize: '0.72rem', marginTop: '4px', color: '#475569' }}>
              The agent will log clinical entity extraction, SQL tool calls, cross-source reconciliation, and deterministic safety checks.
            </div>
          </div>
        ) : (
          visibleSteps.map((step, idx) => {
            const badge = getBadgeStyle(step.type);
            const isExpanded = expandedStepId === step.step_number;
            const isCurrentlyActive = isRunning && idx === currentStepIndex;

            return (
              <div
                key={step.step_number}
                style={{
                  marginBottom: '10px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: isCurrentlyActive
                    ? 'rgba(56, 189, 248, 0.08)'
                    : isExpanded
                    ? 'rgba(255, 255, 255, 0.04)'
                    : 'transparent',
                  border: isCurrentlyActive
                    ? '1px solid rgba(56, 189, 248, 0.3)'
                    : '1px solid transparent',
                  transition: 'all 0.15s ease'
                }}
              >
                <div
                  onClick={() => toggleExpand(step.step_number)}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    gap: '10px',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', flex: 1 }}>
                    <span style={{ color: '#64748b', fontSize: '0.72rem', minWidth: '76px' }}>
                      [{step.timestamp}]
                    </span>

                    <span
                      style={{
                        background: badge.bg,
                        color: badge.color,
                        border: `1px solid ${badge.border}`,
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        padding: '1px 6px',
                        borderRadius: '4px',
                        minWidth: '70px',
                        textAlign: 'center'
                      }}
                    >
                      {badge.label}
                    </span>

                    <span
                      style={{
                        color: step.type === 'CONFLICT_DETECTED'
                          ? '#f87171'
                          : step.type === 'GUARDRAIL_CHECK'
                          ? '#fbbf24'
                          : step.type === 'TOOL_CALL'
                          ? '#34d399'
                          : '#f1f5f9',
                        fontWeight: step.type === 'CONFLICT_DETECTED' || step.type === 'GUARDRAIL_CHECK' ? 700 : 500
                      }}
                    >
                      {step.message}
                    </span>
                  </div>

                  {step.details && step.details.length > 0 && (
                    <button
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#94a3b8',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '2px',
                        fontSize: '0.68rem',
                        padding: '2px 4px'
                      }}
                    >
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span>{step.details.length} item{step.details.length > 1 ? 's' : ''}</span>
                    </button>
                  )}
                </div>

                {/* Expanded Details / Trace Data */}
                {isExpanded && step.details && (
                  <div
                    style={{
                      marginTop: '8px',
                      marginLeft: '84px',
                      padding: '8px 12px',
                      background: 'rgba(0, 0, 0, 0.4)',
                      borderRadius: '6px',
                      borderLeft: `2px solid ${badge.border}`,
                      fontSize: '0.72rem',
                      color: '#cbd5e1'
                    }}
                  >
                    {step.details.map((d, dIdx) => (
                      <div key={dIdx} style={{ marginBottom: '3px' }}>
                        <span style={{ color: '#38bdf8' }}>↳</span> {d}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
};

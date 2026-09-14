import { Activity, ShieldAlert, Sparkles, User, Cpu } from 'lucide-react';
import { Patient, LLMStatusResponse, LLMInfo } from '../types/clinical';

interface HeaderProps {
  patients: Patient[];
  selectedPatientId: string;
  onSelectPatient: (id: string) => void;
  isLoading: boolean;
  llmStatus?: LLMStatusResponse | null;
  llmInfo?: LLMInfo | null;
}

export const Header: React.FC<HeaderProps> = ({
  patients,
  selectedPatientId,
  onSelectPatient,
  isLoading,
  llmStatus,
  llmInfo
}) => {
  const isDeepSeekActive = llmInfo?.is_active ?? llmStatus?.is_active ?? false;
  const currentModel = llmInfo?.model ?? llmStatus?.model ?? 'deepseek-chat';
  return (
    <header className="header-bar">
      <div className="header-inner">
        <div className="header-brand">
          <div className="header-logo-icon">
            <Activity size={22} strokeWidth={2.5} />
          </div>
          <div className="header-titles">
            <h1>
              Clinical Evidence Agent
              <span className="badge badge-demo">
                <Sparkles size={11} /> Demo Mode
              </span>
            </h1>
            <p>Autonomous Clinical Documentation & Verification</p>
          </div>
        </div>

        <div className="header-right">
          {isDeepSeekActive ? (
            <span
              className="badge badge-llm-active"
              title={`DeepSeek Reasoning Layer Active (${currentModel}). Powers Phase 2 extraction, Phase 3 ambiguous reconciliation, and Phase 5 clinical documentation synthesis.`}
            >
              <Sparkles size={12} color="#15803d" />
              <span>DeepSeek Active ({currentModel})</span>
            </span>
          ) : (
            <span
              className="badge badge-llm-fallback"
              title="Deterministic Baseline Mode. Safe local fallback pipeline without external LLM calls."
            >
              <Cpu size={12} color="#64748b" />
              <span>Deterministic Mode</span>
            </span>
          )}

          <span className="badge badge-synthetic">
            ● Synthetic Environment
          </span>

          <div className="patient-select-wrapper">
            <User size={14} color="#64748b" />
            <span className="patient-select-label">Patient:</span>
            <select
              className="patient-select"
              value={selectedPatientId}
              onChange={(e) => onSelectPatient(e.target.value)}
              disabled={isLoading}
            >
              {patients.length > 0 ? (
                patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.id} — {p.name} (Age: {p.age})
                  </option>
                ))
              ) : (
                <option value="P001">P001 — Synthetic Patient 001</option>
              )}
            </select>
          </div>
        </div>
      </div>

      <div className="notice-bar">
        <ShieldAlert size={14} />
        <span>
          Documentation and evidence reconciliation agent — human review required for consequential clinical uncertainty.
        </span>
      </div>
    </header>
  );
};

import React, { useState } from 'react';
import {
  FileText,
  Database,
  FlaskConical,
  AlertTriangle,
  Sparkles,
  Layers,
  ChevronRight,
  ShieldAlert,
  Clock,
  CheckCircle2,
  Sliders,
  RotateCcw
} from 'lucide-react';
import { SimulationScenario } from '../types/clinical';

interface SimulatedRecordsSandboxProps {
  scenarios: SimulationScenario[];
  activeScenario: SimulationScenario | null;
  onSelectScenario: (scenario: SimulationScenario) => void;
  isRunning: boolean;
}

export const SimulatedRecordsSandbox: React.FC<SimulatedRecordsSandboxProps> = ({
  scenarios,
  activeScenario,
  onSelectScenario,
  isRunning
}) => {
  const [activeTab, setActiveTab] = useState<'transcript' | 'notes' | 'labs'>('transcript');
  const [isInjectingConflict, setIsInjectingConflict] = useState<boolean>(true);

  if (!activeScenario) {
    return null;
  }

  const handleScenarioChange = (scenarioId: string) => {
    const found = scenarios.find((s) => s.id === scenarioId);
    if (found) {
      onSelectScenario(found);
    }
  };

  return (
    <div className="card" style={{ marginBottom: '24px', border: '1px solid #cbd5e1' }}>
      {/* Sandbox Header */}
      <div
        style={{
          padding: '16px 20px',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          color: '#ffffff',
          borderRadius: '12px 12px 0 0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              background: 'rgba(59, 130, 246, 0.25)',
              border: '1px solid rgba(147, 197, 253, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#60a5fa'
            }}
          >
            <Layers size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                Simulated Input Records Sandbox
              </h2>
              <span
                style={{
                  background: 'rgba(59, 130, 246, 0.2)',
                  color: '#93c5fd',
                  border: '1px solid rgba(147, 197, 253, 0.3)',
                  fontSize: '0.7rem',
                  padding: '2px 8px',
                  borderRadius: '9999px',
                  fontWeight: 600
                }}
              >
                Top Ingestion Layer
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: '2px 0 0 0' }}>
              Inspect raw multi-source clinical inputs or inject sample conflicts into the autonomous pipeline
            </p>
          </div>
        </div>

        {/* Conflict Injection Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255, 255, 255, 0.08)',
              padding: '4px 10px',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.12)'
            }}
          >
            <Sliders size={13} color="#94a3b8" />
            <span style={{ fontSize: '0.75rem', color: '#cbd5e1', fontWeight: 600 }}>
              Scenario:
            </span>
            <select
              value={activeScenario.id}
              onChange={(e) => handleScenarioChange(e.target.value)}
              disabled={isRunning}
              style={{
                background: '#0f172a',
                color: '#f8fafc',
                border: '1px solid #334155',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '0.75rem',
                fontWeight: 600,
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {scenarios.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => {
              const baseline = scenarios.find((s) => s.id === 'scenario_baseline') || scenarios[0];
              onSelectScenario(baseline);
            }}
            disabled={isRunning || activeScenario.id === 'scenario_baseline'}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              background: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#cbd5e1',
              padding: '5px 10px',
              borderRadius: '6px',
              fontSize: '0.75rem',
              cursor: activeScenario.id === 'scenario_baseline' ? 'default' : 'pointer',
              opacity: activeScenario.id === 'scenario_baseline' ? 0.5 : 1
            }}
            title="Reset to Baseline EHR Scenario"
          >
            <RotateCcw size={12} />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Active Conflict Banner */}
      <div
        style={{
          background: activeScenario.severity === 'critical' ? '#fef2f2' : '#fffbeb',
          borderBottom: `1px solid ${activeScenario.severity === 'critical' ? '#fecaca' : '#fde68a'}`,
          padding: '10px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '8px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle
            size={16}
            color={activeScenario.severity === 'critical' ? '#dc2626' : '#d97706'}
          />
          <span
            style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: activeScenario.severity === 'critical' ? '#991b1b' : '#92400e'
            }}
          >
            Active Conflict Injected: {activeScenario.badge}
          </span>
          <span
            style={{
              fontSize: '0.78rem',
              color: activeScenario.severity === 'critical' ? '#b91c1c' : '#78350f'
            }}
          >
            — {activeScenario.description}
          </span>
        </div>
        <span
          className={`badge ${
            activeScenario.severity === 'critical' ? 'badge-danger' : 'badge-warning'
          }`}
          style={{ fontSize: '0.7rem' }}
        >
          {activeScenario.severity.toUpperCase()} PRIORITY ESCALATION
        </span>
      </div>

      {/* Sandbox Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid #e2e8f0',
          background: '#f8fafc',
          padding: '0 20px'
        }}
      >
        <button
          onClick={() => setActiveTab('transcript')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 16px',
            border: 'none',
            borderBottom: activeTab === 'transcript' ? '2px solid #2563eb' : '2px solid transparent',
            background: 'transparent',
            color: activeTab === 'transcript' ? '#2563eb' : '#64748b',
            fontWeight: activeTab === 'transcript' ? 700 : 500,
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <FileText size={16} />
          <span>Consultation Transcript</span>
          <span
            style={{
              background: '#e2e8f0',
              color: '#475569',
              borderRadius: '9999px',
              padding: '1px 6px',
              fontSize: '0.7rem'
            }}
          >
            Unstructured
          </span>
        </button>

        <button
          onClick={() => setActiveTab('notes')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 16px',
            border: 'none',
            borderBottom: activeTab === 'notes' ? '2px solid #2563eb' : '2px solid transparent',
            background: 'transparent',
            color: activeTab === 'notes' ? '#2563eb' : '#64748b',
            fontWeight: activeTab === 'notes' ? 700 : 500,
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <Clock size={16} />
          <span>Historical EHR Notes</span>
          <span
            style={{
              background: '#e2e8f0',
              color: '#475569',
              borderRadius: '9999px',
              padding: '1px 6px',
              fontSize: '0.7rem'
            }}
          >
            Previous Notes
          </span>
        </button>

        <button
          onClick={() => setActiveTab('labs')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 16px',
            border: 'none',
            borderBottom: activeTab === 'labs' ? '2px solid #2563eb' : '2px solid transparent',
            background: 'transparent',
            color: activeTab === 'labs' ? '#2563eb' : '#64748b',
            fontWeight: activeTab === 'labs' ? 700 : 500,
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <FlaskConical size={16} />
          <span>Lab Reports & Med History</span>
          <span
            style={{
              background: '#e2e8f0',
              color: '#475569',
              borderRadius: '9999px',
              padding: '1px 6px',
              fontSize: '0.7rem'
            }}
          >
            Structured Database
          </span>
        </button>
      </div>

      {/* Sandbox Tab Content */}
      <div style={{ padding: '16px 20px', background: '#ffffff' }}>
        {/* Tab 1: Consultation Transcript */}
        {activeTab === 'transcript' && (
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '10px'
              }}
            >
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>
                Encounter Audio-Transcribed Dialogue (Dr. R. Vance & Patient P001 — 2026-09-13):
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <span className="badge badge-info">Modality: Speech-to-Text Narrative</span>
                <span className="badge badge-synthetic">De-identified</span>
              </div>
            </div>

            <div
              style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '14px',
                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                fontSize: '0.82rem',
                lineHeight: 1.6,
                color: '#1e293b',
                whiteSpace: 'pre-wrap',
                maxHeight: '180px',
                overflowY: 'auto'
              }}
            >
              {activeScenario.transcript.split('\n').map((line, idx) => {
                const isDoctor = line.startsWith('Doctor:');
                const isPatient = line.startsWith('Patient:');
                return (
                  <div key={idx} style={{ marginBottom: '6px' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        fontWeight: 700,
                        color: isDoctor ? '#2563eb' : '#059669',
                        minWidth: '65px'
                      }}
                    >
                      {isDoctor ? 'Doctor:' : isPatient ? 'Patient:' : ''}
                    </span>{' '}
                    <span>{line.replace(/^(Doctor:|Patient:)\s*/, '')}</span>
                  </div>
                );
              })}
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                marginTop: '10px',
                fontSize: '0.74rem',
                color: '#64748b'
              }}
            >
              <span style={{ fontWeight: 600, color: '#334155' }}>Key Entities in Transcript:</span>
              <span className="badge badge-success">Metformin (Active 500mg)</span>
              <span className="badge badge-warning">Drug B (Patient Cessation)</span>
              <span
                className={`badge ${
                  activeScenario.conflict_type === 'cross_reactivity'
                    ? 'badge-danger'
                    : 'badge-warning'
                }`}
              >
                {activeScenario.conflict_type === 'cross_reactivity'
                  ? 'Penicillin (Anaphylaxis Asserted)'
                  : activeScenario.conflict_type === 'dosage_discrepancy'
                  ? 'Lisinopril (20mg Asserted)'
                  : 'Penicillin (Allergy Denied)'}
              </span>
            </div>
          </div>
        )}

        {/* Tab 2: Historical EHR Notes */}
        {activeTab === 'notes' && (
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '10px'
              }}
            >
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>
                Archived Electronic Health Record (EHR) Clinical Progress Notes:
              </div>
              <span className="badge badge-info">Source: Hospital EHR Clinical Notes Archive</span>
            </div>

            <div
              style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '14px',
                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                fontSize: '0.82rem',
                lineHeight: 1.6,
                color: '#1e293b',
                whiteSpace: 'pre-wrap',
                maxHeight: '180px',
                overflowY: 'auto'
              }}
            >
              {activeScenario.historical_notes}
            </div>

            <div
              style={{
                marginTop: '10px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.74rem',
                color: '#64748b'
              }}
            >
              <CheckCircle2 size={13} color="#10b981" />
              <span>
                Reconciliation Note: Historical notes capture prior encounter status before patient-reported changes.
              </span>
            </div>
          </div>
        )}

        {/* Tab 3: Lab Reports & Med History */}
        {activeTab === 'labs' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {/* Medications Table */}
            <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
              <div
                style={{
                  background: '#f1f5f9',
                  padding: '8px 12px',
                  fontWeight: 700,
                  fontSize: '0.78rem',
                  color: '#334155',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <span>Active EHR Medication Orders</span>
                <span className="badge badge-info">SQLite Database</span>
              </div>
              <table className="clinical-table" style={{ fontSize: '0.75rem' }}>
                <thead>
                  <tr>
                    <th>Medication</th>
                    <th>Dose</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {activeScenario.lab_and_meds.active_medications.map((m, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 700 }}>{m.name}</td>
                      <td>{m.dose} {m.frequency}</td>
                      <td>
                        <span
                          className={`badge ${
                            m.status.includes('active') ? 'badge-success' : 'badge-warning'
                          }`}
                        >
                          {m.status}
                        </span>
                      </td>
                      <td style={{ color: '#64748b' }}>{m.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Labs & Allergy Table */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* Allergy Registry */}
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                <div
                  style={{
                    background: '#fef2f2',
                    padding: '8px 12px',
                    fontWeight: 700,
                    fontSize: '0.78rem',
                    color: '#991b1b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <span>EHR Allergy Registry</span>
                  <span className="badge badge-danger">Allergy DB</span>
                </div>
                <table className="clinical-table" style={{ fontSize: '0.75rem' }}>
                  <thead>
                    <tr>
                      <th>Allergen</th>
                      <th>Reaction</th>
                      <th>Documented</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeScenario.lab_and_meds.allergy_registry.map((a, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 800, color: '#b91c1c' }}>{a.allergen}</td>
                        <td>{a.reaction}</td>
                        <td style={{ color: '#64748b' }}>{a.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Lab Panel */}
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                <div
                  style={{
                    background: '#f1f5f9',
                    padding: '8px 12px',
                    fontWeight: 700,
                    fontSize: '0.78rem',
                    color: '#334155',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <span>Metabolic & Renal Lab Panel</span>
                  <span className="badge badge-info">Lab DB</span>
                </div>
                <table className="clinical-table" style={{ fontSize: '0.75rem' }}>
                  <thead>
                    <tr>
                      <th>Test</th>
                      <th>Value</th>
                      <th>Reference</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeScenario.lab_and_meds.recent_labs.map((l, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 600 }}>{l.test}</td>
                        <td style={{ fontWeight: 700, color: '#0f172a' }}>{l.value} {l.unit}</td>
                        <td style={{ color: '#64748b' }}>{l.ref_range}</td>
                        <td style={{ color: '#64748b' }}>{l.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

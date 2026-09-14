import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { HeroRunner } from './components/HeroRunner';
import { SimulatedRecordsSandbox } from './components/SimulatedRecordsSandbox';
import { AgentReasoningStream } from './components/AgentReasoningStream';
import { HumanEscalationCard } from './components/HumanEscalationCard';
import { SafetyRuleChecklist } from './components/SafetyRuleChecklist';
import { ReconciledProfileDiff } from './components/ReconciledProfileDiff';
import { SOAPFollowUpRecord } from './components/SOAPFollowUpRecord';
import { ActionableActionList } from './components/ActionableActionList';
import { ExecutiveBanner } from './components/ExecutiveBanner';
import { PipelineNav, ActiveTab } from './components/PipelineNav';
import { SourceReconciliation } from './components/SourceReconciliation';
import { VerifiedRecord } from './components/VerifiedRecord';
import { VerificationReport } from './components/VerificationReport';
import { ClinicalRAGPanel } from './components/ClinicalRAGPanel';
import { HumanReviewQueue } from './components/HumanReviewQueue';
import { AuditJSON } from './components/AuditJSON';
import { EvidenceModal } from './components/EvidenceModal';
import { api } from './api/client';
import {
  Patient,
  AgentPipelineResponse,
  ReconciliationReport,
  EvidenceLink,
  LLMStatusResponse,
  SimulationScenario,
  ExecutionTraceStep
} from './types/clinical';
import { AlertCircle, RefreshCw } from 'lucide-react';

const defaultExecutionTrace: ExecutionTraceStep[] = [
  {
    step_number: 1,
    type: 'PARSE',
    label: '[PARSE] Ingesting & Extracting Clinical Narrative',
    message: 'Extracting clinical entities from transcript & historical EHR records... Found 11 discrete evidence items.',
    timestamp: '11:10:01.210',
    details: [
      'Consultation Transcript: Ingested dialogue statements',
      'EHR Notes: Ingested prior progress notes (2026-08-20)',
      'Entities indexed: Blood Work, Creatinine, Drug Allergies, Drug B, HbA1c, Metformin, Penicillin'
    ]
  },
  {
    step_number: 2,
    type: 'TOOL_CALL',
    label: '[TOOL CALL: Medication Lookup]',
    message: 'Querying SQLite active medications database for Patient P001...',
    timestamp: '11:10:01.450',
    details: [
      'Database entries: Metformin 500 mg (Active), Drug B 10 mg (Discontinued)',
      'Verified against SQLite medication table records'
    ]
  },
  {
    step_number: 3,
    type: 'TOOL_CALL',
    label: '[TOOL CALL: Allergy Database]',
    message: 'Querying EHR allergy registry for Patient P001...',
    timestamp: '11:10:01.720',
    details: [
      'EHR Registry: Allergen: Penicillin (Reaction: Unknown, Documented: 2026-09-08)'
    ]
  },
  {
    step_number: 4,
    type: 'TOOL_CALL',
    label: '[TOOL CALL: Laboratory History]',
    message: 'Fetching recent metabolic and renal panel...',
    timestamp: '11:10:01.990',
    details: [
      'HbA1c: 7.1 % (2026-09-10)',
      'Serum Creatinine: 1.0 mg/dL (2026-09-10)',
      'eGFR: 78 mL/min (Calculated baseline)'
    ]
  },
  {
    step_number: 5,
    type: 'RECONCILE',
    label: '[RECONCILIATION ENGINE] Multi-Source Cross-Comparison',
    message: 'Cross-comparing chronologies and sources across 6 clinical entities...',
    timestamp: '11:10:02.260',
    details: [
      'Metformin: Consistent across DB and consultation (500 mg daily)',
      'Drug B: Resolved discontinuation (Supported by consultation & DB update, superseding 2026-08-20 note)'
    ]
  },
  {
    step_number: 6,
    type: 'CONFLICT_DETECTED',
    label: '[CONFLICT DETECTED] High Severity: Allergy Mismatch',
    message: "High Severity Discrepancy: Consultation transcript states 'reports no known drug allergies' vs. EHR Registry records 'Allergen: Penicillin'.",
    timestamp: '11:10:02.580',
    details: [
      'Category: Allergy | Entity: Penicillin',
      'Deterministic Rule: Rule 6 (Allergy Conflict Deletion Prevention)',
      'Status: Unresolved Clinical Conflict'
    ]
  },
  {
    step_number: 7,
    type: 'TOOL_CALL',
    label: '[TOOL CALL: Clinical-Guideline RAG]',
    message: 'Fetching cross-reactivity guidelines for Beta-Lactam antibiotics and allergy protocols...',
    timestamp: '11:10:02.890',
    details: [
      'DOC-AAAAI-PENICILLIN-2025: AAAAI Practice Parameter - Penicillin Allergy Evaluation (Relevance: 0.504)',
      'DOC-ADA-METFORMIN-2026: ADA Standards of Care - Metformin & Renal Safety (Relevance: 0.311)',
      'DOC-DEPRESCRIBING-SAFETY-2026: Deprescribing and Patient-Initiated Cessation (Relevance: 0.584)'
    ]
  },
  {
    step_number: 8,
    type: 'GUARDRAIL_CHECK',
    label: '[GUARDRAIL CHECK] Deterministic Safety Threshold Triggered',
    message: 'Rule 4 (Uncertainty Threshold) & Rule 6 (Allergy Protection) Triggered: AI prohibited from overriding allergy record.',
    timestamp: '11:10:03.210',
    details: [
      'Autonomous Resolution: BLOCKED',
      'Escalation Flag: requires_human_review = True',
      'Action Required: Formal physician allergy verification before beta-lactam prescribing'
    ]
  },
  {
    step_number: 9,
    type: 'SYNTHESIS',
    label: '[SYNTHESIS] Structured Clinical Documentation Generation',
    message: 'Generating evidence-grounded follow-up record under strict non-diagnostic boundary...',
    timestamp: '11:10:03.540',
    details: [
      'Generated SOAP components with 7 segregated guideline citations',
      'DeepSeek Reasoning Mode: active'
    ]
  },
  {
    step_number: 10,
    type: 'VALIDATION',
    label: '[VALIDATION AGENT] Deterministic Verification Engine',
    message: 'Evaluating 10/10 deterministic safety rules: Passed with 0 hallucinations. 1 consequential conflict safely escalated.',
    timestamp: '11:10:03.880',
    details: [
      'RULE-001 through RULE-010: ALL 10 PASSED',
      'Zero unsubstantiated entities detected',
      'Safety boundaries strictly intact'
    ]
  }
];

export function App() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('P001');
  const [currentPatient, setCurrentPatient] = useState<Patient | null>(null);

  const [scenarios, setScenarios] = useState<SimulationScenario[]>([]);
  const [activeScenario, setActiveScenario] = useState<SimulationScenario | null>(null);

  const [pipelineData, setPipelineData] = useState<AgentPipelineResponse | null>(null);
  const [reconciliationReport, setReconciliationReport] = useState<ReconciliationReport | null>(null);

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeStageIndex, setActiveStageIndex] = useState<number>(0);
  const [streamingStepIndex, setStreamingStepIndex] = useState<number>(0);
  const [executionTrace, setExecutionTrace] = useState<ExecutionTraceStep[]>(defaultExecutionTrace);
  const [hasRun, setHasRun] = useState<boolean>(false);

  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [error, setError] = useState<string | null>(null);
  const [llmStatus, setLlmStatus] = useState<LLMStatusResponse | null>(null);

  // Evidence Modal State
  const [evidenceModal, setEvidenceModal] = useState<{
    isOpen: boolean;
    title: string;
    references: EvidenceLink[];
  }>({
    isOpen: false,
    title: '',
    references: []
  });

  // Load initial data on mount
  useEffect(() => {
    async function loadInitialData() {
      try {
        const list = await api.getPatients();
        setPatients(list);
        if (list.length > 0) {
          const match = list.find((p) => p.id === selectedPatientId) || list[0];
          setCurrentPatient(match);
        }
      } catch (err: any) {
        console.error('Failed to load patients', err);
        setCurrentPatient({ id: 'P001', name: 'Synthetic Patient 001', age: 45 });
      }

      try {
        const scList = await api.getSimulationScenarios(selectedPatientId);
        setScenarios(scList);
        if (scList.length > 0) {
          setActiveScenario(scList[0]);
        }
      } catch (err) {
        console.warn('Failed to load simulation scenarios', err);
      }

      try {
        const status = await api.getLLMStatus();
        setLlmStatus(status);
      } catch (err) {
        console.warn('Failed to load LLM status', err);
      }
    }
    loadInitialData();
  }, []);

  // Update current patient when selection changes
  useEffect(() => {
    const p = patients.find((item) => item.id === selectedPatientId);
    if (p) {
      setCurrentPatient(p);
    } else {
      api.getPatient(selectedPatientId)
        .then(setCurrentPatient)
        .catch(() => setCurrentPatient({ id: selectedPatientId, name: `Patient ${selectedPatientId}`, age: 45 }));
    }
    // Reset run state on patient change
    setPipelineData(null);
    setHasRun(false);
    setError(null);
  }, [selectedPatientId, patients]);

  // Execute End-to-End Agent Pipeline
  const handleRunAgent = async () => {
    setIsRunning(true);
    setError(null);
    setActiveStageIndex(0);
    setStreamingStepIndex(0);

    const stepInterval = setInterval(() => {
      setStreamingStepIndex((prev) => {
        if (prev < defaultExecutionTrace.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 220);

    const timer1 = setTimeout(() => setActiveStageIndex(1), 300);
    const timer2 = setTimeout(() => setActiveStageIndex(2), 650);
    const timer3 = setTimeout(() => setActiveStageIndex(3), 1050);
    const timer4 = setTimeout(() => setActiveStageIndex(4), 1450);

    try {
      const [pipeResult, reconResult] = await Promise.all([
        api.simulateAgentPipeline(selectedPatientId, activeScenario?.id),
        api.getReconciliation(selectedPatientId).catch(() => null)
      ]);

      await new Promise((resolve) => setTimeout(resolve, 2200));

      setPipelineData(pipeResult);
      if (pipeResult.execution_trace && pipeResult.execution_trace.length > 0) {
        setExecutionTrace(pipeResult.execution_trace);
        setStreamingStepIndex(pipeResult.execution_trace.length - 1);
      } else {
        setStreamingStepIndex(defaultExecutionTrace.length - 1);
      }

      if (reconResult) {
        setReconciliationReport(reconResult);
      }
      setHasRun(true);
      setActiveTab('overview');
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred executing the agent pipeline.');
    } finally {
      clearInterval(stepInterval);
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      setIsRunning(false);
    }
  };

  // View Previous Run
  const handleViewPrevious = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const [doc, val, recon, evPkg] = await Promise.all([
        api.getDocument(selectedPatientId),
        api.getValidation(selectedPatientId),
        api.getReconciliation(selectedPatientId),
        api.getAgentEvidence(selectedPatientId)
      ]);

      setPipelineData({
        patient_id: selectedPatientId,
        pipeline_status: 'completed',
        evidence_summary: evPkg.summary,
        reconciliation_summary: {
          total_entities: recon.total_entities,
          requires_human_review_count: recon.requires_human_review_count
        },
        rag_reference_count: doc.clinical_references.length,
        documentation: doc,
        validation: val
      });
      setReconciliationReport(recon);
      setHasRun(true);
      setStreamingStepIndex(defaultExecutionTrace.length - 1);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve previous agent run data.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleOpenEvidence = (title: string, references: EvidenceLink[]) => {
    setEvidenceModal({
      isOpen: true,
      title,
      references
    });
  };

  return (
    <div className="app-container">
      {/* Top Header & Patient Selection */}
      <Header
        patients={patients}
        selectedPatientId={selectedPatientId}
        onSelectPatient={setSelectedPatientId}
        isLoading={isRunning}
        llmStatus={llmStatus}
        llmInfo={pipelineData?.llm_info}
      />

      <main className="main-content">
        {/* Error Notification */}
        {error && (
          <div
            style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '12px',
              padding: '16px 20px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={22} color="#dc2626" />
              <div>
                <strong style={{ color: '#991b1b', fontSize: '0.9rem' }}>
                  Backend Communication Issue:
                </strong>
                <p style={{ color: '#b91c1c', fontSize: '0.82rem', marginTop: '2px' }}>{error}</p>
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={handleRunAgent}>
              <RefreshCw size={13} /> Retry
            </button>
          </div>
        )}

        {/* 1. Simulated Input Records Sandbox (Top Panel) */}
        {scenarios.length > 0 && activeScenario && (
          <SimulatedRecordsSandbox
            scenarios={scenarios}
            activeScenario={activeScenario}
            onSelectScenario={(sc) => {
              setActiveScenario(sc);
              setPipelineData(null);
              setHasRun(false);
            }}
            isRunning={isRunning}
          />
        )}

        {/* 2. Hero Section & Pipeline Runner */}
        <HeroRunner
          patient={currentPatient}
          onRunAgent={handleRunAgent}
          onViewPrevious={handleViewPrevious}
          isRunning={isRunning}
          activeStageIndex={activeStageIndex}
          hasRun={hasRun}
        />

        {/* 3. Real-Time Agent Execution & Reasoning Stream (Live Feed) */}
        <AgentReasoningStream
          steps={executionTrace}
          isRunning={isRunning}
          currentStepIndex={streamingStepIndex}
        />

        {/* 4. Safety Guardrails & Human Escalation Dashboard (Once Executed) */}
        {pipelineData && (
          <>
            <HumanEscalationCard record={pipelineData.documentation} />
            <SafetyRuleChecklist validationResult={pipelineData.validation} />
          </>
        )}

        {/* Executive Banner */}
        {pipelineData && <ExecutiveBanner pipelineData={pipelineData} />}

        {/* Clickable Pipeline Navigation Bar */}
        {pipelineData && (
          <PipelineNav
            pipelineData={pipelineData}
            activeTab={activeTab}
            onSelectTab={setActiveTab}
          />
        )}

        {/* 5. Structured Output & Interactive Reconciled Fact Sheet */}
        {pipelineData ? (
          <div>
            {activeTab === 'overview' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <ReconciledProfileDiff
                  reconciliationReport={reconciliationReport}
                  onViewEvidenceModal={handleOpenEvidence}
                />
                <SOAPFollowUpRecord
                  record={pipelineData.documentation}
                  onViewEvidence={handleOpenEvidence}
                />
                <ActionableActionList
                  actions={pipelineData.documentation.follow_up_actions}
                />
              </div>
            )}

            {activeTab === 'reconciliation' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <ReconciledProfileDiff
                  reconciliationReport={reconciliationReport}
                  onViewEvidenceModal={handleOpenEvidence}
                />
                <SourceReconciliation reconciliationReport={reconciliationReport} />
              </div>
            )}

            {activeTab === 'documentation' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <SOAPFollowUpRecord
                  record={pipelineData.documentation}
                  onViewEvidence={handleOpenEvidence}
                />
                <ActionableActionList
                  actions={pipelineData.documentation.follow_up_actions}
                />
                <VerifiedRecord
                  record={pipelineData.documentation}
                  onViewEvidence={handleOpenEvidence}
                />
              </div>
            )}

            {activeTab === 'verification' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <SafetyRuleChecklist validationResult={pipelineData.validation} />
                <VerificationReport validationResult={pipelineData.validation} />
              </div>
            )}

            {activeTab === 'rag' && (
              <ClinicalRAGPanel
                references={pipelineData.documentation.clinical_references}
              />
            )}

            {activeTab === 'audit' && (
              <AuditJSON pipelineData={pipelineData} />
            )}
          </div>
        ) : (
          !isRunning && (
            <div className="card" style={{ padding: '40px 20px', textAlign: 'center' }}>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  background: '#eff6ff',
                  color: '#2563eb',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 12px'
                }}
              >
                <RefreshCw size={24} />
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a', margin: '0 0 8px 0' }}>
                Ready to Execute Multi-Agent Clinical Simulation
              </h3>
              <p
                style={{
                  maxWidth: '560px',
                  margin: '0 auto 18px',
                  color: '#64748b',
                  fontSize: '0.85rem',
                  lineHeight: 1.5
                }}
              >
                Select a simulated clinical conflict scenario in the Sandbox above, then click{' '}
                <strong>"Run Clinical Agent"</strong> to stream the real-time reasoning loop and inspect the reconciled fact sheet.
              </p>
              <button
                className="btn btn-primary"
                onClick={handleRunAgent}
                style={{ padding: '10px 24px', fontSize: '0.9rem' }}
              >
                Run Clinical Agent
              </button>
            </div>
          )
        )}
      </main>

      {/* Evidence Traceability Modal */}
      <EvidenceModal
        isOpen={evidenceModal.isOpen}
        title={evidenceModal.title}
        evidenceLinks={evidenceModal.references}
        onClose={() => setEvidenceModal({ isOpen: false, title: '', references: [] })}
      />
    </div>
  );
}

export default App;

import React from 'react';
import { Database, GitCompare, BookOpen, FileText, ShieldCheck, ChevronRight } from 'lucide-react';
import { AgentPipelineResponse } from '../types/clinical';

export type ActiveTab = 'overview' | 'reconciliation' | 'documentation' | 'verification' | 'rag' | 'audit';

interface PipelineNavProps {
  pipelineData: AgentPipelineResponse | null;
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
}

export const PipelineNav: React.FC<PipelineNavProps> = ({
  pipelineData,
  activeTab,
  onSelectTab
}) => {
  const evCount = pipelineData ? pipelineData.evidence_summary.total_evidence_items : 11;
  const reconCount = pipelineData ? pipelineData.reconciliation_summary.total_entities : 6;
  const ragCount = pipelineData ? pipelineData.rag_reference_count : 7;
  const docConflicts = pipelineData ? pipelineData.documentation.unresolved_conflict_count : 1;
  const valStatus = pipelineData ? (pipelineData.validation.passed ? 'PASSED' : 'FAILED') : 'PENDING';

  return (
    <div className="pipeline-bar">
      <div
        className={`pipeline-step ${activeTab === 'overview' ? 'active' : ''}`}
        onClick={() => onSelectTab('overview')}
      >
        <div className="pipeline-step-number">★</div>
        <div className="pipeline-step-text">
          <h4>Overview</h4>
          <p>Executive Summary</p>
        </div>
      </div>

      <ChevronRight size={16} className="pipeline-arrow" />

      <div
        className={`pipeline-step ${activeTab === 'reconciliation' ? 'active' : ''}`}
        onClick={() => onSelectTab('reconciliation')}
      >
        <div className="pipeline-step-number">
          <GitCompare size={14} />
        </div>
        <div className="pipeline-step-text">
          <h4>Reconciliation</h4>
          <p>{reconCount} entities ({evCount} evidence)</p>
        </div>
      </div>

      <ChevronRight size={16} className="pipeline-arrow" />

      <div
        className={`pipeline-step ${activeTab === 'rag' ? 'active' : ''}`}
        onClick={() => onSelectTab('rag')}
      >
        <div className="pipeline-step-number">
          <BookOpen size={14} />
        </div>
        <div className="pipeline-step-text">
          <h4>Clinical RAG</h4>
          <p>{ragCount} references</p>
        </div>
      </div>

      <ChevronRight size={16} className="pipeline-arrow" />

      <div
        className={`pipeline-step ${activeTab === 'documentation' ? 'active' : ''}`}
        onClick={() => onSelectTab('documentation')}
      >
        <div className="pipeline-step-number">
          <FileText size={14} />
        </div>
        <div className="pipeline-step-text">
          <h4>Documentation</h4>
          <p>Structured Record</p>
        </div>
      </div>

      <ChevronRight size={16} className="pipeline-arrow" />

      <div
        className={`pipeline-step ${activeTab === 'verification' ? 'active' : ''}`}
        onClick={() => onSelectTab('verification')}
      >
        <div className="pipeline-step-number">
          <ShieldCheck size={14} />
        </div>
        <div className="pipeline-step-text">
          <h4>Verification</h4>
          <p>{valStatus} ({docConflicts} conflict)</p>
        </div>
      </div>

      <div style={{ marginLeft: 'auto' }}>
        <button
          className={`btn btn-sm ${activeTab === 'audit' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => onSelectTab('audit')}
          style={{ fontSize: '0.75rem' }}
        >
          Audit JSON
        </button>
      </div>
    </div>
  );
};

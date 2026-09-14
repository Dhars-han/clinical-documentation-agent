export interface Patient {
  id: string;
  name: string;
  age: number;
}

export interface EvidenceLink {
  claim: string;
  source: string;
  source_date?: string | null;
  raw_excerpt: string;
}

export interface EvidenceItem {
  id: string;
  category: 'medication' | 'allergy' | 'lab' | 'clinical_observation';
  entity_name: string;
  source: string;
  source_date?: string | null;
  raw_text: string;
  attributes: Record<string, any>;
  modality: 'structured_record' | 'unstructured_text';
  confidence: number;
}

export interface EvidenceSummary {
  total_evidence_items: number;
  sources_queried: string[];
  item_counts_by_source: Record<string, number>;
  item_counts_by_category: Record<string, number>;
  unique_entities_identified: string[];
}

export interface EvidencePackage {
  patient_id: string;
  patient_name?: string | null;
  patient_age?: number | null;
  gathered_at: string;
  summary: EvidenceSummary;
  items: EvidenceItem[];
}

export type ReconciliationStatus = 'consistent' | 'resolved' | 'conflict' | 'unresolved';

export interface EvidenceReference {
  source: string;
  source_date?: string | null;
  raw_excerpt: string;
  attributes: Record<string, any>;
  modality?: string | null;
}

export interface ReconciliationResult {
  patient_id: string;
  entity: string;
  category: string;
  status: ReconciliationStatus;
  current_state?: string | null;
  confidence: number;
  reason: string;
  supporting_evidence: EvidenceReference[];
  conflicting_evidence: EvidenceReference[];
  requires_human_review: boolean;
}

export interface ReconciliationReport {
  patient_id: string;
  reconciled_at: string;
  total_entities: number;
  requires_human_review_count: number;
  results: ReconciliationResult[];
}

export interface DocumentedMedication {
  name: string;
  status: string;
  regimen?: string | null;
  reconciliation_status: string;
  requires_human_review: boolean;
  evidence_references: EvidenceLink[];
}

export interface DocumentedAllergy {
  allergen: string;
  status: string;
  documented_reaction?: string | null;
  reported_statement?: string | null;
  conflict_details?: string | null;
  requires_human_review: boolean;
  evidence_references: EvidenceLink[];
}

export interface DocumentedLab {
  test_name: string;
  value: string;
  unit: string;
  date?: string | null;
  source: string;
  evidence_references: EvidenceLink[];
}

export interface DocumentedChange {
  entity: string;
  change_type: string;
  description: string;
  timeline?: string | null;
  evidence_references: EvidenceLink[];
}

export interface FollowUpAction {
  action_type: string;
  description: string;
  urgency: string;
  requires_human_review: boolean;
}

export interface ClinicalReferenceLink {
  entity: string;
  document_id: string;
  title: string;
  source_organization: string;
  section: string;
  publication_date?: string | null;
  snippet: string;
  relevance_score: number;
}

export interface ClinicalFollowUpRecord {
  patient_id: string;
  patient_name?: string | null;
  patient_age?: number | null;
  generated_at: string;
  consultation_summary: string;
  medications: DocumentedMedication[];
  allergies: DocumentedAllergy[];
  relevant_labs: DocumentedLab[];
  documented_changes: DocumentedChange[];
  unresolved_conflicts: string[];
  follow_up_actions: FollowUpAction[];
  clinical_references: ClinicalReferenceLink[];
  requires_human_review: boolean;
  unresolved_conflict_count: number;
}

export interface ValidationIssue {
  category: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  entity?: string | null;
  rule_id?: string | null;
  evidence_references: any[];
}

export interface ValidationResult {
  patient_id: string;
  validation_status: 'passed' | 'failed' | 'requires_human_review';
  passed: boolean;
  issues: ValidationIssue[];
  checks_performed: string[];
  evidence_grounding_passed: boolean;
  reconciliation_consistency_passed: boolean;
  conflict_preservation_passed: boolean;
  rag_separation_passed: boolean;
  uncertainty_handling_passed: boolean;
  safety_boundary_passed: boolean;
  requires_human_review: boolean;
  validated_at: string;
}

export interface LLMInfo {
  provider: string;
  model: string;
  is_active: boolean;
  mode: 'hybrid_deepseek' | 'deterministic_fallback' | string;
  stages_integrated?: string[];
}

export interface LLMStatusResponse {
  provider: string;
  model: string;
  is_active: boolean;
  mode: 'hybrid_deepseek' | 'deterministic_fallback' | string;
}

export interface ExecutionTraceStep {
  step_number: number;
  type: 'PARSE' | 'TOOL_CALL' | 'RECONCILE' | 'CONFLICT_DETECTED' | 'GUARDRAIL_CHECK' | 'SYNTHESIS' | 'VALIDATION' | string;
  label: string;
  message: string;
  timestamp: string;
  details?: string[];
}

export interface SimulationScenario {
  id: string;
  name: string;
  badge: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  conflict_type: string;
  description: string;
  transcript: string;
  historical_notes: string;
  lab_and_meds: {
    active_medications: Array<{
      name: string;
      dose: string;
      frequency: string;
      status: string;
      date: string;
    }>;
    allergy_registry: Array<{
      allergen: string;
      reaction: string;
      severity: string;
      date: string;
    }>;
    recent_labs: Array<{
      test: string;
      value: string;
      unit: string;
      ref_range: string;
      date: string;
    }>;
  };
}

export interface AgentPipelineResponse {
  patient_id: string;
  pipeline_status: string;
  llm_info?: LLMInfo;
  execution_trace?: ExecutionTraceStep[];
  evidence_summary: EvidenceSummary;
  reconciliation_summary: {
    total_entities: number;
    requires_human_review_count: number;
  };
  rag_reference_count: number;
  documentation: ClinicalFollowUpRecord;
  validation: ValidationResult;
}



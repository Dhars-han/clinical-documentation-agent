import {
  Patient,
  AgentPipelineResponse,
  ClinicalFollowUpRecord,
  ValidationResult,
  ReconciliationReport,
  EvidencePackage,
  LLMStatusResponse,
  SimulationScenario
} from '../types/clinical';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '');

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      let parsedMessage = errorText;
      try {
        const json = JSON.parse(errorText);
        parsedMessage = json.detail || json.message || errorText;
      } catch {
        // use raw text
      }
      throw new Error(`API Error (${response.status}): ${parsedMessage}`);
    }

    return await response.json();
  } catch (err: any) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      const target = API_BASE_URL || window.location.origin;
      throw new Error(`Cannot connect to backend server at ${target}. Ensure the API is reachable.`);
    }
    throw err;
  }
}

const DEFAULT_SCENARIOS: SimulationScenario[] = [
  {
    id: "scenario_baseline",
    name: "Default Baseline: Transcript Denial vs EHR Penicillin Allergy",
    badge: "Baseline EHR Conflict",
    severity: "high",
    conflict_type: "allergy_denial",
    description: "Patient verbally denies drug allergies ('reports no known drug allergies'), but hospital EHR registry documents active Penicillin allergy. Also includes Drug B patient cessation reconciling with EHR discontinuation.",
    transcript: "Doctor: Good morning. How are you feeling on your current medications?\nPatient: Doing well overall. I take the Metformin 500 mg once daily with meals.\nDoctor: What about Drug B?\nPatient: I stopped taking Drug B approximately one week ago because it caused mild morning nausea.\nDoctor: Any known drug allergies or adverse reactions?\nPatient: No, I don't think I have any drug allergies.",
    historical_notes: "2026-08-20 Primary Care Progress Note (Dr. R. Vance):\n- Assessment: Type 2 Diabetes Mellitus, well-controlled on Metformin 500mg daily.\n- Medication reconciliation: Metformin 500mg once daily, Drug B 10mg once daily.\n- Plan: Continue current regimen. Return in 4 weeks for follow-up and lab evaluation.",
    lab_and_meds: {
      active_medications: [
        { name: "Metformin", dose: "500 mg", frequency: "once daily", status: "active", date: "2026-09-10" },
        { name: "Drug B", dose: "10 mg", frequency: "once daily", status: "discontinued", date: "2026-09-10" }
      ],
      allergy_registry: [
        { allergen: "Penicillin", reaction: "Unknown / Unspecified", severity: "Potential Anaphylaxis", date: "2026-09-08" }
      ],
      recent_labs: [
        { test: "Hemoglobin A1c (HbA1c)", value: "7.1", unit: "%", ref_range: "< 5.7%", date: "2026-09-10" },
        { test: "Serum Creatinine", value: "1.0", unit: "mg/dL", ref_range: "0.7 - 1.3 mg/dL", date: "2026-09-10" },
        { test: "eGFR (Estimated)", value: "78", unit: "mL/min/1.73m²", ref_range: "> 60 mL/min", date: "2026-09-10" }
      ]
    }
  },
  {
    id: "scenario_cross_reactivity",
    name: "Injected Conflict: Penicillin Anaphylaxis vs Prior Amoxicillin Tolerated",
    badge: "Cross-Reactivity Alert",
    severity: "critical",
    conflict_type: "cross_reactivity",
    description: "Patient asserts a severe childhood Penicillin allergy with anaphylaxis, but a 2022 EHR urgent care note documents successful completion of a 7-day course of Amoxicillin with zero adverse reaction.",
    transcript: "Doctor: Reviewing your allergies today. Any drug reactions?\nPatient: Yes, doctor! My mother told me I had a severe anaphylactic reaction with hives and facial swelling to Penicillin as a teenager. I must avoid all penicillins!\nDoctor: Understood. And current medications?\nPatient: Still taking Metformin 500 mg daily. I discontinued Drug B about a week ago due to stomach upset.",
    historical_notes: "2022-04-14 Urgent Care Encounter Note (Dr. M. Chen):\n- Diagnosis: Acute bacterial bronchitis with purulent sputum.\n- Prescribed: Amoxicillin-Clavulanate 875/125 mg orally twice daily for 7 days.\n- Follow-up Note (2022-04-22): Patient completed entire 7-day Amoxicillin course. Symptoms resolved. No rash, urticaria, or adverse drug reaction observed.",
    lab_and_meds: {
      active_medications: [
        { name: "Metformin", dose: "500 mg", frequency: "once daily", status: "active", date: "2026-09-10" },
        { name: "Amoxicillin-Clavulanate", dose: "875/125 mg", frequency: "completed historical course", status: "historical", date: "2022-04-14" }
      ],
      allergy_registry: [
        { allergen: "Penicillin", reaction: "Severe Anaphylaxis / Facial Angioedema", severity: "Critical", date: "2026-09-08" }
      ],
      recent_labs: [
        { test: "Hemoglobin A1c (HbA1c)", value: "7.1", unit: "%", ref_range: "< 5.7%", date: "2026-09-10" },
        { test: "Serum Creatinine", value: "1.0", unit: "mg/dL", ref_range: "0.7 - 1.3 mg/dL", date: "2026-09-10" }
      ]
    }
  },
  {
    id: "scenario_dosage_mismatch",
    name: "Injected Conflict: Lisinopril 20mg Active Dose vs EHR 10mg Order",
    badge: "Active Dose Mismatch",
    severity: "high",
    conflict_type: "dosage_discrepancy",
    description: "Patient reports that their cardiologist increased Lisinopril to 20 mg daily 3 weeks ago, but the primary hospital EHR database order reflects Lisinopril 10 mg daily.",
    transcript: "Doctor: Are you taking your blood pressure medication consistently?\nPatient: Yes, the cardiologist increased my Lisinopril to 20 mg every morning three weeks ago. Also on Metformin 500 mg daily, and stopped Drug B last week.\nDoctor: Any lightheadedness or dizziness?\nPatient: None at all. Blood pressure at home has been around 124/80.",
    historical_notes: "2026-08-20 Outpatient Cardiology / Internal Medicine Note:\n- Assessment: Essential Hypertension, stage 1.\n- Order: Lisinopril 10 mg orally once daily. Refilled for 90 days. Next review in 6 months.",
    lab_and_meds: {
      active_medications: [
        { name: "Lisinopril", dose: "10 mg", frequency: "once daily", status: "active order in EHR", date: "2026-08-20" },
        { name: "Metformin", dose: "500 mg", frequency: "once daily", status: "active", date: "2026-09-10" }
      ],
      allergy_registry: [
        { allergen: "Penicillin", reaction: "Unknown", severity: "Moderate", date: "2026-09-08" }
      ],
      recent_labs: [
        { test: "Serum Potassium", value: "4.4", unit: "mEq/L", ref_range: "3.5 - 5.0 mEq/L", date: "2026-09-10" },
        { test: "Serum Creatinine", value: "1.0", unit: "mg/dL", ref_range: "0.7 - 1.3 mg/dL", date: "2026-09-10" }
      ]
    }
  }
];

export const api = {
  getPatients: async (): Promise<Patient[]> => {
    try {
      return await request<Patient[]>('/patients');
    } catch {
      return [{ id: 'P001', name: 'Synthetic Patient 001', age: 45 }];
    }
  },

  getPatient: async (patientId: string): Promise<Patient> => {
    try {
      return await request<Patient>(`/patients/${patientId}`);
    } catch {
      return { id: patientId, name: 'Synthetic Patient 001', age: 45 };
    }
  },

  getAgentEvidence: (patientId: string): Promise<EvidencePackage> => {
    return request<EvidencePackage>(`/patients/${patientId}/agent/evidence`);
  },

  getReconciliation: (patientId: string): Promise<ReconciliationReport> => {
    return request<ReconciliationReport>(`/patients/${patientId}/reconcile`);
  },

  getDocument: (patientId: string): Promise<ClinicalFollowUpRecord> => {
    return request<ClinicalFollowUpRecord>(`/patients/${patientId}/document`);
  },

  getValidation: (patientId: string): Promise<ValidationResult> => {
    return request<ValidationResult>(`/patients/${patientId}/validate`);
  },

  runAgentPipeline: (patientId: string): Promise<AgentPipelineResponse> => {
    return request<AgentPipelineResponse>(`/patients/${patientId}/run-agent`, {
      method: 'POST'
    });
  },

  getRAGContext: (patientId: string): Promise<any> => {
    return request<any>(`/patients/${patientId}/rag/context`);
  },

  getLLMStatus: async (): Promise<LLMStatusResponse> => {
    try {
      return await request<LLMStatusResponse>('/config/llm-status');
    } catch {
      return {
        provider: 'DeepSeek',
        model: 'deepseek-chat',
        is_active: false,
        mode: 'deterministic_fallback'
      };
    }
  },

  getSimulationScenarios: async (patientId: string): Promise<SimulationScenario[]> => {
    try {
      const res = await request<SimulationScenario[]>(`/patients/${patientId}/simulation-scenarios`);
      return res && res.length > 0 ? res : DEFAULT_SCENARIOS;
    } catch {
      return DEFAULT_SCENARIOS;
    }
  },

  simulateAgentPipeline: async (patientId: string, scenarioId?: string): Promise<AgentPipelineResponse> => {
    try {
      return await request<AgentPipelineResponse>(`/patients/${patientId}/simulate-agent`, {
        method: 'POST',
        body: scenarioId ? JSON.stringify({ scenario_id: scenarioId }) : undefined
      });
    } catch (err: any) {
      if (err.message && err.message.includes('404')) {
        // Graceful fallback to existing run-agent endpoint if backend hasn't reloaded yet
        return await request<AgentPipelineResponse>(`/patients/${patientId}/run-agent`, {
          method: 'POST'
        });
      }
      throw err;
    }
  }
};

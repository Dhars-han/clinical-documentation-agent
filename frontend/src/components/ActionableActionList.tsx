import React, { useState } from 'react';
import {
  ClipboardCheck,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Calendar,
  ShieldCheck,
  Check
} from 'lucide-react';
import { FollowUpAction } from '../types/clinical';

interface ActionableActionListProps {
  actions: FollowUpAction[];
}

export const ActionableActionList: React.FC<ActionableActionListProps> = ({ actions }) => {
  const initialTasks = actions && actions.length > 0
    ? actions.map((a, i) => ({
        id: `task-${i + 1}`,
        action_type: a.action_type,
        description: a.description,
        urgency: a.urgency || (a.requires_human_review ? 'HIGH PRIORITY - SAFETY' : 'ROUTINE MONITORING'),
        requires_human_review: a.requires_human_review,
        completed: false
      }))
    : [
        {
          id: 'task-1',
          action_type: 'Allergy Verification & Precaution',
          description: 'Perform formal allergy testing / sensitivity verification for Penicillin before any beta-lactam prescribing.',
          urgency: 'HIGH PRIORITY - CLINICAL SAFETY',
          requires_human_review: true,
          completed: false
        },
        {
          id: 'task-2',
          action_type: 'Pharmacy Record Update',
          description: 'Discontinue Drug B 10 mg order in outpatient electronic dispensing system to prevent unauthorized refills.',
          urgency: 'ROUTINE CARE COORDINATION',
          requires_human_review: false,
          completed: false
        },
        {
          id: 'task-3',
          action_type: 'Laboratory Monitoring',
          description: 'Order repeat Serum Creatinine and eGFR in 3 months per renal safety monitoring guidelines.',
          urgency: 'ROUTINE MONITORING',
          requires_human_review: false,
          completed: false
        },
        {
          id: 'task-4',
          action_type: 'Glycemic Target Evaluation',
          description: 'Schedule repeat HbA1c in 3 months to monitor response to Metformin 500 mg monotherapy (ADA guideline recommendation).',
          urgency: 'ROUTINE MONITORING',
          requires_human_review: false,
          completed: false
        }
      ];

  const [taskList, setTaskList] = useState(initialTasks);

  const toggleComplete = (id: string) => {
    setTaskList((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
    );
  };

  const completedCount = taskList.filter((t) => t.completed).length;

  return (
    <div className="card" style={{ marginBottom: '24px' }}>
      <div className="card-header" style={{ background: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: '#f0fdf4',
              color: '#16a34a',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <ClipboardCheck size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Actionable Action List (Extracted Clinical Tasks)
            </h3>
            <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '2px 0 0 0' }}>
              Specific follow-up and safety actions extracted autonomously from reconciled findings
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-info">
            {completedCount} of {taskList.length} Completed
          </span>
        </div>
      </div>

      <div className="card-body" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {taskList.map((task) => {
            const isHigh = task.urgency.includes('HIGH') || task.requires_human_review;

            return (
              <div
                key={task.id}
                onClick={() => toggleComplete(task.id)}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  border: task.completed
                    ? '1px solid #e2e8f0'
                    : isHigh
                    ? '1px solid #fde68a'
                    : '1px solid #e2e8f0',
                  background: task.completed
                    ? '#f8fafc'
                    : isHigh
                    ? '#fffbeb'
                    : '#ffffff',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '4px',
                    border: task.completed ? '2px solid #10b981' : '2px solid #94a3b8',
                    background: task.completed ? '#10b981' : '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#ffffff',
                    marginTop: '2px',
                    flexShrink: 0
                  }}
                >
                  {task.completed && <Check size={14} strokeWidth={3} />}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: '0.82rem',
                        color: task.completed ? '#94a3b8' : '#0f172a',
                        textDecoration: task.completed ? 'line-through' : 'none'
                      }}
                    >
                      {task.action_type}
                    </span>
                    <span
                      className={`badge ${
                        task.completed
                          ? 'badge-info'
                          : isHigh
                          ? 'badge-warning'
                          : 'badge-info'
                      }`}
                      style={{ fontSize: '0.68rem' }}
                    >
                      {task.urgency}
                    </span>
                  </div>

                  <p
                    style={{
                      margin: 0,
                      fontSize: '0.8rem',
                      color: task.completed ? '#94a3b8' : '#334155',
                      lineHeight: 1.4,
                      textDecoration: task.completed ? 'line-through' : 'none'
                    }}
                  >
                    {task.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export type SessionRecord = {
  id: string;
  created_at: string;
  updated_at: string;
  role: string;
  seniority: string;
  interview_type: string;
  interview_language: string;
  duration_minutes: number;
  voice_mode: string;
  status: string;
  current_question: string | null;
  question_cursor: number;
};

export type SessionDocuments = {
  session_id: string;
  vacancy_text: string;
  vacancy_url: string;
  resume_filename: string;
  resume_saved_path: string;
  created_at: string;
  updated_at: string;
};

export type SessionTurn = {
  turn_index: number;
  topic: string | null;
  question_kind: "main" | "followup" | null;
  question: string;
  answer: string;
  feedback: string;
  evaluation_summary: {
    score_0_10?: number;
    follow_up_needed?: boolean;
    detected_gaps?: string[];
  };
  next_question: string | null;
  created_at: string;
};

export type ParserSummary = {
  source_type: string;
  parser_used: string;
  char_count: number;
  warnings: string[];
  preview: string;
};

export type CandidateProfile = {
  target_role: string;
  target_seniority: string;
  experience_years_estimate: number;
  primary_skills: string[];
  project_highlights: string[];
  strengths: string[];
  risk_signals: string[];
  seniority_signals: string[];
  source_summary: {
    char_count: number;
    line_count: number;
    has_content: boolean;
  };
};

export type JobProfile = {
  target_role: string;
  target_seniority: string;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  domain_keywords: string[];
  source_summary: {
    char_count: number;
    line_count: number;
    has_content: boolean;
  };
};

export type SkillGapMap = {
  matched_skills: string[];
  missing_skills: string[];
  adjacent_skills: string[];
  risk_level: string;
  recommended_focus: string[];
};

export type InterviewTopic = {
  topic: string;
  priority: string;
  expected_difficulty: string;
  interview_type: string;
  reason: string;
};

export type ATSKeywordAnalysis = {
  present_keywords: string[];
  missing_keywords: string[];
  keyword_density_assessment: string;
};

export type RewrittenResumeFragment = {
  section_title: string;
  original_excerpt: string;
  rewritten_version: string;
  rationale: string;
};

export type HRAnalysis = {
  status: string;
  provider: string;
  model: string;
  prompt_version: string;
  message: string;
  overall_match_score_pct: number;
  match_explanation: string;
  candidate_level: string;
  vacancy_level: string;
  resume_quality_score_pct: number;
  ats_compatibility_score_pct: number;
  interview_probability_pct: number;
  hr_screening_probability_pct: number;
  salary_level_estimation: string;
  market_competitiveness: string;
  risk_of_rejection: string;
  strong_sides: string[];
  weak_sides: string[];
  missing_skills: string[];
  strong_matches: string[];
  hr_concerns: string[];
  why_candidate_fits: string[];
  why_candidate_may_be_rejected: string[];
  what_raises_questions: string[];
  improvement_suggestions: string[];
  technologies_to_highlight: string[];
  technologies_to_learn: string[];
  hr_verdict: string;
  ats_keyword_analysis: ATSKeywordAnalysis;
  rewritten_resume_fragments: RewrittenResumeFragment[];
};

export type SessionAnalysis = {
  session_id: string;
  analysis_status: string;
  parser_summary: {
    resume?: ParserSummary;
    vacancy?: ParserSummary;
  };
  candidate_profile: CandidateProfile;
  job_profile: JobProfile;
  skill_gap_map: SkillGapMap;
  hr_analysis?: HRAnalysis;
  interview_topics: InterviewTopic[];
  created_at: string;
  updated_at: string;
};

export type WorkflowTraceEvent = {
  node: string;
  summary: string;
  timestamp: string;
  details?: Record<string, unknown>;
};

export type CoachingReport = {
  skill_name: string;
  skill_path: string;
  skill_loaded: boolean;
  what_was_good: string[];
  what_was_weak: string[];
  how_to_improve: string[];
  recommended_drills: string[];
  raw_skill_excerpt: string;
};

export type FinalReport = {
  summary: string;
  final_score_0_10: number;
  score_by_category: Record<string, number>;
  strengths: string[];
  gaps: string[];
  topics_to_review: string[];
  questions_to_practice: string[];
  coaching?: CoachingReport;
};

export type WorkflowPayload = {
  session_id: string;
  interview_plan: InterviewTopic[];
  latest_trace: WorkflowTraceEvent[];
  last_evaluation: Record<string, unknown>;
  final_report: FinalReport | Record<string, never>;
  created_at: string;
  updated_at: string;
};

export type VoiceTranscriptionPayload = {
  status: string;
  provider: string;
  model: string;
  language: string;
  audio_path: string;
  transcript: string;
};

export type SpeechSynthesisPayload = {
  status: string;
  provider: string;
  model: string;
  voice: string;
  mime_type: string;
  text: string;
  audio_base64: string;
};

export type SessionPayload = {
  session: SessionRecord;
  documents: SessionDocuments;
  analysis: SessionAnalysis;
  workflow: WorkflowPayload;
  turns: SessionTurn[];
};

export type CreateSessionInput = {
  role: string;
  seniority: string;
  interview_type: string;
  interview_language: string;
  duration_minutes: number;
  voice_mode: string;
};

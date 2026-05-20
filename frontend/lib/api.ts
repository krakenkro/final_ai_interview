import type {
  CreateSessionInput,
  SessionPayload,
  SpeechSynthesisPayload,
  VoiceTranscriptionPayload,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }

  return (await response.json()) as T;
}

export async function createSession(
  payload: CreateSessionInput,
): Promise<SessionPayload> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseResponse<SessionPayload>(response);
}

export async function uploadSessionDocuments(
  sessionId: string,
  formData: FormData,
): Promise<SessionPayload> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/documents`, {
    method: "POST",
    body: formData,
  });

  return parseResponse<SessionPayload>(response);
}

export async function getSession(sessionId: string): Promise<SessionPayload> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
    cache: "no-store",
  });

  return parseResponse<SessionPayload>(response);
}

export async function analyzeSession(sessionId: string): Promise<SessionPayload> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/analyze`, {
    method: "POST",
  });

  return parseResponse<SessionPayload>(response);
}

export async function startInterview(sessionId: string): Promise<SessionPayload> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/start`, {
    method: "POST",
  });

  return parseResponse<SessionPayload>(response);
}

export async function submitAnswer(
  sessionId: string,
  answerText: string,
): Promise<SessionPayload> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/answers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ answer_text: answerText }),
  });

  return parseResponse<SessionPayload>(response);
}

export async function transcribeSessionAudio(
  sessionId: string,
  audioFile: File,
): Promise<VoiceTranscriptionPayload> {
  const formData = new FormData();
  formData.append("audio", audioFile);

  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/voice/transcribe`, {
    method: "POST",
    body: formData,
  });

  return parseResponse<VoiceTranscriptionPayload>(response);
}

export async function synthesizeQuestionAudio(
  sessionId: string,
  text?: string,
): Promise<SpeechSynthesisPayload> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/voice/question-audio`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(text ? { text } : {}),
  });

  return parseResponse<SpeechSynthesisPayload>(response);
}

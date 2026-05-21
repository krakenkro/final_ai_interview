"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import {
  analyzeSession,
  createSession,
  getSession,
  startInterview,
  submitAnswer,
  synthesizeQuestionAudio,
  transcribeSessionAudio,
  uploadSessionDocuments,
} from "@/lib/api";
import type { FinalReport, HRAnalysis, SessionPayload, SessionTurn } from "@/lib/types";
import {
  Badge,
  ButtonSpinner,
  EmptyState,
  MetricCard,
  RingScore,
  ScoreBar,
  SectionHeader,
  TrendBars,
} from "@/components/ui/primitives";

type WorkspaceStep = "setup" | "analysis" | "interview" | "report";
type SetupState =
  | "idle"
  | "creating"
  | "uploading"
  | "created"
  | "analyzing"
  | "ready"
  | "error";

function formatStatusLabel(value: string | null | undefined) {
  if (!value) {
    return "draft";
  }
  return value.replaceAll("_", " ");
}

function formatRiskLabel(value: string | undefined) {
  if (!value) {
    return "unknown";
  }
  return value.replaceAll("_", " ");
}

function statusTone(state: SetupState) {
  if (state === "error") {
    return "warning";
  }
  if (state === "ready") {
    return "success";
  }
  if (state === "creating" || state === "uploading" || state === "analyzing") {
    return "accent";
  }
  return "neutral";
}

function questionKindLabel(value: string | null | undefined) {
  return value === "followup" ? "follow-up" : "question";
}

function deriveStep(sessionData: SessionPayload | null): WorkspaceStep {
  if (!sessionData) {
    return "setup";
  }

  const finalReport = sessionData.workflow?.final_report;
  const reportReady =
    finalReport &&
    typeof finalReport === "object" &&
    "summary" in finalReport &&
    typeof finalReport.summary === "string";

  if (sessionData.session.status === "completed" && reportReady) {
    return "report";
  }
  if (sessionData.session.status === "in_progress") {
    return "interview";
  }
  if (sessionData.analysis?.analysis_status === "completed") {
    return "analysis";
  }
  return "setup";
}

function isFinalReport(
  value: SessionPayload["workflow"]["final_report"] | undefined,
): value is FinalReport {
  return Boolean(value && typeof value === "object" && "summary" in value);
}

function buildPipelineSteps(setupState: SetupState) {
  return [
    {
      label: "Session created",
      state:
        setupState === "creating"
          ? "active"
          : setupState === "uploading" ||
              setupState === "created" ||
              setupState === "analyzing" ||
              setupState === "ready"
            ? "done"
            : "pending",
    },
    {
      label: "Documents attached",
      state:
        setupState === "uploading"
          ? "active"
          : setupState === "created" || setupState === "analyzing" || setupState === "ready"
            ? "done"
            : "pending",
    },
    {
      label: "AI analysis ready",
      state:
        setupState === "analyzing"
          ? "active"
          : setupState === "ready"
            ? "done"
            : "pending",
    },
  ] as const;
}

function buildTurnTrend(turns: SessionTurn[]) {
  return turns
    .filter((turn) => typeof turn.evaluation_summary?.score_0_10 === "number")
    .map((turn) => ({
      label: `Turn ${turn.turn_index}`,
      value: Number(turn.evaluation_summary?.score_0_10 ?? 0),
      hint: turn.topic ?? undefined,
    }));
}

function renderList(items: string[], emptyLabel = "Пока нет данных.") {
  if (!items.length) {
    return <p className="bodyMuted">{emptyLabel}</p>;
  }

  return (
    <ul className="listClean">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function renderChips(items: string[], tone: "success" | "accent" | "warning" | "neutral") {
  if (!items.length) {
    return <p className="bodyMuted">Пока нет данных.</p>;
  }

  const toneClass = {
    success: "chipSuccess",
    accent: "chipAccent",
    warning: "chipWarning",
    neutral: "chipNeutral",
  }[tone];

  return (
    <div className="chipRow">
      {items.map((item) => (
        <span className={`chip ${toneClass}`} key={item}>
          {item}
        </span>
      ))}
    </div>
  );
}

function HrSnapshot({ hrAnalysis }: { hrAnalysis?: HRAnalysis }) {
  if (!hrAnalysis?.status) {
    return (
      <article className="workspaceCard">
        <SectionHeader
          eyebrow="HR snapshot"
          title="HR analysis ещё не построен"
          description="Семантический recruiter-style слой появится после завершения анализа."
          size="compact"
        />
      </article>
    );
  }

  return (
    <article className="workspaceCard">
      <SectionHeader
        eyebrow="HR snapshot"
        title={hrAnalysis.hr_verdict || "Recruiter snapshot"}
        description={hrAnalysis.match_explanation || hrAnalysis.message || "Краткое HR summary."}
        size="compact"
        aside={<Badge tone={hrAnalysis.status === "completed" ? "success" : "warning"}>{hrAnalysis.status}</Badge>}
      />

      <div className="summaryStats">
        <div className="summaryStat">
          <span>Match</span>
          <strong>{hrAnalysis.overall_match_score_pct}%</strong>
        </div>
        <div className="summaryStat">
          <span>Interview</span>
          <strong>{hrAnalysis.interview_probability_pct}%</strong>
        </div>
        <div className="summaryStat">
          <span>ATS</span>
          <strong>{hrAnalysis.ats_compatibility_score_pct}%</strong>
        </div>
      </div>

      {hrAnalysis.missing_skills?.length ? (
        <div className="stackSection">
          <p className="miniLabel">Top missing skills</p>
          {renderChips(hrAnalysis.missing_skills.slice(0, 4), "warning")}
        </div>
      ) : null}
    </article>
  );
}

export function InterviewWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const querySessionId = searchParams.get("session_id");

  const [localSessionId, setLocalSessionId] = useState<string | null>(querySessionId);
  const [sessionData, setSessionData] = useState<SessionPayload | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [setupState, setSetupState] = useState<SetupState>("idle");
  const [statusMessage, setStatusMessage] = useState(
    "Соберите контекст интервью: роль, резюме и вакансию. После этого появится HR snapshot и topics для mock interview.",
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [isStarting, setIsStarting] = useState(false);
  const [isSubmittingAnswer, setIsSubmittingAnswer] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(null);
  const [questionAudioUrl, setQuestionAudioUrl] = useState<string | null>(null);
  const [questionAudioForText, setQuestionAudioForText] = useState<string | null>(null);
  const [selectedAudioFile, setSelectedAudioFile] = useState<File | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [mediaSupported, setMediaSupported] = useState(true);
  const [isTraceOpen, setIsTraceOpen] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordedBlobRef = useRef<Blob | null>(null);

  const activeSessionId = querySessionId ?? localSessionId;

  useEffect(() => {
    setLocalSessionId(querySessionId);
  }, [querySessionId]);

  useEffect(() => {
    if (!activeSessionId) {
      setSessionData(null);
      return;
    }

    const sessionId = activeSessionId;
    let cancelled = false;

    async function loadSession() {
      setIsLoadingSession(true);
      try {
        const payload = await getSession(sessionId);
        if (!cancelled) {
          setSessionData(payload);
          if (payload.analysis?.analysis_status === "completed") {
            setSetupState("ready");
          } else if (payload.session?.status === "draft") {
            setSetupState("created");
          }
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error ? error.message : "Не удалось загрузить workspace сессии.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSession(false);
        }
      }
    }

    loadSession();

    return () => {
      cancelled = true;
    };
  }, [activeSessionId]);

  useEffect(() => {
    const supported =
      typeof window !== "undefined" &&
      typeof navigator !== "undefined" &&
      typeof navigator.mediaDevices?.getUserMedia === "function" &&
      typeof MediaRecorder !== "undefined";
    setMediaSupported(Boolean(supported));
  }, []);

  useEffect(() => {
    return () => {
      if (recordedAudioUrl) {
        URL.revokeObjectURL(recordedAudioUrl);
      }
      if (questionAudioUrl) {
        URL.revokeObjectURL(questionAudioUrl);
      }
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, [questionAudioUrl, recordedAudioUrl]);

  async function replaceUrlSession(sessionId: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("session_id", sessionId);
    router.replace(`/?${params.toString()}`);
  }

  async function handleSetupSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setVoiceError(null);
    setSetupState("creating");
    setStatusMessage("Создаю session workspace и сохраняю параметры интервью.");

    const formData = new FormData(event.currentTarget);

    try {
      const created = await createSession({
        role: String(formData.get("role") ?? ""),
        seniority: String(formData.get("seniority") ?? ""),
        interview_type: String(formData.get("interview_type") ?? ""),
        interview_language: String(formData.get("interview_language") ?? ""),
        duration_minutes: Number(formData.get("duration_minutes") ?? 15),
        voice_mode: String(formData.get("voice_mode") ?? "On"),
      });

      const sessionId = created.session.id;
      setLocalSessionId(sessionId);
      setSessionData(created);
      await replaceUrlSession(sessionId);

      setSetupState("uploading");
      setStatusMessage("Привязываю резюме и вакансию к сессии.");
      const uploaded = await uploadSessionDocuments(sessionId, formData);
      setSessionData(uploaded);
      setSetupState("created");
      setStatusMessage("Документы сохранены. Следующий шаг — запустить AI analysis.");
    } catch (error) {
      setSetupState("error");
      setErrorMessage(
        error instanceof Error
          ? error.message.replace(/<[^>]*>/g, "").trim()
          : "Не удалось создать сессию и сохранить документы.",
      );
      setStatusMessage("Сценарий остановился. Исправьте ввод и повторите попытку.");
    }
  }

  async function handleAnalyze() {
    if (!activeSessionId) {
      return;
    }

    setErrorMessage(null);
    setSetupState("analyzing");
    setStatusMessage("Собираю deterministic intake и semantic HR snapshot.");

    try {
      const analyzed = await analyzeSession(activeSessionId);
      setSessionData(analyzed);
      setSetupState("ready");
      setStatusMessage("Анализ завершён. Можно переходить к mock interview.");
    } catch (error) {
      setSetupState("error");
      setErrorMessage(
        error instanceof Error
          ? error.message.replace(/<[^>]*>/g, "").trim()
          : "Не удалось выполнить AI analysis.",
      );
      setStatusMessage("Анализ не завершился. Попробуйте ещё раз.");
    }
  }

  async function handleStartInterview() {
    if (!activeSessionId) {
      return;
    }
    setIsStarting(true);
    setErrorMessage(null);
    try {
      const payload = await startInterview(activeSessionId);
      setSessionData(payload);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Не удалось запустить интервью.",
      );
    } finally {
      setIsStarting(false);
    }
  }

  async function handleSubmitAnswer() {
    if (!activeSessionId || !answerText.trim()) {
      return;
    }

    setIsSubmittingAnswer(true);
    setErrorMessage(null);
    try {
      const payload = await submitAnswer(activeSessionId, answerText.trim());
      setSessionData(payload);
      setAnswerText("");
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Не удалось сохранить ответ.",
      );
    } finally {
      setIsSubmittingAnswer(false);
    }
  }

  async function loadQuestionAudio(questionText?: string, force = false) {
    if (!activeSessionId || !sessionData?.session.current_question) {
      return;
    }

    const targetText = questionText ?? sessionData.session.current_question;
    if (!force && questionAudioForText === targetText && questionAudioUrl) {
      return;
    }

    setIsSynthesizing(true);
    setVoiceError(null);
    try {
      const payload = await synthesizeQuestionAudio(activeSessionId, targetText);
      const binary = window.atob(payload.audio_base64);
      const bytes = new Uint8Array(binary.length);
      for (let index = 0; index < binary.length; index += 1) {
        bytes[index] = binary.charCodeAt(index);
      }
      const audioBlob = new Blob([bytes], { type: payload.mime_type });
      if (questionAudioUrl) {
        URL.revokeObjectURL(questionAudioUrl);
      }
      setQuestionAudioUrl(URL.createObjectURL(audioBlob));
      setQuestionAudioForText(targetText);
    } catch (error) {
      setVoiceError(
        error instanceof Error ? error.message : "Не удалось сгенерировать озвучку вопроса.",
      );
    } finally {
      setIsSynthesizing(false);
    }
  }

  async function handleStartRecording() {
    if (!mediaSupported) {
      setVoiceError("В этом браузере запись с микрофона недоступна. Можно использовать файл или текстовый режим.");
      return;
    }

    setVoiceError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        recordedBlobRef.current = blob;
        if (recordedAudioUrl) {
          URL.revokeObjectURL(recordedAudioUrl);
        }
        setRecordedAudioUrl(URL.createObjectURL(blob));
        mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
        mediaStreamRef.current = null;
      };

      recorder.start();
      setIsRecording(true);
    } catch (error) {
      setVoiceError(
        error instanceof Error ? error.message : "Не удалось получить доступ к микрофону.",
      );
    }
  }

  function handleStopRecording() {
    if (!mediaRecorderRef.current) {
      return;
    }
    mediaRecorderRef.current.stop();
    setIsRecording(false);
  }

  async function handleTranscribeAudio() {
    if (!activeSessionId) {
      return;
    }

    let audioFile: File | null = null;
    if (selectedAudioFile) {
      audioFile = selectedAudioFile;
    } else if (recordedBlobRef.current) {
      audioFile = new File([recordedBlobRef.current], "voice-answer.webm", {
        type: recordedBlobRef.current.type || "audio/webm",
      });
    }

    if (!audioFile) {
      setVoiceError("Сначала запишите аудио или выберите файл.");
      return;
    }

    setIsTranscribing(true);
    setVoiceError(null);
    try {
      const payload = await transcribeSessionAudio(activeSessionId, audioFile);
      setAnswerText(payload.transcript);
    } catch (error) {
      setVoiceError(
        error instanceof Error ? error.message : "Не удалось распознать аудио.",
      );
    } finally {
      setIsTranscribing(false);
    }
  }

  function handleResetWorkspace() {
    setLocalSessionId(null);
    setSessionData(null);
    setAnswerText("");
    setErrorMessage(null);
    setVoiceError(null);
    setSetupState("idle");
    setStatusMessage(
      "Соберите контекст интервью: роль, резюме и вакансию. После этого появится HR snapshot и topics для mock interview.",
    );
    router.replace("/");
  }

  const session = sessionData?.session;
  const analysis = sessionData?.analysis;
  const workflow = sessionData?.workflow;
  const turns = sessionData?.turns ?? [];
  const finalReport = isFinalReport(workflow?.final_report) ? workflow.final_report : null;
  const currentStep = deriveStep(sessionData);
  const voiceModeEnabled = session?.voice_mode === "On";
  const currentTopic =
    workflow?.interview_plan?.[session?.question_cursor ?? 0]?.topic ??
    turns.at(-1)?.topic ??
    analysis?.interview_topics?.[0]?.topic ??
    "Interview topic";
  const progressTotal = Math.max(workflow?.interview_plan?.length ?? 0, 1);
  const progressDone = Math.min(turns.length, progressTotal);
  const progressPercent = Math.round((progressDone / progressTotal) * 100);
  const hrAnalysis = analysis?.hr_analysis;
  const matchedCount = analysis?.skill_gap_map?.matched_skills?.length ?? 0;
  const missingCount = analysis?.skill_gap_map?.missing_skills?.length ?? 0;
  const turnTrend = buildTurnTrend(turns);
  const latestTurn = turns.at(-1) ?? null;
  const showTraceButton = Boolean(workflow?.latest_trace?.length);
  const pipelineSteps = buildPipelineSteps(setupState);
  const currentQuestion =
    session?.current_question ??
    "Сессия ещё не запущена. После анализа можно стартовать интервью и получить первый вопрос.";
  const currentQuestionTurnIndex = turns.length + 1;

  useEffect(() => {
    if (!voiceModeEnabled || !session?.current_question || !activeSessionId) {
      return;
    }
    if (questionAudioForText === session.current_question && questionAudioUrl) {
      return;
    }
    loadQuestionAudio(session.current_question);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voiceModeEnabled, session?.current_question, activeSessionId]);

  const answerHelpText = useMemo(() => {
    if (voiceModeEnabled) {
      return "Ответ можно напечатать или продиктовать. Голосовые инструменты спрятаны в компактный tools-блок.";
    }
    return "Текстовый режим активен. В ответе лучше держать структуру: тезис, причина, пример, итог.";
  }, [voiceModeEnabled]);

  function renderWizardStepper() {
    const steps: Array<{ id: WorkspaceStep; label: string; kicker: string }> = [
      { id: "setup", label: "Setup", kicker: "Session" },
      { id: "analysis", label: "Analysis", kicker: "HR fit" },
      { id: "interview", label: "Interview", kicker: "Chat" },
      { id: "report", label: "Report", kicker: "Coaching" },
    ];
    const currentIndex = steps.findIndex((step) => step.id === currentStep);

    return (
      <div className="wizardStepper" aria-label="Interview workspace steps">
        {steps.map((step, index) => {
          const state =
            currentIndex === index ? "active" : currentIndex > index ? "done" : "idle";
          return (
            <article className={`wizardStep wizardStep-${state}`} key={step.id}>
              <span className="wizardStepIndex">{String(index + 1).padStart(2, "0")}</span>
              <div>
                <p className="wizardStepKicker">{step.kicker}</p>
                <strong>{step.label}</strong>
              </div>
            </article>
          );
        })}
      </div>
    );
  }

  function renderSummaryContent() {
    if (!sessionData) {
      return (
        <>
          <article className="workspaceCard">
            <SectionHeader
              eyebrow="Workspace"
              title="Wizard flow"
              description="Setup, analysis, interview и report теперь живут в одном shell без потери контекста."
              size="compact"
            />
            <div className="summaryStats">
              <div className="summaryStat">
                <span>Mode</span>
                <strong>chat-first</strong>
              </div>
              <div className="summaryStat">
                <span>Trace</span>
                <strong>drawer</strong>
              </div>
            </div>
          </article>
          <article className="workspaceCard">
            <SectionHeader
              eyebrow="Design notes"
              title="Что изменилось"
              description="Меньше тяжёлых панелей, больше одного доминирующего действия на экран."
              size="compact"
            />
            <ul className="listClean">
              <li>Setup и HR analysis не теряются между страницами.</li>
              <li>Интервью превращается в chat transcript, а не timeline dump.</li>
              <li>Итоговый report строится как graph + coaching view.</li>
            </ul>
          </article>
        </>
      );
    }

    return (
      <>
        <article className="workspaceCard">
          <SectionHeader
            eyebrow="Session snapshot"
            title={`${session?.role ?? "Interview"} / ${session?.seniority ?? "n/a"}`}
            description={`Mode: ${session?.interview_type ?? "Mixed"} · Voice: ${session?.voice_mode ?? "Off"}`}
            size="compact"
            aside={<Badge tone={session?.status === "completed" ? "success" : "accent"}>{formatStatusLabel(session?.status)}</Badge>}
          />
          <div className="summaryStats">
            <div className="summaryStat">
              <span>Progress</span>
              <strong>{progressDone}/{progressTotal}</strong>
            </div>
            <div className="summaryStat">
              <span>Missing</span>
              <strong>{missingCount}</strong>
            </div>
            <div className="summaryStat">
              <span>Match</span>
              <strong>{hrAnalysis?.overall_match_score_pct ?? 0}%</strong>
            </div>
          </div>
        </article>

        <article className="workspaceCard">
          <SectionHeader
            eyebrow="Current focus"
            title={currentTopic}
            description="Компактный контекст остаётся рядом на шаге интервью и в финальном отчёте."
            size="compact"
          />
          <div className="progressLine" aria-hidden="true">
            <span style={{ width: `${progressPercent}%` }} />
          </div>
          <p className="bodyMuted">
            {latestTurn?.evaluation_summary?.follow_up_needed
              ? "Последний ответ ещё тянет на follow-up или уточнение."
              : "Текущий поток движется к следующей теме или к финальному отчёту."}
          </p>
        </article>

        <HrSnapshot hrAnalysis={hrAnalysis} />
      </>
    );
  }

  function renderSummaryRail() {
    return (
      <details className="workspaceRail" open>
        <summary className="workspaceRailToggle">Context summary</summary>
        <div className="workspaceRailBody">{renderSummaryContent()}</div>
      </details>
    );
  }

  function renderTraceDrawer() {
    if (!workflow?.latest_trace?.length || !isTraceOpen) {
      return null;
    }

    return (
      <section className="devDrawer fadeUp">
        <SectionHeader
          eyebrow="Dev / Trace"
          title="Workflow trace"
          description="Эта панель спрятана из основного UX, но остаётся под рукой для защиты и отладки."
          size="compact"
        />
        <div className="traceDrawerList">
          {workflow.latest_trace.map((event, index) => (
            <article className="traceDrawerItem" key={`${event.node}-${event.timestamp}-${index}`}>
              <div className="traceDrawerMeta">
                <Badge tone="neutral">{event.node}</Badge>
                <span>{new Date(event.timestamp).toLocaleTimeString("ru-RU")}</span>
              </div>
              <strong>{event.summary}</strong>
              {event.details ? (
                <pre className="traceCode">{JSON.stringify(event.details, null, 2)}</pre>
              ) : null}
            </article>
          ))}
        </div>
      </section>
    );
  }

  function renderSetupStep() {
    if (activeSessionId && sessionData) {
      return (
        <section className="workspaceCard workspaceCardLarge fadeUp">
          <SectionHeader
            eyebrow="Setup"
            title="Сессия уже создана"
            description="Документы и параметры уже сохранены. Отсюда можно запустить анализ и перейти к recruiter snapshot."
            aside={<Badge tone={statusTone(setupState)}>state: {setupState}</Badge>}
          />

          <div className="setupReviewGrid">
            <article className="workspaceCard workspaceCardInset">
              <p className="miniLabel">Session context</p>
              <div className="infoList">
                <div className="infoItem">
                  <span>Role</span>
                  <strong>{sessionData.session.role}</strong>
                </div>
                <div className="infoItem">
                  <span>Interview mode</span>
                  <strong>{sessionData.session.interview_type}</strong>
                </div>
                <div className="infoItem">
                  <span>Voice mode</span>
                  <strong>{sessionData.session.voice_mode}</strong>
                </div>
              </div>
            </article>

            <article className="workspaceCard workspaceCardInset">
              <p className="miniLabel">Documents</p>
              <div className="infoList">
                <div className="infoItem">
                  <span>Resume</span>
                  <strong>{sessionData.documents.resume_filename || "Не загружено"}</strong>
                </div>
                <div className="infoItem">
                  <span>Vacancy URL</span>
                  <strong>{sessionData.documents.vacancy_url || "Не указано"}</strong>
                </div>
                <div className="infoItem">
                  <span>Vacancy text</span>
                  <strong>
                    {sessionData.documents.vacancy_text
                      ? `${sessionData.documents.vacancy_text.length} chars`
                      : "Не добавлен"}
                  </strong>
                </div>
              </div>
            </article>
          </div>

          <div className="pipelineStrip">
            {pipelineSteps.map((step) => (
              <div className={`pipelineChip pipelineChip-${step.state}`} key={step.label}>
                <span className="pipelineDot" />
                {step.label}
              </div>
            ))}
          </div>

          <div className={`statusBanner statusBanner-${statusTone(setupState)}`}>
            <div>
              <p className="statusKicker">Workflow status</p>
              <p>{statusMessage}</p>
            </div>
            <div className="buttonRow">
              <button
                className="button buttonPrimary"
                type="button"
                onClick={handleAnalyze}
                disabled={setupState === "analyzing"}
              >
                {setupState === "analyzing" ? (
                  <>
                    <ButtonSpinner />
                    Строю анализ
                  </>
                ) : (
                  "Запустить анализ"
                )}
              </button>
              <button className="button buttonGhost" type="button" onClick={handleResetWorkspace}>
                Новая сессия
              </button>
            </div>
          </div>
        </section>
      );
    }

    return (
      <section className="workspaceCard workspaceCardLarge fadeUp">
        <SectionHeader
          eyebrow="Setup"
          title="Создайте интервью в одном workspace"
          description="Здесь нет отдельного landing screen: сразу собираем session context, документы и готовим переход к AI analysis."
          aside={<Badge tone={statusTone(setupState)}>state: {setupState}</Badge>}
        />

        <form className="wizardForm" onSubmit={handleSetupSubmit}>
          <div className="wizardFormGrid">
            <label className="fieldGroup">
              <span className="fieldLabel">Роль</span>
              <select className="inputSurface select" name="role" defaultValue="Frontend Developer" required>
                <option>Frontend Developer</option>
              </select>
            </label>

            <label className="fieldGroup">
              <span className="fieldLabel">Seniority</span>
              <select className="inputSurface select" name="seniority" defaultValue="Middle" required>
                <option>Junior</option>
                <option>Middle</option>
              </select>
            </label>

            <label className="fieldGroup">
              <span className="fieldLabel">Формат интервью</span>
              <select className="inputSurface select" name="interview_type" defaultValue="Mixed" required>
                <option>Technical Core</option>
                <option>Behavioural</option>
                <option>Mixed</option>
              </select>
            </label>

            <label className="fieldGroup">
              <span className="fieldLabel">Язык</span>
              <select className="inputSurface select" name="interview_language" defaultValue="Russian" required>
                <option>Russian</option>
                <option>English</option>
              </select>
            </label>

            <label className="fieldGroup">
              <span className="fieldLabel">Длительность</span>
              <input
                className="inputSurface input"
                type="number"
                name="duration_minutes"
                min={5}
                max={45}
                defaultValue={15}
                required
              />
            </label>

            <label className="fieldGroup">
              <span className="fieldLabel">Voice mode</span>
              <select className="inputSurface select" name="voice_mode" defaultValue="On" required>
                <option>On</option>
                <option>Off</option>
              </select>
            </label>
          </div>

          <div className="wizardUploadGrid">
            <label className="fieldGroup">
              <span className="fieldLabel">Резюме</span>
              <span className="fieldHint">PDF или DOCX.</span>
              <input className="inputSurface fileInput" type="file" name="resume" accept=".pdf,.doc,.docx" />
            </label>

            <label className="fieldGroup">
              <span className="fieldLabel">URL вакансии</span>
              <input className="inputSurface input" type="url" name="vacancy_url" placeholder="https://example.com/job" />
            </label>
          </div>

          <label className="fieldGroup">
            <span className="fieldLabel">Текст вакансии</span>
            <span className="fieldHint">Достаточно требований, стеков и ожиданий от кандидата.</span>
            <textarea
              className="inputSurface textarea workspaceTextarea"
              name="vacancy_text"
              rows={8}
              placeholder="Вставьте описание вакансии, требования к стеку и ожидания от кандидата"
            />
          </label>

          <div className="pipelineStrip">
            {pipelineSteps.map((step) => (
              <div className={`pipelineChip pipelineChip-${step.state}`} key={step.label}>
                <span className="pipelineDot" />
                {step.label}
              </div>
            ))}
          </div>

          <div className={`statusBanner statusBanner-${statusTone(setupState)}`}>
            <div>
              <p className="statusKicker">Pipeline</p>
              <p>{statusMessage}</p>
            </div>
            <button
              className="button buttonPrimary"
              type="submit"
              disabled={setupState === "creating" || setupState === "uploading"}
            >
              {setupState === "creating" || setupState === "uploading" ? (
                <>
                  <ButtonSpinner />
                  Сохраняю
                </>
              ) : (
                "Создать сессию"
              )}
            </button>
          </div>
        </form>
      </section>
    );
  }

  function renderAnalysisStep() {
    if (!analysis) {
      return (
        <section className="workspaceCard workspaceCardLarge fadeUp">
          <EmptyState
            title="Анализ ещё не построен"
            description="Сначала завершите setup и запустите AI analysis."
          />
        </section>
      );
    }

    return (
      <section className="workspaceCard workspaceCardLarge fadeUp">
        <SectionHeader
          eyebrow="Analysis"
          title="Recruiter snapshot и interview focus"
          description="Этот шаг показывает mismatch между вакансией и профилем, а затем отдаёт темы в mock interview."
          aside={<Badge tone="success">analysis ready</Badge>}
        />

        <div className="workspaceMetricRow">
          <MetricCard label="Match score" value={`${hrAnalysis?.overall_match_score_pct ?? 0}%`} hint="Сводный HR fit." tone="accent" />
          <MetricCard label="Interview chance" value={`${hrAnalysis?.interview_probability_pct ?? 0}%`} hint="Вероятность пройти на интервью." tone={(hrAnalysis?.interview_probability_pct ?? 0) < 50 ? "warning" : "success"} />
          <MetricCard label="Missing skills" value={missingCount} hint="Наиболее заметный gap под вакансию." tone="warning" />
          <MetricCard label="Risk" value={formatRiskLabel(analysis.skill_gap_map?.risk_level)} hint="Общий риск mismatch." tone="neutral" />
        </div>

        <div className="analysisCompactGrid">
          <article className="workspaceCard workspaceCardInset">
            <SectionHeader
              eyebrow="Verdict"
              title={hrAnalysis?.hr_verdict || "HR verdict пока пустой"}
              description={hrAnalysis?.market_competitiveness || hrAnalysis?.message || "Краткая recruiter оценка."}
              size="compact"
            />
            <div className="infoList">
              <div className="infoItem">
                <span>Candidate level</span>
                <strong>{hrAnalysis?.candidate_level || "Не определён"}</strong>
              </div>
              <div className="infoItem">
                <span>Vacancy level</span>
                <strong>{hrAnalysis?.vacancy_level || "Не определён"}</strong>
              </div>
              <div className="infoItem">
                <span>Risk of rejection</span>
                <strong>{hrAnalysis?.risk_of_rejection || "Не определён"}</strong>
              </div>
            </div>
          </article>

          <article className="workspaceCard workspaceCardInset">
            <SectionHeader eyebrow="Strengths" title="Почему кандидат выглядит сильнее" size="compact" />
            {renderList(hrAnalysis?.strong_sides ?? [])}
          </article>

          <article className="workspaceCard workspaceCardInset workspaceCardWarning">
            <SectionHeader eyebrow="Risks" title="Что recruiter заметит как слабое место" size="compact" />
            {renderList(hrAnalysis?.weak_sides ?? [])}
          </article>
        </div>

        <div className="analysisCompactGrid">
          <article className="workspaceCard workspaceCardInset">
            <SectionHeader eyebrow="Missing skills" title="Что стоит подтянуть" size="compact" />
            {renderChips(analysis.skill_gap_map?.missing_skills ?? [], "warning")}
          </article>

          <article className="workspaceCard workspaceCardInset">
            <SectionHeader eyebrow="ATS keywords" title="Каких слов не хватает" size="compact" />
            <div className="stackSection">
              <p className="miniLabel">Present</p>
              {renderChips(hrAnalysis?.ats_keyword_analysis?.present_keywords ?? [], "success")}
            </div>
            <div className="stackSection">
              <p className="miniLabel">Missing</p>
              {renderChips(hrAnalysis?.ats_keyword_analysis?.missing_keywords ?? [], "warning")}
            </div>
          </article>
        </div>

        <article className="workspaceCard workspaceCardInset">
          <SectionHeader
            eyebrow="Interview topics"
            title="Темы, которые пойдут в mock interview"
            description="Компактный пул тем с приоритетом, а не тяжёлый dashboard."
            size="compact"
          />
          <div className="topicPillGrid">
            {analysis.interview_topics.map((topic) => (
              <article className="topicPillCard" key={topic.topic}>
                <div className="topicPillTop">
                  <strong>{topic.topic}</strong>
                  <Badge tone={topic.priority === "high" ? "accent" : "neutral"}>{topic.priority}</Badge>
                </div>
                <p>{topic.reason}</p>
                <div className="topicMeta">
                  <span>{topic.interview_type}</span>
                  <span>{topic.expected_difficulty}</span>
                </div>
              </article>
            ))}
          </div>
        </article>

        {(hrAnalysis?.rewritten_resume_fragments ?? []).length ? (
          <article className="workspaceCard workspaceCardInset">
            <SectionHeader
              eyebrow="Resume rewrite"
              title="Фрагменты, которые можно усилить"
              description="Вместо длинной стены текста — компактные accordion-блоки."
              size="compact"
            />
            <div className="accordionList">
              {(hrAnalysis?.rewritten_resume_fragments ?? []).map((fragment, index) => (
                <details className="accordionItem" key={`${fragment.section_title}-${index}`}>
                  <summary>
                    <span>{fragment.section_title || `Fragment ${index + 1}`}</span>
                    <Badge tone="neutral">rewrite</Badge>
                  </summary>
                  <div className="accordionBody">
                    <div className="rewriteBlock">
                      <p className="miniLabel">Original</p>
                      <p>{fragment.original_excerpt || "Исходный фрагмент не передан."}</p>
                    </div>
                    <div className="rewriteBlock">
                      <p className="miniLabel">Rewritten</p>
                      <p>{fragment.rewritten_version}</p>
                    </div>
                    <div className="rewriteBlock">
                      <p className="miniLabel">Rationale</p>
                      <p>{fragment.rationale}</p>
                    </div>
                  </div>
                </details>
              ))}
            </div>
          </article>
        ) : null}

        <div className="buttonRow">
          <button className="button buttonPrimary" type="button" onClick={handleStartInterview} disabled={isStarting}>
            {isStarting ? (
              <>
                <ButtonSpinner />
                Запускаю интервью
              </>
            ) : (
              "Перейти к интервью"
            )}
          </button>
          <button className="button buttonGhost" type="button" onClick={handleResetWorkspace}>
            Новая сессия
          </button>
        </div>
      </section>
    );
  }

  function renderChatMessages() {
    if (!turns.length && !session?.current_question) {
      return (
        <EmptyState
          title="Чат интервью ещё пустой"
          description="После запуска интервью здесь появится первый AI-вопрос, а потом история turn-by-turn."
        />
      );
    }

    return (
      <div className="chatTranscript">
        {turns.map((turn) => (
          <div className="chatTurn" key={turn.turn_index}>
            <article className="chatMessage chatMessageAi fadeUp">
              <div className="chatMeta">
                <Badge tone="accent">AI</Badge>
                <span>Turn {turn.turn_index} · {questionKindLabel(turn.question_kind)}</span>
              </div>
              <p>{turn.question}</p>
              {turn.topic ? <div className="chatTopic">{turn.topic}</div> : null}
            </article>

            <article className="chatMessage chatMessageUser fadeUp">
              <div className="chatMeta">
                <Badge tone="neutral">You</Badge>
                <span>{new Date(turn.created_at).toLocaleTimeString("ru-RU")}</span>
              </div>
              <p>{turn.answer}</p>
            </article>

            <article className="chatMessage chatMessageCoach fadeUp">
              <div className="chatMeta">
                <Badge tone="success">Coach</Badge>
                <span>
                  {typeof turn.evaluation_summary?.score_0_10 === "number"
                    ? `${turn.evaluation_summary.score_0_10}/10`
                    : "feedback"}
                </span>
              </div>
              <p>{turn.feedback}</p>
            </article>
          </div>
        ))}

        {session?.status !== "completed" && session?.current_question ? (
          <article className="chatMessage chatMessageAi chatMessagePending fadeUp">
            <div className="chatMeta">
              <Badge tone="accent">AI</Badge>
              <span>Turn {currentQuestionTurnIndex} · pending</span>
            </div>
            <p>{session.current_question}</p>
            {currentTopic ? <div className="chatTopic">{currentTopic}</div> : null}
          </article>
        ) : null}
      </div>
    );
  }

  function renderInterviewStep() {
    return (
      <section className="workspaceCard workspaceCardLarge fadeUp">
        <SectionHeader
          eyebrow="Interview"
          title="Mock interview как chat transcript"
          description="Текущий вопрос не вырывается в отдельный oversized hero. Он живёт в потоке вместе с ответами и компактным coach feedback."
          aside={<Badge tone="accent">{progressDone}/{progressTotal} topics</Badge>}
        />

        <div className="interviewLayout">
          <div className="chatSurface">{renderChatMessages()}</div>

          <div className="composerSurface">
            <SectionHeader eyebrow="Answer composer" title="Ваш ответ" description={answerHelpText} size="compact" />

            {voiceModeEnabled ? (
              <details className="toolAccordion">
                <summary>
                  <span>Voice tools</span>
                  <Badge tone={mediaSupported ? "success" : "warning"}>
                    {mediaSupported ? "mic ready" : "file mode"}
                  </Badge>
                </summary>
                <div className="toolAccordionBody">
                  <div className="buttonRow">
                    <button
                      className="button buttonSecondary"
                      type="button"
                      onClick={isRecording ? handleStopRecording : handleStartRecording}
                      disabled={isSubmittingAnswer || isTranscribing}
                    >
                      {isRecording ? (
                        <>
                          <ButtonSpinner />
                          Остановить запись
                        </>
                      ) : (
                        "Начать запись"
                      )}
                    </button>
                    <button
                      className="button buttonGhost"
                      type="button"
                      onClick={handleTranscribeAudio}
                      disabled={isSubmittingAnswer || isTranscribing}
                    >
                      {isTranscribing ? (
                        <>
                          <ButtonSpinner />
                          Распознаю
                        </>
                      ) : (
                        "Распознать и вставить"
                      )}
                    </button>
                  </div>

                  <label className="fieldGroup">
                    <span className="fieldLabel">Или выбрать готовый аудиофайл</span>
                    <input
                      className="inputSurface fileInput"
                      type="file"
                      accept="audio/*,.webm,.wav,.m4a,.mp3"
                      onChange={(event) => {
                        const file = event.target.files?.[0] ?? null;
                        setSelectedAudioFile(file);
                        if (file) {
                          if (recordedAudioUrl) {
                            URL.revokeObjectURL(recordedAudioUrl);
                          }
                          setRecordedAudioUrl(URL.createObjectURL(file));
                          recordedBlobRef.current = file;
                        }
                      }}
                    />
                  </label>

                  {recordedAudioUrl ? (
                    <audio className="audioPlayer" controls src={recordedAudioUrl}>
                      Ваш браузер не поддерживает аудио-плеер.
                    </audio>
                  ) : null}

                  <div className="buttonRow">
                    <button
                      className="button buttonGhost"
                      type="button"
                      onClick={() => loadQuestionAudio(session?.current_question ?? "", true)}
                      disabled={isSynthesizing}
                    >
                      {isSynthesizing ? (
                        <>
                          <ButtonSpinner />
                          Озвучиваю вопрос
                        </>
                      ) : (
                        "Озвучить текущий вопрос"
                      )}
                    </button>
                  </div>

                  {questionAudioUrl ? (
                    <audio className="audioPlayer" controls src={questionAudioUrl}>
                      Ваш браузер не поддерживает аудио-плеер.
                    </audio>
                  ) : null}
                </div>
              </details>
            ) : null}

            <textarea
              className="inputSurface textarea workspaceAnswerField"
              rows={7}
              placeholder="Сформулируй ответ как на реальном интервью: тезис, причина, пример, компромисс, итог."
              value={answerText}
              onChange={(event) => setAnswerText(event.target.value)}
              disabled={isSubmittingAnswer || session?.status === "completed"}
            />

            <div className="buttonRow">
              <button
                className="button buttonPrimary"
                type="button"
                onClick={handleSubmitAnswer}
                disabled={isSubmittingAnswer || session?.status === "completed" || !answerText.trim()}
              >
                {isSubmittingAnswer ? (
                  <>
                    <ButtonSpinner />
                    Отправляю ответ
                  </>
                ) : (
                  "Отправить ответ"
                )}
              </button>
            </div>
          </div>
        </div>
      </section>
    );
  }

  function renderReportStep() {
    const strengths = finalReport?.strengths ?? [];
    const gaps = finalReport?.gaps ?? [];
    const topics = finalReport?.topics_to_review ?? [];
    const coaching = finalReport?.coaching;

    return (
      <section className="workspaceCard workspaceCardLarge fadeUp">
        <SectionHeader
          eyebrow="Report"
          title="Graph-first review и coaching"
          description="Итоговый экран теперь подаёт результат как score summary, turn trend и конкретные next steps."
          aside={<Badge tone="success">{finalReport?.final_score_0_10 ?? 0}/10</Badge>}
        />

        <div className="reportHeroGrid">
          <RingScore label="Final interview score" value={finalReport?.final_score_0_10 ?? 0} />

          <article className="workspaceCard workspaceCardInset">
            <SectionHeader
              eyebrow="Session summary"
              title="Краткий итог"
              description={finalReport?.summary ?? "Report summary"}
              size="compact"
            />
            <div className="summaryStats">
              <div className="summaryStat">
                <span>Strengths</span>
                <strong>{strengths.length}</strong>
              </div>
              <div className="summaryStat">
                <span>Growth areas</span>
                <strong>{gaps.length}</strong>
              </div>
              <div className="summaryStat">
                <span>Practice prompts</span>
                <strong>{finalReport?.questions_to_practice.length ?? 0}</strong>
              </div>
            </div>
            <div className="stackSection">
              <p className="miniLabel">Topics to review</p>
              {renderChips(topics, "neutral")}
            </div>
          </article>
        </div>

        {turnTrend.length ? (
          <article className="workspaceCard workspaceCardInset">
            <SectionHeader
              eyebrow="Turn trend"
              title="Как менялось качество ответов"
              description="Новый report использует turn-level evaluation history, а не только финальные aggregate поля."
              size="compact"
            />
            <TrendBars items={turnTrend} />
          </article>
        ) : null}

        <div className="reportGrid">
          <article className="workspaceCard workspaceCardInset">
            <SectionHeader eyebrow="Strengths" title="Что уже звучит уверенно" size="compact" />
            {renderList(strengths)}
          </article>

          <article className="workspaceCard workspaceCardInset workspaceCardWarning">
            <SectionHeader eyebrow="Growth" title="Что стоит подтянуть" size="compact" />
            {renderList(gaps)}
          </article>
        </div>

        <article className="workspaceCard workspaceCardInset">
          <SectionHeader eyebrow="Practice prompts" title="Что потренировать следующим" size="compact" />
          {renderList(finalReport?.questions_to_practice ?? [])}
        </article>

        {coaching ? (
          <div className="reportGrid">
            <article className="workspaceCard workspaceCardInset">
              <SectionHeader eyebrow="Coach" title="Что получилось хорошо" size="compact" />
              {renderList(coaching.what_was_good)}
            </article>
            <article className="workspaceCard workspaceCardInset">
              <SectionHeader eyebrow="Coach" title="Что стоит усилить" size="compact" />
              {renderList(coaching.what_was_weak)}
            </article>
            <article className="workspaceCard workspaceCardInset">
              <SectionHeader eyebrow="Coach" title="Как улучшить ответ" size="compact" />
              {renderList(coaching.how_to_improve)}
            </article>
            <article className="workspaceCard workspaceCardInset">
              <SectionHeader eyebrow="Coach" title="Какие drills прогнать" size="compact" />
              {renderList(coaching.recommended_drills)}
            </article>
          </div>
        ) : null}

        <div className="buttonRow">
          <button className="button buttonPrimary" type="button" onClick={handleResetWorkspace}>
            Создать новую сессию
          </button>
        </div>
      </section>
    );
  }

  return (
    <main className="workspaceShell">
      <section className="workspaceHeader fadeUp">
        <div className="workspaceHeaderCopy">
          <div className="heroBadgeRow">
            <Badge tone="live">Interview Workspace</Badge>
            <Badge tone="neutral">wizard + chat-first</Badge>
          </div>
          <h1 className="workspaceTitle">AI workspace для подготовки к техническому интервью</h1>
          <p className="workspaceLead">
            Один shell для setup, HR analysis, mock interview и финального разбора.
          </p>
        </div>

        <div className="workspaceHeaderActions">
          {showTraceButton ? (
            <button className="button buttonGhost" type="button" onClick={() => setIsTraceOpen((value) => !value)}>
              {isTraceOpen ? "Скрыть Dev / Trace" : "Открыть Dev / Trace"}
            </button>
          ) : null}
          {sessionData ? (
            <button className="button buttonSecondary" type="button" onClick={handleResetWorkspace}>
              Новая сессия
            </button>
          ) : null}
        </div>
      </section>

      {renderWizardStepper()}
      {renderTraceDrawer()}

      {errorMessage ? <div className="statusBanner statusBannerError fadeUp">{errorMessage}</div> : null}
      {voiceError ? <div className="statusBanner statusBannerWarning fadeUp">{voiceError}</div> : null}

      {isLoadingSession && activeSessionId && !sessionData ? (
        <section className="workspaceCard workspaceCardLarge fadeUp">
          <EmptyState
            title="Загружаю workspace"
            description="Подтягиваю session state, HR analysis, turns и workflow trace."
          />
        </section>
      ) : (
        <div className="workspaceGrid fadeUp">
          <div className="workspaceMain">
            {currentStep === "setup" ? renderSetupStep() : null}
            {currentStep === "analysis" ? renderAnalysisStep() : null}
            {currentStep === "interview" ? renderInterviewStep() : null}
            {currentStep === "report" ? renderReportStep() : null}
          </div>

          <aside className="workspaceAside">{renderSummaryRail()}</aside>
        </div>
      )}
    </main>
  );
}

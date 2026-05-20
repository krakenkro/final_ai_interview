"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  getSession,
  startInterview,
  submitAnswer,
  synthesizeQuestionAudio,
  transcribeSessionAudio,
} from "@/lib/api";
import type { SessionPayload } from "@/lib/types";
import { Badge, EmptyState, MetricCard, SectionHeader } from "@/components/ui/primitives";

function formatStatusLabel(value: string | null | undefined) {
  if (!value) {
    return "draft";
  }

  return value.replaceAll("_", " ");
}

function traceTone(node: string) {
  if (node === "report" || node === "feedback") {
    return "success";
  }
  if (node === "interviewer" || node === "planner") {
    return "accent";
  }
  return "neutral";
}

export function InterviewSessionView() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");

  const [sessionData, setSessionData] = useState<SessionPayload | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(null);
  const [questionAudioUrl, setQuestionAudioUrl] = useState<string | null>(null);
  const [questionAudioForText, setQuestionAudioForText] = useState<string | null>(null);
  const [selectedAudioFile, setSelectedAudioFile] = useState<File | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [mediaSupported, setMediaSupported] = useState(true);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordedBlobRef = useRef<Blob | null>(null);

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const currentSessionId = sessionId;
    let cancelled = false;

    async function loadSession() {
      try {
        const payload = await getSession(currentSessionId);
        if (!cancelled) {
          setSessionData(payload);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error ? error.message : "Не удалось загрузить сессию.",
          );
        }
      }
    }

    loadSession();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

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

  async function handleStart() {
    if (!sessionId) {
      return;
    }

    setIsBusy(true);
    setErrorMessage(null);
    try {
      const payload = await startInterview(sessionId);
      setSessionData(payload);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Не удалось запустить интервью.",
      );
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSubmitAnswer() {
    if (!sessionId || !answerText.trim()) {
      return;
    }

    setIsBusy(true);
    setErrorMessage(null);
    try {
      const payload = await submitAnswer(sessionId, answerText.trim());
      setSessionData(payload);
      setAnswerText("");
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Не удалось сохранить ответ.",
      );
    } finally {
      setIsBusy(false);
    }
  }

  async function loadQuestionAudio(questionText?: string, force = false) {
    if (!sessionId || !sessionData?.session.current_question) {
      return;
    }

    const targetText = questionText ?? sessionData.session.current_question;
    if (!force && questionAudioForText === targetText && questionAudioUrl) {
      return;
    }

    setIsSynthesizing(true);
    setVoiceError(null);
    try {
      const payload = await synthesizeQuestionAudio(sessionId, targetText);
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
    if (!sessionId) {
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
      const payload = await transcribeSessionAudio(sessionId, audioFile);
      setAnswerText(payload.transcript);
    } catch (error) {
      setVoiceError(
        error instanceof Error ? error.message : "Не удалось распознать аудио.",
      );
    } finally {
      setIsTranscribing(false);
    }
  }

  if (!sessionId) {
    return (
      <section className="surfacePanel fadeUp">
        <EmptyState
          title="Сессия не найдена"
          description="Вернитесь на главный экран, создайте новую сессию и затем откройте interview workspace."
        />
        <div className="inlineActions">
          <Link className="button buttonSecondary" href="/">
            Вернуться к настройке
          </Link>
        </div>
      </section>
    );
  }

  const session = sessionData?.session;
  const analysis = sessionData?.analysis;
  const workflow = sessionData?.workflow;
  const turns = sessionData?.turns ?? [];
  const voiceModeEnabled = session?.voice_mode === "On";
  const hrAnalysis = analysis?.hr_analysis;
  const finalReport =
    workflow?.final_report && "summary" in workflow.final_report
      ? workflow.final_report
      : null;
  const coaching = finalReport?.coaching;
  const currentQuestion =
    session?.current_question ??
    "Сессия ещё не запущена. Когда будешь готова, нажми кнопку запуска ниже.";
  const topicCount = analysis?.interview_topics?.length ?? 0;
  const missingCount = analysis?.skill_gap_map?.missing_skills?.length ?? 0;

  const answerHelpText = useMemo(() => {
    if (voiceModeEnabled) {
      return "Можно надиктовать ответ, получить транскрипт и быстро отредактировать его перед отправкой.";
    }
    return "Сейчас доступен текстовый режим. Voice layer можно включить на экране настройки сессии.";
  }, [voiceModeEnabled]);

  useEffect(() => {
    if (!voiceModeEnabled || !session?.current_question || !sessionId) {
      return;
    }
    if (questionAudioForText === session.current_question && questionAudioUrl) {
      return;
    }
    loadQuestionAudio(session.current_question);
  }, [
    questionAudioForText,
    questionAudioUrl,
    session?.current_question,
    sessionId,
    voiceModeEnabled,
  ]);

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

  return (
    <div className="pageStack">
      <section className="heroPanel heroPanelCompact fadeUp">
        <div className="heroGrid">
          <div className="heroCopy">
            <div className="heroBadgeRow">
              <Badge tone="live">{formatStatusLabel(session?.status)}</Badge>
              <Badge tone="neutral">{session?.interview_type ?? "Interview"}</Badge>
              <Badge tone={voiceModeEnabled ? "accent" : "neutral"}>
                voice {voiceModeEnabled ? "on" : "off"}
              </Badge>
            </div>
            <h1 className="heroTitle heroTitleCompact">
              {session ? `${session.role} / ${session.seniority}` : "Interview workspace"}
            </h1>
            <p className="heroLead">
              {session
                ? "Это рабочая консоль интервью: текущий вопрос, answer composer, voice tools, trace и итоговый coaching report."
                : "Подтягиваю состояние сессии и workflow."}
            </p>
          </div>

          <div className="heroMetrics heroMetricsCompact">
            <MetricCard
              label="Topics"
              value={topicCount}
              hint="Темы, которые анализ передал в interview planner."
              tone="accent"
            />
            <MetricCard
              label="Turns"
              value={turns.length}
              hint="Сколько question-answer шагов уже прошло."
              tone="neutral"
            />
            <MetricCard
              label="Missing skills"
              value={missingCount}
              hint="Ключевой mismatch между резюме и вакансией."
              tone={missingCount > 0 ? "warning" : "success"}
            />
          </div>
        </div>
      </section>

      {errorMessage ? <div className="statusBanner statusBannerError fadeUp">{errorMessage}</div> : null}
      {voiceError ? <div className="statusBanner statusBannerWarning fadeUp">{voiceError}</div> : null}

      <div className="dashboardGrid fadeUp">
        <div className="mainColumn">
          <section className="surfacePanel">
            <SectionHeader
              eyebrow="Current prompt"
              title="Текущий вопрос"
              description="Главный фокус интерфейса. Здесь интервьюерский prompt должен считываться мгновенно."
              aside={<Badge tone="accent">{formatStatusLabel(session?.status)}</Badge>}
            />

            <div className="questionStage">
              <div className="questionDisplay">
                <p className="questionText">{currentQuestion}</p>
              </div>

              {voiceModeEnabled && session?.current_question ? (
                <div className="voicePanel">
                  <div className="voicePanelHeader">
                    <div>
                      <strong>Озвучка вопроса</strong>
                      <p className="bodyMuted">fal.ai MiniMax Speech 02 HD</p>
                    </div>
                    <button
                      className="button buttonGhost"
                      type="button"
                      onClick={() => loadQuestionAudio(session.current_question ?? "", true)}
                      disabled={isSynthesizing}
                    >
                      {isSynthesizing ? "Генерирую..." : "Обновить озвучку"}
                    </button>
                  </div>
                  {questionAudioUrl ? (
                    <audio className="audioPlayer" controls src={questionAudioUrl}>
                      Ваш браузер не поддерживает аудио-плеер.
                    </audio>
                  ) : (
                    <div className="miniEmptyState">Аудио вопроса появится после первого синтеза.</div>
                  )}
                </div>
              ) : null}

              <div className="buttonRow">
                <button
                  className="button buttonPrimary"
                  type="button"
                  onClick={handleStart}
                  disabled={
                    isBusy ||
                    session?.status === "completed" ||
                    analysis?.analysis_status === "not_started" ||
                    session?.status === "in_progress"
                  }
                >
                  {session?.status === "in_progress"
                    ? "Интервью уже запущено"
                    : session?.status === "completed"
                      ? "Интервью завершено"
                      : "Запустить интервью"}
                </button>
                <Link className="button buttonSecondary" href="/">
                  Вернуться к настройке
                </Link>
              </div>
            </div>
          </section>

          <section className="surfacePanel">
            <SectionHeader
              eyebrow="Answer composer"
              title="Ваш ответ"
              description={answerHelpText}
            />

            {voiceModeEnabled ? (
              <div className="voicePanel">
                <div className="voicePanelHeader">
                  <div>
                    <strong>Голосовой ответ</strong>
                    <p className="bodyMuted">Запись, загрузка файла и STT в одном блоке.</p>
                  </div>
                  <Badge tone={mediaSupported ? "success" : "warning"}>
                    {mediaSupported ? "mic ready" : "file mode"}
                  </Badge>
                </div>

                <div className="buttonRow">
                  <button
                    className="button buttonSecondary"
                    type="button"
                    onClick={isRecording ? handleStopRecording : handleStartRecording}
                    disabled={isBusy || isTranscribing}
                  >
                    {isRecording ? "Остановить запись" : "Начать запись"}
                  </button>
                  <button
                    className="button buttonGhost"
                    type="button"
                    onClick={handleTranscribeAudio}
                    disabled={isBusy || isTranscribing}
                  >
                    {isTranscribing ? "Распознаю..." : "Распознать и вставить"}
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

                {!mediaSupported ? (
                  <p className="bodyMuted">
                    У этого браузера нет доступа к <code>MediaRecorder</code>. Можно
                    продолжить через аудиофайл или текстовый ввод.
                  </p>
                ) : null}
              </div>
            ) : null}

            <textarea
              className="inputSurface textarea textareaLarge"
              rows={8}
              placeholder="Сформулируй ответ как на реальном интервью: короткая структура, суть, пример, trade-off и итог."
              value={answerText}
              onChange={(event) => setAnswerText(event.target.value)}
              disabled={isBusy || session?.status === "completed"}
            />

            <div className="buttonRow">
              <button
                className="button buttonPrimary"
                type="button"
                onClick={handleSubmitAnswer}
                disabled={isBusy || session?.status === "completed"}
              >
                Отправить ответ
              </button>
            </div>
          </section>

          <section className="surfacePanel">
            <SectionHeader
              eyebrow="Session memory"
              title="История интервью"
              description="Хронология turns помогает быстро понять, как менялась глубина вопросов и feedback."
            />

            {turns.length ? (
              <div className="timelineList">
                {turns.map((turn) => (
                  <article className="timelineItem" key={turn.turn_index}>
                    <div className="timelineMarker">
                      <span>{turn.turn_index}</span>
                    </div>
                    <div className="timelineContent">
                      <div className="timelineHeader">
                        <h3>Turn {turn.turn_index}</h3>
                        <span>{new Date(turn.created_at).toLocaleString("ru-RU")}</span>
                      </div>
                      <div className="timelineBody">
                        <div className="timelineBlock">
                          <p className="miniLabel">Вопрос</p>
                          <p>{turn.question}</p>
                        </div>
                        <div className="timelineBlock">
                          <p className="miniLabel">Ответ</p>
                          <p>{turn.answer}</p>
                        </div>
                        <div className="timelineBlock">
                          <p className="miniLabel">Фидбек</p>
                          <p>{turn.feedback}</p>
                        </div>
                        <div className="timelineBlock">
                          <p className="miniLabel">Следующий шаг</p>
                          <p>{turn.next_question ?? "Интервью завершено."}</p>
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                title="История пока пустая"
                description="После первого ответа здесь появятся turns с вопросами, ответами и кратким feedback."
              />
            )}
          </section>
        </div>

        <aside className="sideColumn">
          {analysis?.analysis_status ? (
            <section className="surfacePanel">
              <SectionHeader
                eyebrow="Readiness"
                title="Snapshot профиля"
                description="Краткий обзор того, с чем интервью вообще работает."
              />

              <div className="metricGrid metricGridCompact">
                <MetricCard
                  label="Primary skills"
                  value={analysis.candidate_profile?.primary_skills?.length ?? 0}
                  hint="Ключевые сигналы из резюме."
                  tone="success"
                />
                <MetricCard
                  label="Missing"
                  value={analysis.skill_gap_map?.missing_skills?.length ?? 0}
                  hint="Наиболее важный разрыв с вакансией."
                  tone="warning"
                />
                <MetricCard
                  label="HR match"
                  value={`${hrAnalysis?.overall_match_score_pct ?? 0}%`}
                  hint="Semantic fit score от HR-style AI analysis."
                  tone="accent"
                />
                <MetricCard
                  label="Interview chance"
                  value={`${hrAnalysis?.interview_probability_pct ?? 0}%`}
                  hint="Оценка вероятности получить интервью."
                  tone={(hrAnalysis?.interview_probability_pct ?? 0) < 50 ? "warning" : "success"}
                />
              </div>

              <div className="stackSection">
                <p className="miniLabel">Primary skills</p>
                <div className="chipRow">
                  {(analysis.candidate_profile?.primary_skills ?? []).map((skill) => (
                    <span className="chip chipSuccess" key={skill}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              <div className="stackSection">
                <p className="miniLabel">Missing skills</p>
                <div className="chipRow">
                  {(analysis.skill_gap_map?.missing_skills ?? []).map((skill) => (
                    <span className="chip chipWarning" key={skill}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {hrAnalysis?.hr_verdict ? (
                <div className="stackSection">
                  <p className="miniLabel">HR verdict</p>
                  <p className="bodyMuted">{hrAnalysis.hr_verdict}</p>
                </div>
              ) : null}
            </section>
          ) : null}

          {workflow?.latest_trace?.length ? (
            <section className="surfacePanel">
              <SectionHeader
                eyebrow="Trace"
                title="Workflow trace"
                description="Показывает, какие узлы и tool calls реально отработали в interview workflow."
              />

              <div className="traceList">
                {workflow.latest_trace.map((event, index) => (
                  <article className="traceItem" key={`${event.node}-${event.timestamp}-${index}`}>
                    <div className="traceMeta">
                      <Badge tone={traceTone(event.node)}>{event.node}</Badge>
                      <span>{new Date(event.timestamp).toLocaleTimeString("ru-RU")}</span>
                    </div>
                    <strong>{event.summary}</strong>
                    {event.details ? (
                      <pre className="traceCode">
                        {JSON.stringify(event.details, null, 2)}
                      </pre>
                    ) : null}
                  </article>
                ))}
              </div>
            </section>
          ) : (
            <section className="surfacePanel">
              <EmptyState
                title="Trace появится позже"
                description="После запуска интервью здесь появятся planner, interviewer, evaluator и другие узлы workflow."
              />
            </section>
          )}
        </aside>
      </div>

      {finalReport ? (
        <section className="surfacePanel fadeUp">
          <SectionHeader
            eyebrow="Final report"
            title="Итоговый разбор"
            description="Финальный блок должен быть полезен и как retrospective summary, и как следующая тренировка."
            aside={<Badge tone="success">{finalReport.final_score_0_10}/10</Badge>}
          />

          <div className="metricGrid">
            <MetricCard
              label="Final score"
              value={`${finalReport.final_score_0_10}/10`}
              hint="Сводная оценка по всей сессии."
              tone="accent"
            />
            <MetricCard
              label="Strengths"
              value={finalReport.strengths.length}
              hint="Сильные сигналы, которые уже считываются уверенно."
              tone="success"
            />
            <MetricCard
              label="Gaps"
              value={finalReport.gaps.length}
              hint="Темы, которые стоит подтянуть до следующей сессии."
              tone="warning"
            />
            <MetricCard
              label="Practice prompts"
              value={finalReport.questions_to_practice.length}
              hint="Вопросы для следующей самостоятельной тренировки."
              tone="neutral"
            />
          </div>

          <div className="analysisDashboard">
            <article className="subtlePanel">
              <SectionHeader
                eyebrow="Summary"
                title="Сводка"
                description={finalReport.summary}
                size="compact"
              />
              <div className="stackSection">
                <p className="miniLabel">Topics to review</p>
                <div className="chipRow">
                  {finalReport.topics_to_review.map((item) => (
                    <span className="chip chipNeutral" key={item}>
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </article>

            <article className="subtlePanel">
              <SectionHeader eyebrow="Strengths" title="Что уже хорошо" size="compact" />
              {renderList(finalReport.strengths)}
            </article>

            <article className="subtlePanel">
              <SectionHeader eyebrow="Growth" title="Что стоит усилить" size="compact" />
              {renderList(finalReport.gaps)}
            </article>
          </div>

          {coaching ? (
            <section className="coachSection">
              <SectionHeader
                eyebrow="Interview Coach"
                title="Coaching layer"
                description="Ниже уже не сырые служебные поля, а человекочитаемый блок для повторной практики."
                aside={<Badge tone="accent">{coaching.skill_name}</Badge>}
              />

              <div className="coachGrid">
                <article className="subtlePanel">
                  <h3>Что получилось хорошо</h3>
                  {renderList(coaching.what_was_good)}
                </article>
                <article className="subtlePanel">
                  <h3>Что стоит усилить</h3>
                  {renderList(coaching.what_was_weak)}
                </article>
                <article className="subtlePanel">
                  <h3>Как улучшить ответ</h3>
                  {renderList(coaching.how_to_improve)}
                </article>
                <article className="subtlePanel">
                  <h3>Что потренировать</h3>
                  {renderList(coaching.recommended_drills)}
                </article>
              </div>
            </section>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

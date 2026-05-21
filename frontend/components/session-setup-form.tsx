"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

import { analyzeSession, createSession, uploadSessionDocuments } from "@/lib/api";
import type { SessionPayload } from "@/lib/types";
import {
  AnalysisLoader,
  Badge,
  EmptyState,
  MetricCard,
  ScoreBar,
  SectionHeader,
} from "@/components/ui/primitives";

type SubmitState =
  | "idle"
  | "creating"
  | "uploading"
  | "created"
  | "analyzing"
  | "ready"
  | "error";

type StepTone = "done" | "active" | "idle";

function formatRiskLabel(value: string | undefined) {
  if (!value) {
    return "unknown";
  }

  return value.replaceAll("_", " ");
}

function statusTone(state: SubmitState) {
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

function buildStepState(step: number, submitState: SubmitState): StepTone {
  if (step === 1) {
    if (submitState === "created" || submitState === "ready" || submitState === "analyzing") {
      return "done";
    }
    if (submitState === "creating" || submitState === "uploading" || submitState === "idle" || submitState === "error") {
      return "active";
    }
  }

  if (step === 2) {
    if (submitState === "ready") {
      return "done";
    }
    if (submitState === "created" || submitState === "analyzing") {
      return "active";
    }
  }

  if (step === 3 && submitState === "ready") {
    return "active";
  }

  return "idle";
}

export function SessionSetupForm() {
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [statusMessage, setStatusMessage] = useState(
    "Сессия ещё не создана. Начните с роли, документов и вакансии.",
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [createdSessionId, setCreatedSessionId] = useState<string | null>(null);
  const [analysisPayload, setAnalysisPayload] = useState<SessionPayload | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setAnalysisPayload(null);
    setSubmitState("creating");
    setStatusMessage("Создаю workspace сессии и сохраняю параметры интервью.");

    const formElement = event.currentTarget;
    const formData = new FormData(formElement);

    try {
      const created = await createSession({
        role: String(formData.get("role") ?? ""),
        seniority: String(formData.get("seniority") ?? ""),
        interview_type: String(formData.get("interview_type") ?? ""),
        interview_language: String(formData.get("interview_language") ?? ""),
        duration_minutes: Number(formData.get("duration_minutes") ?? 15),
        voice_mode: String(formData.get("voice_mode") ?? "On"),
      });

      setCreatedSessionId(created.session.id);
      setSubmitState("uploading");
      setStatusMessage("Загружаю резюме и привязываю вакансию к сессии.");

      await uploadSessionDocuments(created.session.id, formData);

      setSubmitState("created");
      setStatusMessage(
        "Документы сохранены. Теперь можно построить profile fit и определить interview topics.",
      );
    } catch (error) {
      setSubmitState("error");
      setErrorMessage(
        error instanceof Error
          ? error.message.replace(/<[^>]*>/g, "").trim()
          : "Не удалось создать сессию и сохранить документы.",
      );
      setStatusMessage("Сценарий прервался. Исправьте ввод и повторите попытку.");
    }
  }

  async function handleAnalyze() {
    if (!createdSessionId) {
      return;
    }

    setErrorMessage(null);
    setSubmitState("analyzing");
    setStatusMessage("Сравниваю стек кандидата с вакансией и собираю interview plan.");

    try {
      const analyzed = await analyzeSession(createdSessionId);
      setAnalysisPayload(analyzed);
      setSubmitState("ready");
      setStatusMessage(
        "Анализ завершён. Можно проверить fit, gaps и перейти к mock interview.",
      );
    } catch (error) {
      setSubmitState("error");
      setErrorMessage(
        error instanceof Error
          ? error.message.replace(/<[^>]*>/g, "").trim()
          : "Не удалось проанализировать сессию.",
      );
      setStatusMessage("Анализ не завершился. Можно повторить попытку.");
    }
  }

  const analysis = analysisPayload?.analysis;
  const candidate = analysis?.candidate_profile;
  const job = analysis?.job_profile;
  const gaps = analysis?.skill_gap_map;
  const hrAnalysis = analysis?.hr_analysis;
  const topics = analysis?.interview_topics ?? [];

  const stepState = useMemo(
    () => [
      buildStepState(1, submitState),
      buildStepState(2, submitState),
      buildStepState(3, submitState),
    ],
    [submitState],
  );

  const matchedCount = gaps?.matched_skills?.length ?? 0;
  const missingCount = gaps?.missing_skills?.length ?? 0;
  const adjacentCount = gaps?.adjacent_skills?.length ?? 0;
  const isPipelineBusy =
    submitState === "creating" ||
    submitState === "uploading" ||
    submitState === "analyzing";
  const loaderTitle =
    submitState === "creating"
      ? "Создаю interview workspace"
      : submitState === "uploading"
        ? "Привязываю резюме и вакансию"
        : "Строю AI-анализ кандидата и вакансии";
  const loaderDescription =
    submitState === "creating"
      ? "Фиксирую параметры сессии, чтобы дальше analysis и interview flow работали в одном контексте."
      : submitState === "uploading"
        ? "Сохраняю документы в session storage и подготавливаю их к parsing."
        : "Сначала собираю deterministic intake artifacts, затем добавляю semantic HR analysis через MCP.";
  const loaderSteps = [
    {
      label: "Session context",
      state:
        submitState === "creating"
          ? "active"
          : submitState === "uploading" || submitState === "created" || submitState === "analyzing" || submitState === "ready"
            ? "done"
            : "pending",
    },
    {
      label: "Document ingest",
      state:
        submitState === "uploading"
          ? "active"
          : submitState === "created" || submitState === "analyzing" || submitState === "ready"
            ? "done"
            : "pending",
    },
    {
      label: "Profile fit + HR scoring",
      state:
        submitState === "analyzing"
          ? "active"
          : submitState === "ready"
            ? "done"
            : "pending",
    },
  ] as const;

  return (
    <div className="pageStack">
      <section className="surfacePanel formPanel fadeUp">
        <SectionHeader
          eyebrow="Session setup"
          title="Настройка интервью и intake"
          description="Сначала создаём workspace, затем отдельно запускаем анализ, чтобы интерфейс явно показывал match и mismatch между резюме и вакансией."
          aside={<Badge tone={statusTone(submitState)}>state: {submitState}</Badge>}
        />

        <div className="progressRail progressRailWide">
          <article className={`progressStep progressStep-${stepState[0]}`}>
            <span className="progressIndex">01</span>
            <div>
              <strong>Session config</strong>
              <p>Роль, seniority, язык, формат и voice mode.</p>
            </div>
          </article>
          <article className={`progressStep progressStep-${stepState[1]}`}>
            <span className="progressIndex">02</span>
            <div>
              <strong>Upload + analysis</strong>
              <p>Резюме, vacancy input и profile fit analysis.</p>
            </div>
          </article>
          <article className={`progressStep progressStep-${stepState[2]}`}>
            <span className="progressIndex">03</span>
            <div>
              <strong>Interview ready</strong>
              <p>Topics, gaps и переход к mock interview.</p>
            </div>
          </article>
        </div>

        <form className="formLayout" onSubmit={handleSubmit}>
          <div className="formSection">
            <SectionHeader
              eyebrow="Configuration"
              title="Контекст интервью"
              description="Фиксируем параметры, которые будут влиять на planner, evaluator и voice flow."
            />

            <div className="fieldGrid">
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
          </div>

          <div className="formSection">
            <SectionHeader
              eyebrow="Documents"
              title="Резюме и вакансия"
              description="На этом шаге интерфейс собирает документы, которые дальше лягут в candidate profile и job profile."
            />

            <div className="fieldGrid fieldGridSingle">
              <label className="fieldGroup">
                <span className="fieldLabel">Резюме</span>
                <span className="fieldHint">Поддерживаются PDF и DOCX.</span>
                <input
                  className="inputSurface fileInput"
                  type="file"
                  name="resume"
                  accept=".pdf,.doc,.docx"
                />
              </label>

              <label className="fieldGroup">
                <span className="fieldLabel">URL вакансии</span>
                <input
                  className="inputSurface input"
                  type="url"
                  name="vacancy_url"
                  placeholder="https://example.com/job"
                />
              </label>

              <label className="fieldGroup">
                <span className="fieldLabel">Текст вакансии</span>
                <span className="fieldHint">
                  Можно вставить полное описание или только требования и ожидания.
                </span>
                <textarea
                  className="inputSurface textarea textareaLarge"
                  name="vacancy_text"
                  rows={8}
                  placeholder="Вставьте описание вакансии, требования к стеку и ожидания от кандидата"
                />
              </label>
            </div>
          </div>

          {errorMessage ? <div className="statusBanner statusBannerError">{errorMessage}</div> : null}

          <div className="actionCluster">
            <div className="buttonRow">
              <button
                className="button buttonPrimary"
                type="submit"
                disabled={
                  submitState === "creating" ||
                  submitState === "uploading" ||
                  submitState === "analyzing"
                }
              >
                {submitState === "creating" || submitState === "uploading"
                  ? "Сохраняю сессию..."
                  : "Создать сессию"}
              </button>

              <button
                className="button buttonSecondary"
                type="button"
                onClick={handleAnalyze}
                disabled={
                  !createdSessionId ||
                  submitState === "creating" ||
                  submitState === "uploading" ||
                  submitState === "analyzing"
                }
              >
                {submitState === "analyzing" ? "Строю анализ..." : "Запустить анализ"}
              </button>
            </div>

            <div className={`statusBanner statusBanner-${statusTone(submitState)}`}>
              <div>
                <p className="statusKicker">Workflow status</p>
                <p>{statusMessage}</p>
              </div>
              {createdSessionId ? (
                <div className="statusMetaBlock">
                  <span className="statusMetaLabel">Session ID</span>
                  <code className="monoLine">{createdSessionId}</code>
                </div>
              ) : null}
            </div>

            {isPipelineBusy ? (
              <AnalysisLoader
                title={loaderTitle}
                description={loaderDescription}
                steps={[...loaderSteps]}
              />
            ) : null}
          </div>

          {createdSessionId ? (
            <div className="inlineActions">
              <Link className="button buttonGhost" href={`/mock-interview?session_id=${createdSessionId}`}>
                Открыть interview workspace
              </Link>
            </div>
          ) : null}
        </form>
      </section>

      {analysis ? (
        <section className="surfacePanel fadeUp">
          <SectionHeader
            eyebrow="Profile fit"
            title="Результат intake analysis"
            description="Здесь особенно важен разрыв между резюме и вакансией: matched skills, missing skills, adjacent knowledge и topics для интервью."
            aside={<Badge tone="success">analysis ready</Badge>}
          />

          <div className="metricGrid">
            <MetricCard
              label="Matched skills"
              value={matchedCount}
              hint="Совпадения между стеком кандидата и вакансией."
              tone="success"
            />
            <MetricCard
              label="Missing skills"
              value={missingCount}
              hint="То, что вакансия ожидает, но профиль пока не показывает явно."
              tone={missingCount > 0 ? "warning" : "neutral"}
            />
            <MetricCard
              label="Adjacent skills"
              value={adjacentCount}
              hint="Соседние сигналы, из которых можно строить follow-up."
              tone="accent"
            />
            <MetricCard
              label="Risk level"
              value={formatRiskLabel(gaps?.risk_level)}
              hint="Общий риск mismatch между профилем и вакансией."
              tone={missingCount > matchedCount ? "warning" : "neutral"}
            />
          </div>

          <div className="analysisDashboard">
            <article className="subtlePanel">
              <SectionHeader
                eyebrow="Candidate"
                title="Профиль кандидата"
                description={`Оценка опыта: ${candidate?.experience_years_estimate ?? 0} years`}
                size="compact"
              />
              <div className="chipRow">
                {(candidate?.primary_skills ?? []).map((skill) => (
                  <span className="chip chipSuccess" key={skill}>
                    {skill}
                  </span>
                ))}
              </div>
              <div className="infoList">
                <div className="infoItem">
                  <span>Strengths</span>
                  <strong>{(candidate?.strengths ?? []).join(", ") || "Пока мало сигналов."}</strong>
                </div>
                <div className="infoItem">
                  <span>Resume parser</span>
                  <strong>{analysis.parser_summary.resume?.parser_used ?? "unknown"}</strong>
                </div>
              </div>
            </article>

            <article className="subtlePanel">
              <SectionHeader
                eyebrow="Vacancy"
                title="Профиль вакансии"
                description="Требования, которые будут использоваться для planning и evaluation."
                size="compact"
              />
              <div className="chipRow">
                {(job?.required_skills ?? []).map((skill) => (
                  <span className="chip chipAccent" key={skill}>
                    {skill}
                  </span>
                ))}
              </div>
              <div className="infoList">
                <div className="infoItem">
                  <span>Preferred</span>
                  <strong>{(job?.preferred_skills ?? []).join(", ") || "Не указано."}</strong>
                </div>
                <div className="infoItem">
                  <span>Vacancy parser</span>
                  <strong>{analysis.parser_summary.vacancy?.parser_used ?? "unknown"}</strong>
                </div>
              </div>
            </article>

            <article className="subtlePanel mismatchPanel">
              <SectionHeader
                eyebrow="Stack mismatch"
                title="Где профиль и вакансия расходятся"
                description="Этот блок специально усиливает mismatch, чтобы интервью не выглядело случайным."
                size="compact"
              />
              <div className="mismatchColumns">
                <div>
                  <p className="miniLabel">Missing</p>
                  <div className="chipRow">
                    {(gaps?.missing_skills ?? []).map((skill) => (
                      <span className="chip chipWarning" key={skill}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="miniLabel">Matched</p>
                  <div className="chipRow">
                    {(gaps?.matched_skills ?? []).map((skill) => (
                      <span className="chip chipSuccess" key={skill}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="miniLabel">Recommended focus</p>
                  <div className="chipRow">
                    {(gaps?.recommended_focus ?? []).map((skill) => (
                      <span className="chip chipNeutral" key={skill}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </article>
          </div>

          <section className="topicsSection">
            <SectionHeader
              eyebrow="Interview plan"
              title="Темы, которые пойдут в mock interview"
              description="Приоритет и причина каждой темы должны читаться быстро, без перегруза."
            />

            <div className="topicGrid">
              {topics.map((topic) => (
                <article className="topicCard" key={topic.topic}>
                  <div className="topicCardTop">
                    <div>
                      <h3>{topic.topic}</h3>
                      <p>{topic.reason}</p>
                    </div>
                    <Badge tone={topic.priority === "high" ? "accent" : "neutral"}>
                      {topic.priority}
                    </Badge>
                  </div>
                  <div className="topicMeta">
                    <span>{topic.interview_type}</span>
                    <span>{topic.expected_difficulty}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>

          {hrAnalysis?.status ? (
            <section className="topicsSection">
              <SectionHeader
                eyebrow="HR analysis"
                title="Честная оценка от AI recruiter"
                description="Этот слой не заменяет deterministic intake, а добавляет semantic analysis в стиле опытного HR."
                aside={
                  <Badge tone={hrAnalysis.status === "completed" ? "success" : "warning"}>
                    {hrAnalysis.status}
                  </Badge>
                }
              />

              <div className="metricGrid">
                <MetricCard
                  label="Match score"
                  value={`${hrAnalysis.overall_match_score_pct}%`}
                  hint={hrAnalysis.match_explanation || "AI оценка соответствия резюме и вакансии."}
                  tone="accent"
                />
                <MetricCard
                  label="Resume quality"
                  value={`${hrAnalysis.resume_quality_score_pct}%`}
                  hint="Насколько резюме выглядит сильным для recruiter screening."
                  tone="neutral"
                />
                <MetricCard
                  label="ATS compatibility"
                  value={`${hrAnalysis.ats_compatibility_score_pct}%`}
                  hint="Оценка читаемости и keyword fit для ATS."
                  tone="success"
                />
                <MetricCard
                  label="Interview probability"
                  value={`${hrAnalysis.interview_probability_pct}%`}
                  hint="Оценка вероятности получить интервью."
                  tone={hrAnalysis.interview_probability_pct < 50 ? "warning" : "success"}
                />
              </div>

              <div className="scoreBarGrid">
                <ScoreBar
                  label="Match score"
                  value={hrAnalysis.overall_match_score_pct}
                  hint="Насколько резюме соответствует требованиям вакансии."
                  tone="accent"
                />
                <ScoreBar
                  label="Resume quality"
                  value={hrAnalysis.resume_quality_score_pct}
                  hint="Сила резюме глазами recruiter и hiring manager."
                  tone="neutral"
                />
                <ScoreBar
                  label="ATS compatibility"
                  value={hrAnalysis.ats_compatibility_score_pct}
                  hint="Вероятность корректного прохождения ATS и keyword screen."
                  tone="success"
                />
                <ScoreBar
                  label="Interview probability"
                  value={hrAnalysis.interview_probability_pct}
                  hint="Шанс получить интервью при текущем состоянии профиля."
                  tone={hrAnalysis.interview_probability_pct < 50 ? "warning" : "success"}
                />
              </div>

              <div className="analysisDashboard">
                <article className="subtlePanel">
                  <SectionHeader
                    eyebrow="Verdict"
                    title={hrAnalysis.hr_verdict || "HR verdict пока пустой"}
                    description={hrAnalysis.message || hrAnalysis.market_competitiveness || "Semantic HR feedback."}
                    size="compact"
                  />
                  <div className="infoList">
                    <div className="infoItem">
                      <span>Candidate level</span>
                      <strong>{hrAnalysis.candidate_level || "Не определён"}</strong>
                    </div>
                    <div className="infoItem">
                      <span>Vacancy level</span>
                      <strong>{hrAnalysis.vacancy_level || "Не определён"}</strong>
                    </div>
                    <div className="infoItem">
                      <span>Risk of rejection</span>
                      <strong>{hrAnalysis.risk_of_rejection || "Не определён"}</strong>
                    </div>
                    <div className="infoItem">
                      <span>Salary level estimation</span>
                      <strong>{hrAnalysis.salary_level_estimation || "Недостаточно данных"}</strong>
                    </div>
                  </div>
                </article>

                <article className="subtlePanel">
                  <SectionHeader eyebrow="Strong sides" title="Почему кандидат может пройти screening" size="compact" />
                  <ul className="listClean">
                    {(hrAnalysis.strong_sides ?? []).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>

                <article className="subtlePanel mismatchPanel">
                  <SectionHeader eyebrow="Weak sides" title="Что может привести к отказу" size="compact" />
                  <ul className="listClean">
                    {(hrAnalysis.weak_sides ?? []).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              </div>

              <div className="analysisDashboard">
                <article className="subtlePanel">
                  <SectionHeader eyebrow="Missing skills" title="Чего не хватает под вакансию" size="compact" />
                  <div className="chipRow">
                    {(hrAnalysis.missing_skills ?? []).map((skill) => (
                      <span className="chip chipWarning" key={skill}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </article>

                <article className="subtlePanel">
                  <SectionHeader eyebrow="ATS keywords" title="Ключевые слова и ATS" size="compact" />
                  <div className="stackSection">
                    <p className="miniLabel">Present</p>
                    <div className="chipRow">
                      {(hrAnalysis.ats_keyword_analysis?.present_keywords ?? []).map((item) => (
                        <span className="chip chipSuccess" key={item}>
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="stackSection">
                    <p className="miniLabel">Missing</p>
                    <div className="chipRow">
                      {(hrAnalysis.ats_keyword_analysis?.missing_keywords ?? []).map((item) => (
                        <span className="chip chipWarning" key={item}>
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                  <p className="bodyMuted">
                    {hrAnalysis.ats_keyword_analysis?.keyword_density_assessment || "Пока без ATS-комментария."}
                  </p>
                </article>

                <article className="subtlePanel">
                  <SectionHeader eyebrow="Improvement plan" title="Что переписать и усилить" size="compact" />
                  <ul className="listClean">
                    {(hrAnalysis.improvement_suggestions ?? []).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              </div>

              {(hrAnalysis.rewritten_resume_fragments ?? []).length ? (
                <section className="topicsSection">
                  <SectionHeader
                    eyebrow="Rewrite suggestions"
                    title="Переписанные фрагменты резюме"
                    description="Готовые примеры, как можно усилить слабые sections и bullet points."
                  />
                  <div className="rewriteGrid">
                    {(hrAnalysis.rewritten_resume_fragments ?? []).map((fragment, index) => (
                      <article className="subtlePanel" key={`${fragment.section_title}-${index}`}>
                        <h3>{fragment.section_title || `Fragment ${index + 1}`}</h3>
                        <div className="rewriteBlock">
                          <p className="miniLabel">Original</p>
                          <p>{fragment.original_excerpt || "Фрагмент не был передан."}</p>
                        </div>
                        <div className="rewriteBlock">
                          <p className="miniLabel">Rewritten</p>
                          <p>{fragment.rewritten_version}</p>
                        </div>
                        <div className="rewriteBlock">
                          <p className="miniLabel">Rationale</p>
                          <p>{fragment.rationale}</p>
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              ) : null}
            </section>
          ) : null}

          <div className="inlineActions">
            <Link className="button buttonPrimary" href={`/mock-interview?session_id=${createdSessionId}`}>
              Перейти к интервью
            </Link>
          </div>
        </section>
      ) : (
        <section className="surfacePanel fadeUp">
          <EmptyState
            title="Анализ ещё не построен"
            description="После сохранения документов здесь появится profile fit dashboard с matched skills, mismatch и interview topics."
          />
        </section>
      )}
    </div>
  );
}

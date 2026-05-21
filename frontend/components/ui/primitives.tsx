import type { ReactNode } from "react";

function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

type BadgeTone = "neutral" | "success" | "accent" | "warning" | "live";

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: BadgeTone;
}) {
  return <span className={cx("badge", `badge-${tone}`)}>{children}</span>;
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  aside,
  size = "default",
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  aside?: ReactNode;
  size?: "default" | "compact";
}) {
  return (
    <div className={cx("panelHeader", size === "compact" && "panelHeaderCompact")}>
      <div className={cx("panelHeaderBody", size === "compact" && "panelHeaderBodyCompact")}>
        {eyebrow ? <p className="panelEyebrow">{eyebrow}</p> : null}
        <h2 className={cx("panelTitle", size === "compact" && "panelTitleCompact")}>{title}</h2>
        {description ? (
          <p className={cx("panelDescription", size === "compact" && "panelDescriptionCompact")}>
            {description}
          </p>
        ) : null}
      </div>
      {aside ? <div className="panelHeaderAside">{aside}</div> : null}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: "neutral" | "accent" | "success" | "warning";
}) {
  return (
    <article className={cx("metricCard", `metricCard-${tone}`)}>
      <p className="metricLabel">{label}</p>
      <strong className="metricValue">{value}</strong>
      {hint ? <p className="metricHint">{hint}</p> : null}
    </article>
  );
}

export function ScoreBar({
  label,
  value,
  hint,
  tone = "accent",
}: {
  label: string;
  value: number;
  hint?: string;
  tone?: "accent" | "success" | "warning" | "neutral";
}) {
  const normalized = Math.max(0, Math.min(value, 100));

  return (
    <article className="scoreBarCard">
      <div className="scoreBarHeader">
        <div>
          <p className="metricLabel">{label}</p>
          {hint ? <p className="scoreBarHint">{hint}</p> : null}
        </div>
        <strong className="scoreBarValue">{normalized}%</strong>
      </div>
      <div className="scoreBarTrack" aria-hidden="true">
        <div
          className={cx("scoreBarFill", `scoreBarFill-${tone}`)}
          style={{ width: `${normalized}%` }}
        />
      </div>
    </article>
  );
}

export function AnalysisLoader({
  title,
  description,
  steps,
}: {
  title: string;
  description: string;
  steps: Array<{
    label: string;
    state: "done" | "active" | "pending";
  }>;
}) {
  return (
    <section className="analysisLoaderPanel" aria-live="polite">
      <div className="analysisLoaderVisual" aria-hidden="true">
        <div className="analysisLoaderCore">
          <span className="analysisLoaderPulse analysisLoaderPulseOne" />
          <span className="analysisLoaderPulse analysisLoaderPulseTwo" />
          <span className="analysisLoaderDot analysisLoaderDotTop" />
          <span className="analysisLoaderDot analysisLoaderDotRight" />
          <span className="analysisLoaderDot analysisLoaderDotBottom" />
          <span className="analysisLoaderDot analysisLoaderDotLeft" />
        </div>
      </div>

      <div className="analysisLoaderBody">
        <p className="panelEyebrow">AI Analysis Pipeline</p>
        <h3 className="analysisLoaderTitle">{title}</h3>
        <p className="analysisLoaderDescription">{description}</p>

        <div className="analysisLoaderSteps">
          {steps.map((step) => (
            <div className={`analysisLoaderStep analysisLoaderStep-${step.state}`} key={step.label}>
              <span className="analysisLoaderStepDot" />
              <span>{step.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="emptyStatePanel">
      <div className="emptyStateOrb" />
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

export function ButtonSpinner() {
  return <span className="buttonSpinner" aria-hidden="true" />;
}

export function RingScore({
  label,
  value,
  max = 10,
}: {
  label: string;
  value: number;
  max?: number;
}) {
  const safeMax = max <= 0 ? 10 : max;
  const normalized = Math.max(0, Math.min(value, safeMax));
  const percent = (normalized / safeMax) * 100;

  return (
    <article className="ringScoreCard">
      <div
        className="ringScoreVisual"
        style={{ background: `conic-gradient(var(--accent-warm) ${percent}%, rgba(255,255,255,0.08) ${percent}% 100%)` }}
        aria-hidden="true"
      >
        <div className="ringScoreInner">
          <strong>{normalized}</strong>
          <span>из {safeMax}</span>
        </div>
      </div>
      <div className="ringScoreMeta">
        <p className="metricLabel">{label}</p>
      </div>
    </article>
  );
}

export function TrendBars({
  items,
}: {
  items: Array<{ label: string; value: number; hint?: string }>;
}) {
  return (
    <div className="trendBars">
      {items.map((item) => {
        const normalized = Math.max(0, Math.min(item.value, 10));
        const width = `${(normalized / 10) * 100}%`;
        return (
          <article className="trendBarItem" key={item.label}>
            <div className="trendBarHeader">
              <strong>{item.label}</strong>
              <span>{normalized}/10</span>
            </div>
            <div className="trendBarTrack" aria-hidden="true">
              <div className="trendBarFill" style={{ width }} />
            </div>
            {item.hint ? <p className="trendBarHint">{item.hint}</p> : null}
          </article>
        );
      })}
    </div>
  );
}

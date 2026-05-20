import { SessionSetupForm } from "@/components/session-setup-form";
import { Badge, MetricCard } from "@/components/ui/primitives";

export default function HomePage() {
  return (
    <main className="shell shellWide">
      <section className="heroPanel fadeUp">
        <div className="heroGrid">
          <div className="heroCopy">
            <div className="heroBadgeRow">
              <Badge tone="live">Interview OS</Badge>
              <Badge tone="accent">RAG + LangGraph + Voice</Badge>
            </div>
            <h1 className="heroTitle">
              AI workspace для подготовки к техническому интервью.
            </h1>
            <p className="heroLead">
              Сначала собираем роль, резюме и вакансию. Затем строим profile fit,
              выявляем skill gaps и запускаем mock interview в одном связанном
              продуктном потоке.
            </p>
            <div className="heroSignalRow">
              <div className="signalPill">
                <span className="signalDot" />
                Анализ, voice и interview workflow уже работают end-to-end
              </div>
            </div>
          </div>

          <div className="heroMetrics">
            <MetricCard
              label="Core flow"
              value="Session -> Analysis -> Interview"
              hint="Без переключений между разными экранами и ручных шагов."
              tone="accent"
            />
            <MetricCard
              label="Knowledge layer"
              value="196 documents / 525 chunks"
              hint="RAG, retrieval evals и topic-aware interview planning."
              tone="success"
            />
            <MetricCard
              label="Voice layer"
              value="Whisper + MiniMax HD"
              hint="STT и TTS уже подключены к текущему interview flow."
              tone="neutral"
            />
          </div>
        </div>
      </section>

      <section className="pageGrid pageGridSidebar fadeUp">
        <SessionSetupForm />

        <aside className="sidebarRail">
          <section className="surfacePanel sidePanel">
            <div className="panelHeader">
              <div className="panelHeaderBody">
                <p className="panelEyebrow">Product flow</p>
                <h2 className="panelTitle">Как устроен сценарий</h2>
                <p className="panelDescription">
                  Интерфейс теперь ведёт пользователя от настройки до интервью как
                  единый onboarding-поток.
                </p>
              </div>
            </div>

            <div className="progressRail">
              <article className="progressStep progressStepDone">
                <span className="progressIndex">01</span>
                <div>
                  <strong>Configure session</strong>
                  <p>Фиксируем роль, seniority, язык и voice mode.</p>
                </div>
              </article>
              <article className="progressStep progressStepActive">
                <span className="progressIndex">02</span>
                <div>
                  <strong>Upload + analyze</strong>
                  <p>Сравниваем стек кандидата и требования вакансии.</p>
                </div>
              </article>
              <article className="progressStep">
                <span className="progressIndex">03</span>
                <div>
                  <strong>Run interview</strong>
                  <p>Planner, evaluator и coaching используют общий knowledge layer.</p>
                </div>
              </article>
            </div>
          </section>

          <section className="surfacePanel sidePanel">
            <div className="panelHeader">
              <div className="panelHeaderBody">
                <p className="panelEyebrow">Stack health</p>
                <h2 className="panelTitle">Что уже подключено</h2>
              </div>
            </div>

            <div className="stackList">
              <div className="stackRow">
                <span>Frontend</span>
                <strong>Next.js / TypeScript</strong>
              </div>
              <div className="stackRow">
                <span>Interview engine</span>
                <strong>LangGraph + MCP</strong>
              </div>
              <div className="stackRow">
                <span>Knowledge retrieval</span>
                <strong>OpenAI embeddings + Chroma</strong>
              </div>
              <div className="stackRow">
                <span>Voice</span>
                <strong>Whisper + fal.ai MiniMax</strong>
              </div>
            </div>
          </section>

          <section className="surfacePanel sidePanel">
            <div className="panelHeader">
              <div className="panelHeaderBody">
                <p className="panelEyebrow">Environment</p>
                <h2 className="panelTitle">Backend expectations</h2>
              </div>
            </div>

            <div className="inlineNotice">
              <Badge tone="success">API</Badge>
              <p>
                Frontend использует <code>NEXT_PUBLIC_API_BASE_URL</code> и ожидает
                backend по адресу <code>127.0.0.1:8000</code>.
              </p>
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}

import { Suspense } from "react";

import { InterviewSessionView } from "@/components/interview-session-view";
import { EmptyState } from "@/components/ui/primitives";

export default function MockInterviewPage() {
  return (
    <main className="shell shellNarrow">
      <Suspense
        fallback={
          <section className="surfacePanel fadeUp">
            <EmptyState
              title="Загружаю workspace интервью"
              description="Подтягиваю состояние сессии, историю ответов, voice mode и workflow trace."
            />
          </section>
        }
      >
        <InterviewSessionView />
      </Suspense>
    </main>
  );
}

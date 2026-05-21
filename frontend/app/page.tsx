import { Suspense } from "react";

import { InterviewWorkspace } from "@/components/interview-workspace";
import { EmptyState } from "@/components/ui/primitives";

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <main className="workspaceShell">
          <section className="workspaceCard workspaceCardLarge fadeUp">
            <EmptyState
              title="Собираю workspace"
              description="Подтягиваю session state, analysis snapshot и interview history."
            />
          </section>
        </main>
      }
    >
      <InterviewWorkspace />
    </Suspense>
  );
}

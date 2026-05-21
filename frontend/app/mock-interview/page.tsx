import { Suspense } from "react";

import { InterviewWorkspace } from "@/components/interview-workspace";
import { EmptyState } from "@/components/ui/primitives";

export default function MockInterviewPage() {
  return (
    <Suspense
      fallback={
        <main className="workspaceShell">
          <section className="workspaceCard workspaceCardLarge fadeUp">
            <EmptyState
              title="Открываю interview workspace"
              description="Compatibility route использует тот же shell, что и главная страница."
            />
          </section>
        </main>
      }
    >
      <InterviewWorkspace />
    </Suspense>
  );
}

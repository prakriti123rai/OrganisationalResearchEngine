import {
  Activity,
  BarChart3,
  FileText,
  GitPullRequest,
  Network,
  PlayCircle,
  ShieldCheck,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", icon: BarChart3, active: true },
  { name: "Evidence", icon: FileText, active: false },
  { name: "Graph", icon: Network, active: false },
  { name: "Reasoning", icon: Activity, active: false },
  { name: "Impact", icon: GitPullRequest, active: false },
  { name: "Actions", icon: ShieldCheck, active: false },
  { name: "Execution", icon: PlayCircle, active: false },
];

export default function Home() {
  return (
    <main className="flex min-h-screen bg-background text-foreground">
      <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-muted px-4 py-5">
        <div className="mb-8">
          <div className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">
            ORE
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            Organizational Reasoning Engine
          </div>
        </div>
        <nav className="space-y-1" aria-label="Primary navigation">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <a
                key={item.name}
                href="#"
                className={[
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm transition",
                  item.active
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                ].join(" ")}
              >
                <Icon aria-hidden="true" className="h-4 w-4" />
                <span>{item.name}</span>
              </a>
            );
          })}
        </nav>
      </aside>

      <section className="flex flex-1 flex-col px-8 py-7">
        <header className="border-b border-border pb-6">
          <div className="text-sm text-muted-foreground">Milestone 1</div>
          <h1 className="mt-2 text-2xl font-semibold">Project Foundation</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
            The ORE shell is ready for the canonical evidence-first workflow.
            Feature surfaces remain intentionally empty until their assigned
            milestones.
          </p>
        </header>

        <div className="grid flex-1 place-items-center">
          <div className="w-full max-w-3xl border border-border bg-muted p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold">Foundation Status</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Frontend shell, backend health endpoint, PostgreSQL, and Neo4j
                  are wired through Docker Compose.
                </p>
              </div>
              <div className="rounded-md border border-confidence/40 px-3 py-2 text-sm text-confidence">
                Runnable
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

import { createFileRoute } from "@tanstack/react-router";
import { KnowledgeBaseBrowser } from "@/components/knowledge-base-browser";

export const Route = createFileRoute("/_app/knowledge")({
  head: () => ({
    meta: [
      { title: "Knowledge Base Browser — PRATHAM" },
      { name: "description", content: "Interactive 13 Emergency Disease Rule Specification & YAML Browser." },
    ],
  }),
  component: KnowledgePage,
});

function KnowledgePage() {
  return <KnowledgeBaseBrowser />;
}

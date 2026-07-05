import { createFileRoute } from "@tanstack/react-router";
import { ClinicalSearchView } from "@/components/clinical-search-view";

export const Route = createFileRoute("/_app/search")({
  head: () => ({
    meta: [
      { title: "Clinical Search — PRATHAM" },
      { name: "description", content: "Filterable emergency intake search across patient records." },
    ],
  }),
  component: SearchPage,
});

function SearchPage() {
  return <ClinicalSearchView />;
}

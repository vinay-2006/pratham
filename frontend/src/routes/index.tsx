import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useCallback } from "react";
import { useLenis } from "@/lib/use-lenis";
import { Ambient } from "@/components/showcase/ambient";
import { Nav, Hero } from "@/components/showcase/hero";
import { Problem, Pipeline, Architecture } from "@/components/showcase/act-one";
import { Engineering, AI, Production } from "@/components/showcase/act-two";
import { Demo, Atlas, Timeline, Lessons, Finale } from "@/components/showcase/act-three";
import { BootSequence } from "@/components/showcase/boot-sequence";

export const Route = createFileRoute("/")(  {
  head: () => ({
    meta: [
      { title: "PRATHAM — Emergency Clinical Intelligence Platform" },
      {
        name: "description",
        content:
          "A cinematic engineering case study of PRATHAM: predictive risk assessment and triage for healthcare AI, by Vinay Kumar Reddy.",
      },
      { property: "og:title", content: "PRATHAM — Emergency Clinical Intelligence Platform" },
      { property: "og:description", content: "Built to augment clinicians. Designed for transparency. Engineered for trust." },
    ],
  }),
  component: ShowcasePage,
});

function ShowcasePage() {
  useLenis();
  const [booting, setBooting] = useState(false);

  const handleLaunch = useCallback(() => {
    setBooting(true);
  }, []);

  const handleBootComplete = useCallback(() => {
    setBooting(false);
  }, []);

  // Keyboard shortcuts: Enter to launch (when at bottom), Escape to cancel boot
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input/textarea
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      if (e.key === "Enter" && !booting) {
        // Only launch if scrolled near the bottom (last 20% of page)
        const scrollPct = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
        if (scrollPct > 0.8) {
          e.preventDefault();
          handleLaunch();
        }
      }
      if (e.key === "Escape" && booting) {
        setBooting(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [booting, handleLaunch]);

  return (
    <div className="showcase">
      <main className="relative">
        <Ambient />
        <Nav />
        <Hero />
        <Problem />
        <Pipeline />
        <Architecture />
        <Engineering />
        <AI />
        <Production />
        <Demo />
        <Atlas />
        <Timeline />
        <Lessons />
        <Finale onLaunch={handleLaunch} />
      </main>

      <BootSequence isVisible={booting} onComplete={handleBootComplete} />
    </div>
  );
}

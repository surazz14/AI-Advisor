import type { Metadata } from "next";
import { CoveragePage } from "@/components/coverage/CoveragePage";

export const metadata: Metadata = {
  title: "Coverage tracker — Plantagenet Planning Advisor",
  description:
    "Track which Shire planning data is in the knowledge base and what is still missing.",
};

export default function CoverageRoute() {
  return <CoveragePage />;
}

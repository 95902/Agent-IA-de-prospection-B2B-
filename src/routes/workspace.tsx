/* eslint-disable react-refresh/only-export-components */
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { WorkspaceForm1 } from "@/features/workspaces/components/WorkspaceForm1";
import { WorkspaceForm2 } from "@/features/workspaces/components/WorkspaceForm2";
import { WorkspaceForm3 } from "@/features/workspaces/components/WorkspaceForm3";
import { WorkspaceForm4 } from "@/features/workspaces/components/WorkspaceForm4";
import { STEPS } from "@/features/workspaces/seed";

const Workspace = () => {
  const [step, setStep] = useState<number>(0);

  const handleNext = () => {
    setStep((prev) => Math.min(prev + 1, STEPS.length - 1));
  };

  const handlePrevious = () => {
    setStep((prev) => Math.max(prev - 1, 0));
  };

  const handleSubmit = () => {};

  return (
    <div className="flex flex-col items-center gap-8 justify-center w-full h-full">
      <Breadcrumbs data={STEPS} step={step} />

      {step === 3 ? (
        <WorkspaceForm4 onNext={handleSubmit} onPrevious={handlePrevious} />
      ) : (
        <div className="w-full h-full flex flex-col justify-start gap-8 items-center">
          <div className="flex flex-col gap-4 items-center justify-center w-full">
            <h1 className="text-3xl font-bold">
              Configurez votre espace de travail
            </h1>
            <h2 className="text-muted-foreground">
              Configurez votre profil client pour aider le moteur d'intelligence
              B2B de ProspectFlow à identifier les prospects à fort potentiel.
            </h2>
          </div>
          <Card className="rounded-lg border-2 flex-1 flex flex-col overflow-y-scroll w-full h-full p-4 ">
            {step === 0 && <WorkspaceForm1 onNext={handleNext} />}
            {step === 1 && (
              <WorkspaceForm2 onNext={handleNext} onPrevious={handlePrevious} />
            )}
            {step === 2 && (
              <WorkspaceForm3 onNext={handleNext} onPrevious={handlePrevious} />
            )}
            {step === 3 && (
              <WorkspaceForm4 onNext={handleSubmit} onPrevious={handlePrevious} />
            )}
          </Card>
        </div>
      )}
    </div>
  );
};

export const Route = createFileRoute("/workspace")({
  component: Workspace,
});

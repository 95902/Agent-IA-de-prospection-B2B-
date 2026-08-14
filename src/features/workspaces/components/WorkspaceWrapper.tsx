import { Button } from "@/components/ui/Button";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { WorkspaceHeaderForm } from "./WorkspaceHeaderForm";
import type { ReactNode, SubmitEvent } from "react";
import type { StepsProps } from "../types";

interface WorkspaceWrapperProps extends StepsProps {
  title: string;
  description: string;
  children: ReactNode;
  handleNext: () => void;
  handleReset: () => void;
  handlePrevious?: () => void;
}

export const WorkspaceWrapper = ({
  handleNext,
  handleReset,
  handlePrevious,
  children,
  title,
  description,
}: WorkspaceWrapperProps) => {
  const onSubmit = (e: SubmitEvent) => {
    e.preventDefault();
    e.stopPropagation();
    handleNext();
  };

  return (
    <form
      onSubmit={onSubmit}
      className="flex flex-col gap-8 items-end flex-1 justify-between"
    >
      <div className="flex flex-col gap-6 w-full h-full">
        <WorkspaceHeaderForm
          handleReset={handleReset}
          title={title}
          description={description}
        />
        {children}
      </div>
      <div
        className={`flex w-full ${handlePrevious ? "justify-between" : "justify-end"} items-center`}
      >
        {handlePrevious && (
          <Button type="button" className="w-fit" onClick={handlePrevious}>
            <ArrowLeft /> Retour
          </Button>
        )}
        <Button type="submit" className="w-fit">
          Suivant <ArrowRight />
        </Button>
      </div>
    </form>
  );
};

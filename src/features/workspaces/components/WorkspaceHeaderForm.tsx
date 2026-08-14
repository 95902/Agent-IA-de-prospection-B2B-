import { Button } from "@/components/ui/Button";
import { FieldDescription, FieldLegend } from "@/components/ui/Field";

interface WorkspaceHeaderFormProps {
  handleReset: () => void;
  title: string;
  description: string;
}

export const WorkspaceHeaderForm = ({
  handleReset,
  title,
  description,
}: WorkspaceHeaderFormProps) => (
  <div className="flex lg:flex-row flex-col justify-between gap-4 w-full">
    <div className="flex flex-col">
      <FieldLegend>
        <p className="text-3xl font-bold text-nowrap">{title}</p>
      </FieldLegend>
      <FieldDescription>{description}</FieldDescription>
    </div>
    <Button
      type="reset"
      variant="outline"
      className="w-fit"
      onClick={handleReset}
    >
      Réinitialiser
    </Button>
  </div>
);

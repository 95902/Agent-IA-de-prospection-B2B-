/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Checkbox";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/Field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import {
  ProspectsTable,
  type ProspectFilters,
} from "@/components/ProspectsTable";
import { useState } from "react";
import { Card } from "@/components/ui/Card";

// Options réelles présentes dans les données (dép. 75/92, NAF hôtels/agences).
const DEPARTEMENTS = [
  { value: "75", label: "75 — Paris" },
  { value: "92", label: "92 — Hauts-de-Seine" },
];
const NAF_OPTIONS = [
  { value: "", label: "Tous les NAF" },
  { value: "5510Z", label: "5510Z — Hôtels" },
  { value: "7311Z", label: "7311Z — Agences de com" },
];

const Propspect = () => {
  const [contactableOnly, setContactableOnly] = useState(false);
  const [nafCode, setNafCode] = useState<string>("");
  const [departments, setDepartments] = useState<string[]>([]);

  const toggleDepartment = (dep: string, checked: boolean) => {
    setDepartments((prev) =>
      checked ? [...prev, dep] : prev.filter((d) => d !== dep),
    );
  };
  const handleReset = () => {
    setContactableOnly(false);
    setNafCode("");
    setDepartments([]);
  };

  // Filtres appliqués en direct (pas de bouton "Appliquer").
  const filters: ProspectFilters = {
    contactableOnly,
    departements: departments,
    codeNaf: nafCode || undefined,
  };

  return (
    <div className="w-full lg:h-full flex flex-col lg:flex-row gap-4">
      <Card className="w-full lg:max-w-md h-fit lg:h-full overflow-hidden border rounded-lg p-4 shrink-0">
        <FieldGroup>
          <FieldSet>
            <div className="flex items-center justify-between mb-4">
              <FieldLegend>Filtres</FieldLegend>
              <Button type="button" variant="outline" onClick={handleReset}>
                Réinitialiser
              </Button>
            </div>
            <FieldDescription>
              Filtrez la file d'appel selon les différents critères
            </FieldDescription>
            <FieldGroup>
              <Field>
                <label className="flex gap-2 items-center cursor-pointer text-sm">
                  <Checkbox
                    id="contactable-only"
                    checked={contactableOnly}
                    onCheckedChange={(c) => setContactableOnly(!!c)}
                  />
                  <span>
                    Uniquement les prospects joignables (tél. ou email)
                  </span>
                </label>
              </Field>
              <Field>
                <FieldLabel>Départements</FieldLabel>
                <div className="flex flex-col gap-2 mt-2">
                  {DEPARTEMENTS.map((dep) => (
                    <label
                      key={dep.value}
                      className="flex gap-2 items-center cursor-pointer text-sm"
                    >
                      <Checkbox
                        id={`dep-${dep.value}`}
                        checked={departments.includes(dep.value)}
                        onCheckedChange={(c) => toggleDepartment(dep.value, !!c)}
                      />
                      <span>{dep.label}</span>
                    </label>
                  ))}
                </div>
              </Field>
              <Field>
                <FieldLabel htmlFor="select-naf">Code NAF</FieldLabel>
                <Select
                  value={nafCode}
                  onValueChange={(v) => setNafCode(v ?? "")}
                >
                  <SelectTrigger id="select-naf">
                    <SelectValue placeholder="Tous les NAF" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {NAF_OPTIONS.map((item) => (
                        <SelectItem key={item.value} value={item.value}>
                          {item.label}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </Field>
            </FieldGroup>
          </FieldSet>
        </FieldGroup>
      </Card>
      <ProspectsTable filters={filters} />
    </div>
  );
};

export const Route = createFileRoute("/prospects/")({
  component: Propspect,
});

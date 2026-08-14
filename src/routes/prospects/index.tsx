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
import { ProspectsTable } from "@/components/ProspectsTable";
import { useState } from "react";
import { Card } from "@/components/ui/Card";

const NAFCodes = [
  { label: "NAF", value: "" },
  { label: "A", value: "A" },
  { label: "B", value: "B" },
  { label: "C", value: "C" },
  { label: "D", value: "D" },
  { label: "E", value: "E" },
];

const departmentList = ["Information Tech", "Marketing & Sales", "Opérations"];

const Propspect = () => {
  const [numberOfEmployees, setNumberOfEmployees] = useState<string | null>(
    null,
  );
  const [nafCode, setNafCode] = useState<string | null>(null);
  const [departments, setDepartments] = useState<string[]>([]);
  const employeeRanges = ["1-50", "51-100", "101-200", "201-500"];
  console.log(departments, "dep");
  const handleReset = () => {
    setNumberOfEmployees(null);
    setNafCode("");
    setDepartments([]);
  };

  // const toggleDepartment = (dep: string, checked: boolean) => {
  //   setDepartments((prev) =>
  //     checked ? [...prev, dep] : prev.filter((item) => item !== dep),
  //   );
  // };

  return (
    <div className="w-full h-full flex gap-4">
      <Card className="w-full max-w-md overflow-hidden border rounded-lg p-4 shrink-0">
        <form>
          <FieldGroup>
            <FieldSet>
              <div className="flex items-center justify-between mb-4">
                <FieldLegend>Filtres</FieldLegend>
                <Button type="reset" variant="outline" onClick={handleReset}>
                  Réinitialiser
                </Button>
              </div>
              <FieldDescription>
                Filtrez vos prospects selon les différents critères
              </FieldDescription>
              <FieldGroup>
                <Field>
                  <FieldLabel>Départements</FieldLabel>
                  <div className="flex flex-col gap-2 mt-2">
                    {departmentList.map((department) => {
                      // const isChecked = departments.includes(department);
                      return (
                        <label
                          key={department}
                          className="flex gap-2 items-center cursor-pointer text-sm"
                        >
                          <Checkbox
                            id={`dep-${department}`}
                            // checked={isChecked}
                            // onCheckedChange={(checked) =>
                            //   toggleDepartment(department, !!checked)
                            // }
                          />
                          <span>{department}</span>
                        </label>
                      );
                    })}
                  </div>
                </Field>
                <Field>
                  <FieldLabel htmlFor="select-naf">Code NAF</FieldLabel>
                  <Select
                    value={nafCode}
                    onValueChange={(val) => setNafCode(val)}
                  >
                    <SelectTrigger id="select-naf">
                      <SelectValue placeholder="Code NAF" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        {NAFCodes.map((item) => (
                          <SelectItem key={item.value} value={item.value}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </Field>
                <Field>
                  <FieldLabel htmlFor="checkout-7j9-card-number-uw1">
                    Nombre d'employés
                  </FieldLabel>
                  <div className="flex flex-wrap gap-2 w-full">
                    {employeeRanges.map((range) => (
                      <Button
                        key={range}
                        type="button"
                        variant="outline"
                        onClick={() => setNumberOfEmployees(range)}
                        className={`w-32 rounded-md transition-colors ${
                          numberOfEmployees === range
                            ? "bg-blue-600 text-white border-blue-600 hover:bg-blue-700 hover:text-white"
                            : ""
                        }`}
                      >
                        {range.replace("-", " - ")}
                      </Button>
                    ))}
                  </div>
                </Field>
              </FieldGroup>
            </FieldSet>
          </FieldGroup>
          <Button type="submit" className="w-full mt-4">
            Appliquer les filtres
          </Button>
        </form>
      </Card>
      <ProspectsTable />
    </div>
  );
};

export const Route = createFileRoute("/prospects/")({
  component: Propspect,
});

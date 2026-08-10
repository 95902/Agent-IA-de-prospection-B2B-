/* eslint-disable react-refresh/only-export-components */
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/Table";
import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Checkbox";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
} from "@/components/ui/Pagination";
import { MoveLeft, MoveRight } from "lucide-react";
import { Progress } from "@/components/ui/Progress";
import { useState } from "react";
import type { ColumnConfig } from "@/components/DesktopTable";
import { useNavigate } from "@tanstack/react-router";

export interface CompanyData {
  id: string;
  companyName: string;
  contactName: string;
  location: string;
  logoLetter: string;
  logoBgColor: string;
  logoTextColor: string;
  nafCode: string;
  scoringStatus: "Hot" | "Warm" | "Cold";
  scoringPercentage: number;
  lastContactDate: string;
  lastContactType: string;
}

export const companyTableSeed: CompanyData[] = [
  {
    id: "1",
    companyName: "Vercel Inc.",
    contactName: "Guillermo Rauch",
    location: "SF, USA",
    logoLetter: "V",
    logoBgColor: "bg-indigo-100 dark:bg-indigo-950",
    logoTextColor: "text-indigo-600 dark:text-indigo-400",
    nafCode: "6201Z",
    scoringStatus: "Hot",
    scoringPercentage: 92,
    lastContactDate: "Oct 24, 2023",
    lastContactType: "Email Follow-up",
  },
  {
    id: "2",
    companyName: "Stripe Ltd.",
    contactName: "John Collison",
    location: "Dublin, IE",
    logoLetter: "S",
    logoBgColor: "bg-indigo-100 dark:bg-indigo-950",
    logoTextColor: "text-indigo-600 dark:text-indigo-400",
    nafCode: "4619B",
    scoringStatus: "Warm",
    scoringPercentage: 78,
    lastContactDate: "Oct 23, 2023",
    lastContactType: "LinkedIn Connect",
  },
  {
    id: "3",
    companyName: "Anthropic AI",
    contactName: "Dario Amodei",
    location: "Palo Alto",
    logoLetter: "A",
    logoBgColor: "bg-slate-200 dark:bg-slate-800",
    logoTextColor: "text-slate-700 dark:text-slate-300",
    nafCode: "6201Z",
    scoringStatus: "Cold",
    scoringPercentage: 34,
    lastContactDate: "Oct 19, 2023",
    lastContactType: "Initial Outreach",
  },
  {
    id: "4",
    companyName: "Figma Design",
    contactName: "Dylan Field",
    location: "SF",
    logoLetter: "F",
    logoBgColor: "bg-indigo-100 dark:bg-indigo-950",
    logoTextColor: "text-indigo-600 dark:text-indigo-400",
    nafCode: "7022Z",
    scoringStatus: "Hot",
    scoringPercentage: 88,
    lastContactDate: "Oct 25, 2023",
    lastContactType: "Phone Call",
  },
];

const prospectColumns: ColumnConfig[] = [
  { key: "checkbox", label: "" },
  { key: "company", label: "Nom de la compagnie" },
  { key: "status", label: "Code NAF" },
  { key: "score", label: "Notation", className: "w-[200px]" },
  { key: "value", label: "Dernier contact" },
];

export const ProspectsTable = () => {
  const data = companyTableSeed;
  const [currentPage, setCurrentPage] = useState(1);
  const [rowPerPage, setRowPerPage] = useState(10);
  const [selectedItems, setSelectedItems] = useState<Record<string, boolean>>(
    {},
  );

  const totalPages = Math.max(1, Math.ceil(data.length / rowPerPage));
  const startIndex = (currentPage - 1) * rowPerPage;
  const endIndex = startIndex + rowPerPage;
  const paginatedData = data.slice(startIndex, endIndex);
  const navigate = useNavigate();

  const handlePrevious = () => {
    setCurrentPage((prev) => Math.max(prev - 1, 1));
  };

  const handleNext = () => {
    setCurrentPage((prev) => Math.min(prev + 1, totalPages));
  };

  const getProgressColor = (status: CompanyData["scoringStatus"]) => {
    switch (status) {
      case "Hot":
        return "bg-emerald-600";
      case "Warm":
        return "bg-blue-600";
      case "Cold":
        return "bg-rose-700";
      default:
        return "bg-slate-700";
    }
  };

  const getTitleProgressColor = (status: CompanyData["scoringStatus"]) => {
    switch (status) {
      case "Hot":
        return "text-emerald-600";
      case "Warm":
        return "text-blue-600";
      case "Cold":
        return "text-rose-700";
      default:
        return "text-slate-800";
    }
  };

  const handleRowClick = (id: string) => {
    navigate({
      to: "/prospects/$prospectId",
      params: { prospectId: id },
    });
  };

  return (
    <div className="w-full h-full flex flex-col justify-between overflow-hidden border rounded-lg bg-white">
      <div className="flex-1 overflow-y-auto w-full">
        <Table className="w-full">
          <TableHeader className="sticky top-0 bg-white z-10 shadow-sm">
            <TableRow>
              {prospectColumns.map((column, idx) => (
                <TableCell
                  key={column.key || idx}
                  className={`${column.className || ""} font-bold`}
                >
                  {column.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedData.map((item) => {
              const isSelected = !!selectedItems[item.id];
              return (
                <TableRow
                  key={item.id}
                  className={`cursor-pointer transition-colors ${
                    isSelected ? "bg-slate-100/80 hover:bg-slate-100" : ""
                  }`}
                  onClick={() => handleRowClick(item.id)}
                >
                  <TableCell className="w-[10%] text-center">
                    <div
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center justify-center"
                    >
                      <Checkbox
                        id={item.id}
                        checked={isSelected}
                        onCheckedChange={(checked) => {
                          setSelectedItems((prev) => ({
                            ...prev,
                            [item.id]: !!checked,
                          }));
                        }}
                      />
                    </div>
                  </TableCell>
                  <TableCell className="w-[30%]">
                    <div className="font-medium">{item.companyName}</div>
                    <div className="text-xs text-muted-foreground">
                      {item.contactName}
                    </div>
                  </TableCell>
                  <TableCell className="w-[20%]">{item.nafCode}</TableCell>
                  <TableCell className="w-[25%]">
                    <div className="flex flex-col items-center gap-2 w-30">
                      <div className="flex justify-between items-center gap-1 w-full">
                        <p
                          className={`text-xs font-bold ${getTitleProgressColor(
                            item.scoringStatus,
                          )}`}
                        >
                          {item.scoringStatus}
                        </p>
                        <span className="font-bold w-6 text-right text-xs text-muted-foreground">
                          {item.scoringPercentage}%
                        </span>
                      </div>
                      <Progress
                        value={item.scoringPercentage}
                        className="w-30 shrink-0"
                        indicatorClassName={getProgressColor(
                          item.scoringStatus,
                        )}
                      />
                    </div>
                  </TableCell>
                  <TableCell className="w-[25%] font-medium">
                    <div className="flex flex-col gap-1">
                      <p>{item.lastContactDate}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.lastContactType}
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
      <div className="shrink-0 border-t bg-slate-50/50 p-3">
        <div className="flex w-full items-center justify-between gap-4 px-4">
          <div className="flex items-center gap-3">
            <p className="text-sm text-muted-foreground whitespace-nowrap">
              {data.length > 0 ? startIndex + 1 : 0}-
              {Math.min(endIndex, data.length)} sur {data.length} prospects
            </p>
            <Select
              value={rowPerPage.toString()}
              onValueChange={(value) => {
                setRowPerPage(Number(value));
                setCurrentPage(1);
              }}
            >
              <SelectTrigger
                className="w-18 h-8 bg-white"
                id="select-rows-per-page"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent align="end">
                <SelectGroup>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <Pagination className="w-auto m-0">
            <PaginationContent className="gap-2 flex items-center">
              <PaginationItem>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={handlePrevious}
                  disabled={currentPage === 1}
                >
                  <MoveLeft className="h-4 w-4" />
                  <span className="sr-only">Page précédente</span>
                </Button>
              </PaginationItem>

              {Array.from({ length: totalPages }, (_, index) => {
                const pageNumber = index + 1;
                return (
                  <PaginationItem key={pageNumber}>
                    <PaginationLink
                      className="h-8 w-8 cursor-pointer"
                      isActive={currentPage === pageNumber}
                      onClick={() => setCurrentPage(pageNumber)}
                    >
                      {pageNumber}
                    </PaginationLink>
                  </PaginationItem>
                );
              })}

              <PaginationItem>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={handleNext}
                  disabled={currentPage === totalPages}
                >
                  <MoveRight className="h-4 w-4" />
                  <span className="sr-only">Page suivante</span>
                </Button>
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      </div>
    </div>
  );
};

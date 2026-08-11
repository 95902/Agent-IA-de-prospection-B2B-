import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHeader,
  TableRow,
} from "@/components/ui/Table";
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/Popover";
import { Badge } from "@/components/ui/Badge";
import type { PropspectTableProps } from "@/routes";
import { Button } from "./ui/Button";
import { Menu, MoveLeft, MoveRight } from "lucide-react";
import { Progress } from "@/components/ui/Progress";
import { useState } from "react";

export interface DataTableProps {
  data: PropspectTableProps[];
}

export interface ColumnConfig {
  key: string;
  label: string;
  className?: string;
}

const ITEMS_PER_PAGE = 10;

const prospectColumns: ColumnConfig[] = [
  { key: "company", label: "COMPANY & LEAD" },
  { key: "status", label: "STATUS" },
  { key: "score", label: "LEAD SCORE", className: "w-[200px]" },
  { key: "value", label: "VALUE" },
  { key: "actions", label: "ACTIONS", className: "w-12 text-center" },
];
export const DesktopTable = ({ data }: DataTableProps) => {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(data.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentData = data.slice(startIndex, endIndex);

  const handlePrevious = () => {
    setCurrentPage((prev) => Math.max(prev - 1, 1));
  };

  const handleNext = () => {
    setCurrentPage((prev) => Math.min(prev + 1, totalPages));
  };

  const getProgressColor = (status: PropspectTableProps["status"]) => {
    switch (status) {
      case "Qualified":
        return "bg-emerald-600";
      case "Negotiation":
        return "bg-blue-600";
      case "High Priority":
        return "bg-rose-700";
      case "Discovery":
        return "bg-slate-700";
      default:
        return "bg-slate-700";
    }
  };

  const getBadgeStyle = (status: PropspectTableProps["status"]) => {
    switch (status) {
      case "Qualified":
        return "bg-emerald-50 text-emerald-800 hover:bg-emerald-50 border-emerald-200/60";
      case "Negotiation":
        return "bg-blue-50 text-blue-800 hover:bg-blue-50 border-blue-200/60";
      case "High Priority":
        return "bg-rose-50 text-rose-800 hover:bg-rose-50 border-rose-200/60";
      case "Discovery":
        return "bg-slate-100 text-slate-800 hover:bg-slate-100 border-slate-200/60";
      default:
        return "bg-slate-100 text-slate-800";
    }
  };

  return (
    <div className="w-full overflow-hidden border rounded-lg">
      <Table className="w-full">
        <TableHeader>
          <TableRow>
            {prospectColumns.map((column) => (
              <TableCell key={column.key} className={column.className}>
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {currentData.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="w-[35%]">
                <div className="font-medium">{item.companyName}</div>
                <div className="text-xs text-muted-foreground">
                  {item.contactName} • {item.contactRole}
                </div>
              </TableCell>
              <TableCell className="w-[20%]">
                <Badge variant="outline" className={getBadgeStyle(item.status)}>
                  {item.status}
                </Badge>
              </TableCell>
              <TableCell className="w-[25%]">
                <div className="flex items-center gap-2 w-full">
                  <Progress
                    value={item.score}
                    className="w-24 shrink-0"
                    indicatorClassName={getProgressColor(item.status)}
                  />
                  <span className="font-bold text-sm w-6 text-right">
                    {item.score}
                  </span>
                </div>
              </TableCell>
              <TableCell className="w-[15%] font-medium">
                {item.value.toLocaleString("fr-FR")} €
              </TableCell>
              <TableCell className="w-[5%] text-center">
                <Popover>
                  <PopoverTrigger render={<Button variant="outline" />}>
                    <Menu className="h-4 w-4" />
                  </PopoverTrigger>
                  <PopoverContent>
                    <PopoverHeader>
                      <PopoverTitle>{item.companyName}</PopoverTitle>
                      <PopoverDescription>
                        Description text here.
                      </PopoverDescription>
                    </PopoverHeader>
                  </PopoverContent>
                </Popover>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={5}>
              <div className="flex w-full items-center justify-between">
                <p>
                  {startIndex + 1}-{Math.min(endIndex, data.length)} sur{" "}
                  {data.length} prospects
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={handlePrevious}
                    disabled={currentPage === 1}
                  >
                    <MoveLeft />
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleNext}
                    disabled={currentPage === totalPages}
                  >
                    <MoveRight />
                  </Button>
                </div>
              </div>
            </TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  );
};

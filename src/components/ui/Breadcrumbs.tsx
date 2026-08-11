import React from "react";

interface BreadcrumbsProps {
  data: string[];
  step: number;
}
export const Breadcrumbs = ({ data, step }: BreadcrumbsProps) => {
  return (
    <div className="flex gap-2 w-full items-center overflow-hidden">
      {data.map((crumb, index) => {
        const isLast = index === data.length - 1;
        return (
          <React.Fragment key={index} >
            <div
              className={`min-w-8 min-h-8transition-colors duration-500 rounded-full ${step >= index ? "bg-blue-500" : "bg-gray-500"}  shrink-0 items-center justify-center font-semibold flex text-white`}
            >
              {index}
            </div>
            <p
              className={`${step >= index ? "text-blue-500" : "text-gray-500"} transition-colors duration-500  whitespace-nowrap shrink-0`}
            >
              {crumb}
            </p>
            {!isLast && (
              <div className="relative w-full h-1 bg-slate-200 rounded-full overflow-hidden shrink">
                <div
                  className="absolute top-0 left-0 h-full bg-blue-600 rounded-full transition-all duration-500 ease-in-out"
                  style={{
                    width: step > index ? "100%" : "0%",
                  }}
                />
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

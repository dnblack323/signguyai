import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-9 w-full rounded-md border border-[#CBD5E1] bg-[#F5F7FA] px-3 py-1 text-base text-[#0F172A] shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[#0F172A] placeholder:text-[#475569] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2F8BFB] focus-visible:border-[#2F8BFB] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Input.displayName = "Input"

export { Input }

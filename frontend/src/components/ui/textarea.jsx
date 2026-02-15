import * as React from "react"

import { cn } from "@/lib/utils"

const Textarea = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[60px] w-full rounded-md border border-[#CBD5E1] bg-[#F5F7FA] px-3 py-2 text-base text-[#0F172A] shadow-sm placeholder:text-[#475569] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2F8BFB] focus-visible:border-[#2F8BFB] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Textarea.displayName = "Textarea"

export { Textarea }

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-[#2F8BFB] text-white shadow hover:bg-[#1E7AF0]",
        destructive:
          "bg-[#EF4444] text-white shadow-sm hover:bg-[#DC2626]",
        outline:
          "border border-[#CBD5E1] bg-[#F5F7FA] text-[#0F172A] shadow-sm hover:bg-[#E9EEF5] hover:border-[#2F8BFB]",
        secondary:
          "bg-[#E9EEF5] text-[#0F172A] shadow-sm hover:bg-[#CBD5E1]",
        ghost: "text-[#0F172A] hover:bg-[#E7F0FF] hover:text-[#2F8BFB]",
        link: "text-[#2F8BFB] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props} />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }

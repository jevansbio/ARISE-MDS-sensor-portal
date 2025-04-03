"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        type="range"
        className={cn(
          "w-full h-1.5 bg-primary/20 rounded-full appearance-none cursor-pointer",
          "accent-primary",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Slider.displayName = "Slider";

export { Slider } 
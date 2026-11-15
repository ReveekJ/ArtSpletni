import { type CSSProperties, type ReactNode, type SVGProps, useLayoutEffect } from "react";

import { useInView } from "@/lib/useInView";
import { cn } from "@/lib/utils";

const SHAPES = "path, circle, rect, line, polyline, polygon, ellipse";
const LAYERS = ".sk-drawn__pencil, .sk-drawn__ink";

interface DrawnSvgProps extends Omit<SVGProps<SVGSVGElement>, "ref"> {
  children: ReactNode;
  delay?: number;
  pencil?: boolean;
}

export function DrawnSvg({ children, delay = 0, pencil = true, className, style, ...props }: DrawnSvgProps) {
  const [ref, inView] = useInView<SVGSVGElement>();

  useLayoutEffect(() => {
    ref.current?.querySelectorAll(LAYERS).forEach((layer) => {
      layer.querySelectorAll<SVGGeometryElement>(SHAPES).forEach((shape, index) => {
        if (!shape.hasAttribute("stroke-dasharray")) shape.setAttribute("pathLength", "1");
        if (!shape.style.getPropertyValue("--i")) shape.style.setProperty("--i", String(index));
      });
    });
  });

  const motionStyle = { "--draw-delay": `${delay}ms`, ...style } as CSSProperties;
  return (
    <svg ref={ref} data-inview={inView} className={cn("sk-drawn", className)} style={motionStyle} {...props}>
      {pencil ? (
        <g className="sk-drawn__pencil" transform="translate(1.6 1.2)">
          {children}
        </g>
      ) : null}
      <g className="sk-drawn__ink">{children}</g>
    </svg>
  );
}

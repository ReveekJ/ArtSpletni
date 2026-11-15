import { CircleAlert, CircleCheck, Info, Loader2, TriangleAlert } from "lucide-react";
import { Toaster as Sonner, type ToasterProps } from "sonner";

import { useTheme } from "@/lib/theme";

function Toaster(props: ToasterProps) {
  const { resolved } = useTheme();
  return (
    <Sonner
      theme={resolved}
      position="bottom-center"
      icons={{
        success: <CircleCheck className="size-[18px]" strokeWidth={1.8} />,
        info: <Info className="size-[18px]" strokeWidth={1.8} />,
        warning: <TriangleAlert className="size-[18px]" strokeWidth={1.8} />,
        error: <CircleAlert className="size-[18px]" strokeWidth={1.8} />,
        loading: <Loader2 className="size-[18px] animate-spin" strokeWidth={1.8} />,
      }}
      toastOptions={{
        unstyled: true,
        classNames: {
          toast:
            "flex w-full items-center gap-2.5 rounded-md bg-ink px-4 py-3 font-sans text-[15px] font-semibold leading-[1.3] text-paper shadow-[3px_4px_0_var(--brand)]",
          description: "text-[13px] font-normal opacity-80",
          actionButton:
            "ml-auto cursor-pointer rounded-wobble border-0 bg-paper px-3 py-1 text-[13px] font-semibold text-ink",
        },
      }}
      {...props}
    />
  );
}

export { Toaster };

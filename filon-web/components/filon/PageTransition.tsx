"use client";
import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
/** The interface is immediately present; navigation never waits on an exit animation. */
export function PageTransition({ children }: { children: ReactNode }) {
 const pathname = usePathname();
 return <div key={pathname} className="fn-page-enter">{children}</div>;
}

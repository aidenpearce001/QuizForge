"use client";
import { useEffect, ReactNode } from "react";

export default function AntiCopyPaste({ children }: { children: ReactNode }) {
  useEffect(() => {
    const preventCopy = (e: Event) => e.preventDefault();
    const preventKeys = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && ["c", "a", "v", "x"].includes(e.key.toLowerCase())) {
        e.preventDefault();
      }
    };
    document.addEventListener("copy", preventCopy);
    document.addEventListener("cut", preventCopy);
    document.addEventListener("paste", preventCopy);
    document.addEventListener("keydown", preventKeys);
    document.addEventListener("contextmenu", preventCopy);
    document.addEventListener("dragstart", preventCopy);
    return () => {
      document.removeEventListener("copy", preventCopy);
      document.removeEventListener("cut", preventCopy);
      document.removeEventListener("paste", preventCopy);
      document.removeEventListener("keydown", preventKeys);
      document.removeEventListener("contextmenu", preventCopy);
      document.removeEventListener("dragstart", preventCopy);
    };
  }, []);
  return <div style={{ userSelect: "none", WebkitUserSelect: "none" }}>{children}</div>;
}

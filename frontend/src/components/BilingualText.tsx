type Props = {
  text: string;
  sep?: string;
  variant?: "question" | "choice";
};

export function BilingualText({ text, sep = "\n\n", variant = "choice" }: Props) {
  const idx = text.indexOf(sep);
  if (idx === -1) return <>{text}</>;

  const en = text.slice(0, idx);
  const vi = text.slice(idx + sep.length);

  if (variant === "question") {
    return (
      <>
        <span className="block">{en}</span>
        <span className="block mt-3 pt-3 border-t border-gray-700/40 text-base font-normal text-gray-400 leading-relaxed">
          {vi}
        </span>
      </>
    );
  }

  // choice: en flows inline (inherits parent color), vi wraps below in muted gray
  return (
    <>
      {en}
      <span className="block text-xs text-gray-500 mt-0.5 leading-snug">{vi}</span>
    </>
  );
}

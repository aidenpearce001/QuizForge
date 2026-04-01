import StudentNav from "@/components/StudentNav";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StudentNav />
      {children}
    </>
  );
}

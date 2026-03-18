"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { api, apiFetch } from "@/lib/api";

type Subject = { id: string; name: string };
type PdfUpload = {
  id: string;
  filename: string;
  status: string;
  questions_extracted: number;
  error_message?: string;
};

export default function UploadsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [pdfs, setPdfs] = useState<PdfUpload[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    api.getSubjects().then((s: Subject[]) => {
      setSubjects(s);
      if (s.length > 0) setSelectedSubject(s[0].id);
    });
  }, []);

  const fetchPdfs = useCallback(() => {
    if (!selectedSubject) return;
    api.getPdfs(selectedSubject).then(setPdfs);
  }, [selectedSubject]);

  useEffect(() => {
    fetchPdfs();
  }, [fetchPdfs]);

  // Poll while any upload is pending or processing
  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    const hasPending = pdfs.some((p) => p.status === "pending" || p.status === "processing");
    if (hasPending) {
      pollRef.current = setInterval(fetchPdfs, 5000);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [pdfs, fetchPdfs]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !selectedSubject) return;
    setError("");
    setUploading(true);
    try {
      await api.uploadPdfs(selectedSubject, e.target.files);
      fetchPdfs();
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleDelete = async (pdfId: string) => {
    if (!confirm("Delete this upload and its questions?")) return;
    try {
      await apiFetch(`/api/subjects/${selectedSubject}/pdfs/${pdfId}`, { method: "DELETE" });
      fetchPdfs();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleReprocess = async (pdfId: string) => {
    try {
      await apiFetch(`/api/subjects/${selectedSubject}/pdfs/${pdfId}/reprocess`, { method: "POST" });
      fetchPdfs();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      pending: "bg-yellow-900/50 text-yellow-400",
      processing: "bg-blue-900/50 text-blue-400",
      done: "bg-green-900/50 text-green-400",
      error: "bg-red-900/50 text-red-400",
    };
    return (
      <span className={`text-xs px-2 py-0.5 rounded ${map[status] || "bg-gray-800 text-gray-500"}`}>
        {status}
      </span>
    );
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">PDF Uploads</h1>

      <div className="flex gap-3 items-end mb-6">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Subject</label>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-100 focus:outline-none focus:border-blue-500"
          >
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>
        <div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            multiple
            onChange={handleUpload}
            className="hidden"
            id="pdf-upload"
          />
          <label
            htmlFor="pdf-upload"
            className={`inline-block cursor-pointer bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2 text-sm font-medium ${
              uploading ? "opacity-50 pointer-events-none" : ""
            }`}
          >
            {uploading ? "Uploading..." : "Upload PDFs"}
          </label>
        </div>
      </div>

      {error && <p className="text-sm text-red-400 mb-4">{error}</p>}

      {pdfs.length === 0 ? (
        <p className="text-gray-500">No uploads yet.</p>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                <th className="text-left p-3">Filename</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Questions</th>
                <th className="text-left p-3"></th>
              </tr>
            </thead>
            <tbody>
              {pdfs.map((p) => (
                <tr key={p.id} className="border-b border-gray-800 last:border-0">
                  <td className="p-3 text-gray-200">{p.filename}</td>
                  <td className="p-3">{statusBadge(p.status)}</td>
                  <td className="p-3 text-gray-400">{p.questions_extracted}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      {p.status === "error" && (
                        <>
                          <span className="text-xs text-red-400 truncate max-w-[200px]" title={p.error_message}>
                            {p.error_message}
                          </span>
                          <button
                            onClick={() => handleReprocess(p.id)}
                            className="text-xs text-blue-400 hover:underline whitespace-nowrap"
                          >
                            Reprocess
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="text-xs text-red-400 hover:underline whitespace-nowrap"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, X, FileText, Image, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

interface UploadedFile {
  file_id: string;
  filename: string;
  status: "uploading" | "confirmed" | "error";
  progress: number;
  error?: string;
}

interface FileUploadProps {
  projectId: string;
  token: string;
  category: string;
  portalPrefix?: string;
  accept?: string;
  multiple?: boolean;
  maxSizeMB?: number;
  onUploadComplete?: (fileId: string, filename: string) => void;
  onUploadError?: (filename: string, error: string) => void;
}

const ICON_MAP: Record<string, typeof FileText> = {
  "image/": Image,
  "application/pdf": FileText,
};

function getFileIcon(mimeType: string) {
  for (const [prefix, Icon] of Object.entries(ICON_MAP)) {
    if (mimeType.startsWith(prefix)) return Icon;
  }
  return FileText;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileUpload({
  projectId,
  token,
  category,
  portalPrefix = "/api/gc",
  accept,
  multiple = true,
  maxSizeMB = 100,
  onUploadComplete,
  onUploadError,
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFile = useCallback(
    async (file: File) => {
      const fileEntry: UploadedFile = {
        file_id: "",
        filename: file.name,
        status: "uploading",
        progress: 0,
      };

      setFiles((prev) => [...prev, fileEntry]);
      const idx = files.length;

      // Client-side size check
      if (file.size > maxSizeMB * 1024 * 1024) {
        setFiles((prev) =>
          prev.map((f) =>
            f.filename === file.name
              ? { ...f, status: "error" as const, error: `Exceeds ${maxSizeMB}MB limit` }
              : f
          )
        );
        onUploadError?.(file.name, `Exceeds ${maxSizeMB}MB limit`);
        return;
      }

      try {
        // Step 1: Get pre-signed URL
        const { data } = await fetchWithAuth(
          `${portalPrefix}/projects/${projectId}/files/upload-url`,
          token,
          {
            method: "POST",
            body: JSON.stringify({
              filename: file.name,
              content_type: file.type || "application/octet-stream",
              category,
              file_size_bytes: file.size,
            }),
          }
        );

        const fileId = data.file_id;
        setFiles((prev) =>
          prev.map((f) =>
            f.filename === file.name ? { ...f, file_id: fileId } : f
          )
        );

        // Step 2: Upload to S3 with progress tracking
        await new Promise<void>((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open("PUT", data.upload_url);
          xhr.setRequestHeader("Content-Type", file.type || "application/octet-stream");

          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
              const progress = Math.round((e.loaded / e.total) * 100);
              setFiles((prev) =>
                prev.map((f) =>
                  f.file_id === fileId ? { ...f, progress } : f
                )
              );
            }
          };

          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve();
            } else {
              reject(new Error(`S3 upload failed: ${xhr.status}`));
            }
          };
          xhr.onerror = () => reject(new Error("Upload failed"));
          xhr.send(file);
        });

        // Step 3: Confirm upload
        await fetchWithAuth(
          `${portalPrefix}/projects/${projectId}/files/${fileId}/confirm`,
          token,
          { method: "POST" }
        );

        setFiles((prev) =>
          prev.map((f) =>
            f.file_id === fileId
              ? { ...f, status: "confirmed" as const, progress: 100 }
              : f
          )
        );
        onUploadComplete?.(fileId, file.name);
      } catch (err: any) {
        setFiles((prev) =>
          prev.map((f) =>
            f.filename === file.name
              ? { ...f, status: "error" as const, error: err.message || "Upload failed" }
              : f
          )
        );
        onUploadError?.(file.name, err.message || "Upload failed");
      }
    },
    [projectId, token, category, portalPrefix, maxSizeMB, onUploadComplete, onUploadError, files.length]
  );

  const handleFiles = useCallback(
    (fileList: FileList) => {
      Array.from(fileList).forEach(uploadFile);
    },
    [uploadFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.file_id !== fileId));
  };

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragging
            ? "border-blue-400 bg-blue-50"
            : "border-gray-300 hover:border-gray-400 hover:bg-gray-50"
        }`}
      >
        <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-600">
          Drag and drop files here, or <span className="text-blue-600 font-medium">browse</span>
        </p>
        <p className="text-xs text-gray-400 mt-1">Max {maxSizeMB}MB per file</p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="hidden"
        />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((f, i) => {
            const Icon = f.status === "confirmed" ? CheckCircle : f.status === "error" ? AlertCircle : Loader2;
            const iconColor =
              f.status === "confirmed" ? "text-green-500" : f.status === "error" ? "text-red-500" : "text-blue-500";

            return (
              <li key={f.file_id || i} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
                <Icon className={`h-4 w-4 flex-shrink-0 ${iconColor} ${f.status === "uploading" ? "animate-spin" : ""}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{f.filename}</p>
                  {f.status === "uploading" && (
                    <div className="mt-1 h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all duration-300"
                        style={{ width: `${f.progress}%` }}
                      />
                    </div>
                  )}
                  {f.error && <p className="text-xs text-red-500 mt-0.5">{f.error}</p>}
                </div>
                {f.status !== "uploading" && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(f.file_id);
                    }}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

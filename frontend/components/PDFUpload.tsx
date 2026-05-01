"use client";

import React, { useState, useRef } from "react";

export default function PDFUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== "application/pdf") {
        setStatus("error");
        setMessage("Please select a PDF file.");
        return;
      }
      setFile(selectedFile);
      uploadFile(selectedFile);
    }
  };

  const uploadFile = async (selectedFile: File) => {
    setStatus("uploading");
    setMessage("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        setStatus("error");
        setMessage(data.error || "Upload failed");
      } else {
        setStatus("success");
        setMessage(`✓ ${selectedFile.name} ingested — ${data.total_chunks} chunks created`);
      }
    } catch (error: any) {
      setStatus("error");
      setMessage(error.message || "Network error occurred while uploading.");
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <div 
        onClick={triggerFileSelect}
        className="border-2 border-dashed border-neutral-700 rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer hover:border-neutral-500 hover:bg-neutral-900 transition-colors"
      >
        <input 
          type="file" 
          accept="application/pdf" 
          className="hidden" 
          ref={fileInputRef}
          onChange={handleFileSelect}
        />
        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-neutral-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p className="text-neutral-300 font-medium">Click or drag PDF to upload</p>
        <p className="text-neutral-500 text-sm mt-1">Only .pdf files are supported</p>
      </div>

      {status === "uploading" && (
        <div className="mt-4 p-3 bg-neutral-800 text-neutral-300 rounded flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-neutral-400 border-t-transparent rounded-full animate-spin mr-2"></div>
          Uploading and processing...
        </div>
      )}

      {status === "success" && (
        <div className="mt-4 p-3 bg-green-900/50 border border-green-800 text-green-300 rounded text-sm">
          {message}
        </div>
      )}

      {status === "error" && (
        <div className="mt-4 p-3 bg-red-900/50 border border-red-800 text-red-300 rounded text-sm">
          {message}
        </div>
      )}
    </div>
  );
}

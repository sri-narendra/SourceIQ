"use client";

import { useCallback, useState } from "react";

import { documentApi } from "@/services/api-endpoints";
import type { IDocument } from "@/types";

export function useDocuments(workspaceId?: string) {
  const [documents, setDocuments] = useState<IDocument[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setDocuments(await documentApi.list(workspaceId));
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  const upload = useCallback(
    async (file: File) => {
      if (!workspaceId) return;
      await documentApi.upload(workspaceId, file);
      await load();
    },
    [workspaceId, load]
  );

  const remove = useCallback(
    async (documentId: string) => {
      await documentApi.remove(documentId);
      await load();
    },
    [load]
  );

  return { documents, loading, load, upload, remove };
}
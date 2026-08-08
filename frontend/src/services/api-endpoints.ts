import api from "@/services/api";
import type {
  IChatRequest,
  IChatResponse,
  IDashboard,
  IDocument,
  ISearchResult,
  IUser,
  IWorkspace,
} from "@/types";

export const authApi = {
  register: (name: string, email: string, password: string) =>
    api.post("/auth/register", { name, email, password }),
  login: async (email: string, password: string) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("token", data.access_token);
    return data as { user: IUser; access_token: string };
  },
  me: async () => (await api.get<IUser>("/auth/me")).data,
};

export const workspaceApi = {
  create: (name: string, description?: string) =>
    api.post("/workspaces", { name, description }),
  list: async () => (await api.get<IWorkspace[]>("/workspaces")).data,
  remove: (workspaceId: string) => api.delete(`/workspaces/${workspaceId}`),
};

export const documentApi = {
  upload: async (workspaceId: string, file: File) => {
    const form = new FormData();
    form.append("workspace_id", workspaceId);
    form.append("file", file);
    return api.post("/documents/upload", form);
  },
  list: async (workspaceId?: string) =>
    (
      await api.get<IDocument[]>("/documents", {
        params: workspaceId ? { workspace_id: workspaceId } : {},
      })
    ).data,
  remove: (documentId: string) => api.delete(`/documents/${documentId}`),
  preview: async (documentId: string) =>
    (await api.get<{ id: string; name: string; content: string }>(
      `/documents/${documentId}/preview`,
    )).data,
  fileUrl: async (documentId: string) => {
    const res = await api.get(`/documents/${documentId}/file`, {
      responseType: "blob",
    });
    return URL.createObjectURL(res.data);
  },
};

export const chatApi = {
  ask: async (body: IChatRequest) =>
    (await api.post<IChatResponse>("/chat", body)).data,
  history: (conversationId: string) =>
    api.get("/chat/history", { params: { conversation_id: conversationId } }),
  remove: (conversationId: string) => api.delete(`/chat/${conversationId}`),
};

export const searchApi = {
  semantic: async (workspaceId: string, query: string) =>
    (
      await api.post<{ results: ISearchResult[] }>("/search", {
        workspace_id: workspaceId,
        query,
      })
    ).data.results,
};

export const dashboardApi = {
  summary: async () => (await api.get<IDashboard>("/dashboard")).data,
};
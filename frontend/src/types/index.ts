export interface IUser {
  id: string;
  name: string;
  email: string;
}

export interface IWorkspace {
  id: string;
  name: string;
  description?: string | null;
  documents: number;
}

export interface IDocument {
  id: string;
  name: string;
  status: "uploading" | "processing" | "completed" | "failed";
  uploaded_at: string;
}

export interface IMessage {
  role: "user" | "assistant";
  content: string;
}

export interface IChatSource {
  document_id?: string | null;
  document: string;
  page?: number | null;
  score: number;
  content?: string;
}

export interface IChatRequest {
  workspace_id: string;
  message: string;
  conversation_id?: string;
}

export interface IChatResponse {
  answer: string;
  sources: IChatSource[];
  conversation_id?: string | null;
}

export interface ISearchResult {
  document: string;
  page?: number | null;
  text: string;
  score: number;
}

export interface IDashboard {
  documents: number;
  conversations: number;
  storage_used_mb: number;
  workspace_count: number;
}

export type UserRole = "user" | "admin";
export type DocumentStatus = "uploading" | "processing" | "completed" | "failed";
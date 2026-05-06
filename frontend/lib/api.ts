import type {
  AskResponse,
  AuthResponse,
  Flashcard,
  ProgressSummary,
  Quiz,
  QuizAttempt,
  StudyDocument,
  User,
  WeakTopic,
} from "@/types";

const TOKEN_KEY = "studywise_token";

function getApiUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  return "/api/v1";
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${getApiUrl()}${path}`, { ...options, headers });
  } catch {
    throw new Error("Could not reach the backend. Check that the API server and Next.js proxy are running.");
  }
  if (!response.ok) {
    let message = "Request failed.";
    try {
      const error = await response.json();
      message = error.detail ?? message;
    } catch {
      message = response.statusText;
    }
    if (response.status === 401) {
      clearToken();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/auth")) {
        const next = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.assign(`/auth/login?session=expired&next=${next}`);
      }
      throw new Error("Your session expired. Please log in again.");
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  register: (payload: { name: string; email: string; password: string }) =>
    request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { name: string; password: string }) =>
    request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request<User>("/users/me"),
  documents: () => request<StudyDocument[]>("/documents"),
  document: (documentId: string) => request<StudyDocument>(`/documents/${documentId}`),
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<StudyDocument>("/documents", { method: "POST", body: formData });
  },
  ask: (documentId: string, question: string) =>
    request<AskResponse>(`/documents/${documentId}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  quizzes: () => request<Quiz[]>("/quizzes"),
  quiz: (quizId: string) => request<Quiz>(`/quizzes/${quizId}`),
  createQuiz: (documentId: string, question_count: number, difficulty: string) =>
    request<Quiz>(`/documents/${documentId}/quizzes`, {
      method: "POST",
      body: JSON.stringify({ question_count, difficulty }),
    }),
  submitQuiz: (quizId: string, answers: Record<string, string>) =>
    request<QuizAttempt>(`/quizzes/${quizId}/attempts`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),
  flashcards: (documentId: string) => request<Flashcard[]>(`/documents/${documentId}/flashcards`),
  createFlashcards: (documentId: string) =>
    request<Flashcard[]>(`/documents/${documentId}/flashcards`, { method: "POST" }),
  progressSummary: () => request<ProgressSummary>("/progress/summary"),
  weakTopics: () => request<WeakTopic[]>("/progress/weak-topics"),
  recommendations: () => request<{ topic: string; message: string; priority: string }[]>("/progress/recommendations"),
  evaluation: () => request<{ metric_name: string; metric_value: number }[]>("/evaluation/metrics"),
};

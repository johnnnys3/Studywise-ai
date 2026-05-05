export type User = {
  id: string;
  name: string;
  email: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type StudyDocument = {
  id: string;
  user_id: string;
  title: string;
  original_filename: string;
  file_type: string;
  file_path: string;
  status: "uploaded" | "processing" | "ready" | "failed";
  error_message: string | null;
  total_pages: number;
  chunk_count: number;
  created_at: string;
  updated_at: string;
  chunks?: DocumentChunk[];
};

export type DocumentChunk = {
  id: string;
  document_id: string;
  user_id: string;
  chunk_index: number;
  chunk_text: string;
  page_number: number;
  page_start?: number;
  page_end?: number;
  section_title?: string | null;
  section_path_json?: string[];
  content_type?: string;
  token_count: number;
  quality_score?: number;
  text_hash?: string;
  vector_id: string;
};

export type Citation = {
  document_id: string;
  chunk_id: string;
  page_number: number;
  page_start?: number;
  page_end?: number;
  chunk_index: number;
  section_title?: string | null;
  source_label?: string;
};

export type AskResponse = {
  answer: string;
  citations: Citation[];
  retrieved_context: DocumentChunk[];
};

export type QuizQuestion = {
  id: string;
  quiz_id: string;
  question: string;
  options_json: string[];
  correct_answer: string;
  explanation: string;
  difficulty?: "easy" | "medium" | "hard";
  topic: string;
  source_page: number;
  source_chunk_id?: string;
  cognitive_skill?: string;
};

export type Quiz = {
  id: string;
  user_id: string;
  document_id: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  question_count: number;
  created_at: string;
  questions: QuizQuestion[];
};

export type QuizAttempt = {
  id: string;
  user_id: string;
  quiz_id: string;
  score: number;
  total_questions: number;
  percentage: number;
};

export type WeakTopic = {
  id: string;
  user_id: string;
  topic: string;
  document_id?: string;
  source_page?: number;
  source_chunk_id?: string;
  difficulty?: string;
  cognitive_skill?: string;
  review_recommendation?: string;
  correct_count: number;
  incorrect_count: number;
  accuracy: number;
};

export type ProgressSummary = {
  total_documents: number;
  quizzes_completed: number;
  average_quiz_score: number;
  weak_topic_count: number;
  recent_attempts: QuizAttempt[];
};

export type Flashcard = {
  id: string;
  user_id: string;
  document_id: string;
  front: string;
  back: string;
  topic: string;
  source_page: number;
  source_chunk_id?: string;
  difficulty?: string;
};

/**
 * Pattern Library Types - Bundle 31.0.5
 */

export type PatternRecord = {
  pattern_id: string;
  name: string;
  description?: string | null;
  tags: string[];
  generator_key: string;
  params: Record<string, any>;
  created_at: string;
  updated_at: string;
};

export type PatternSummary = {
  pattern_id: string;
  name: string;
  tags: string[];
  generator_key: string;
  updated_at: string;
};

export type PatternListResponse = {
  items: PatternSummary[];
};

export type PatternCreateRequest = {
  name: string;
  description?: string | null;
  tags?: string[];
  generator_key: string;
  params?: Record<string, any>;
};

export type PatternUpdateRequest = Partial<{
  name: string;
  description: string | null;
  tags: string[];
  generator_key: string;
  params: Record<string, any>;
}>;

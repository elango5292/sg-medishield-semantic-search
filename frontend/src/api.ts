import type { SearchResponse } from './types';

const API_URL = import.meta.env.VITE_API_URL || '';

export async function searchDocuments(
  query: string,
  topK: number = 5
): Promise<SearchResponse> {
  const response = await fetch(`${API_URL}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
  });

  if (!response.ok) {
    throw new Error('Search failed');
  }

  return response.json();
}

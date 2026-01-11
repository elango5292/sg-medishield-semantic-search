export interface Coordinates {
  points: number[][];
  system: string;
  layout_width: number;
  layout_height: number;
}

export interface SearchResult {
  id: string;
  score: number;
  text: string;
  page: number;
  node_type: string;
  coordinates: string;
}

export interface SearchResponse {
  results: SearchResult[];
}

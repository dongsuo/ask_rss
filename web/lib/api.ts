import axios from 'axios';

// Use the environment variable with a fallback for development
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface SearchResult {
  title: string;
  link: string;
  source_url: string;
  published: string;
  summary: string;
  score: number;
}

export interface ProcessRSSResult {
  status: string;
  message: string;
  source_url: string;
  articles_processed: number;
  dataset_name?: string;
  hf_repo?: string;
}

export interface ProcessRSSResponse {
  status: string;
  message: string;
  results: ProcessRSSResult[];
  total_feeds: number;
  successful_feeds: number;
  total_articles: number;
}

export const addFeedSource = async (url: string, maxArticles: number = 100): Promise<ProcessRSSResult> => {
  const response = await api.post<ProcessRSSResponse>('/process-rss', {
    rss_urls: [url],
    max_articles: maxArticles
  });
  
  if (!response.data.results || response.data.results.length === 0) {
    throw new Error('No results returned from the server');
  }
  
  return response.data.results[0]; // Return the first result since we're processing one URL at a time
};

export interface SearchResult {
  title: string;
  link: string;
  source_url: string;
  published: string;
  summary: string;
  score: number;
}

export const searchFeeds = async (query: string, sourcePaths: string[] = []): Promise<SearchResult[]> => {
  try {
    const response = await api.post('/semantic-search', {
      query,
      source_url: sourcePaths.length > 0 ? sourcePaths[0] : undefined, // For now, just use the first source path
    });
    
    // The backend returns results in the format { results: SearchResult[] }
    return response.data?.results || [];
  } catch (error) {
    console.error('Error searching feeds:', error);
    throw new Error('Failed to search feeds');
  }
};

export interface FeedSource {
  name: string;
  path: string;
  article_count: number;
  last_modified: string;
  last_article?: string;
  size_mb: number;
}

export const listFeedSources = async (): Promise<FeedSource[]> => {
  try {
    const response = await api.get<FeedSource[]>('/sources');
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Error fetching feed sources:', error);
    throw new Error('Failed to fetch feed sources');
  }
};

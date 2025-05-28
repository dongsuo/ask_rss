'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { 
  listFeedSources, 
  searchFeeds, 
  SearchResult,
  FeedSource
} from '@/lib/api';
import { 
  MagnifyingGlassIcon, 
  Cog6ToothIcon 
} from '@heroicons/react/24/outline';

export default function Home() {
  const [query, setQuery] = useState('');
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: sources = [], isLoading } = useQuery({
    queryKey: ['feedSources'],
    queryFn: listFeedSources,
  });

  const searchQuery = useMemo(() => ({
    query,
    sources: selectedSources,
  }), [query, selectedSources]);

  const { data: searchResults, refetch } = useQuery<SearchResult[]>({
    queryKey: ['search', searchQuery],
    queryFn: async ({ queryKey }) => {
      const [_, { query: searchQuery, sources: selectedSources }] = queryKey as [string, { query: string; sources: string[] }];
      
      if (!searchQuery.trim()) return [];
      
      try {
        // Get the full source objects for the selected source names
        const selectedSourceObjects = sources.filter(source => 
          selectedSources.includes(source.name)
        );
        
        // Extract the source paths
        const sourcePaths = selectedSourceObjects.map(source => source.path);
        
        const response = await searchFeeds(searchQuery, sourcePaths);
        return Array.isArray(response) ? response : [];
      } catch (error) {
        console.error('Search error:', error);
        return [];
      }
    },
    enabled: false, // We'll trigger this manually
    initialData: [],
  });

  // Ensure searchResults is always an array
  const results = Array.isArray(searchResults) ? searchResults : [];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    if (selectedSources.length === 0) {
      setError('Please select at least one source to search');
      return;
    }
    
    setError(null);
    setIsSearching(true);
    
    try {
      // Trigger the search by refetching with the current query and sources
      const { data } = await refetch();
      
      if (data && data.length === 0) {
        setError('No results found. Try different search terms or sources.');
      }
    } catch (error) {
      setError('Failed to perform search. Please try again.');
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleSource = (sourceName: string) => {
    setSelectedSources((prev: string[]) => 
      prev.includes(sourceName)
        ? prev.filter((name: string) => name !== sourceName)
        : [...prev, sourceName]
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">RSS Feed Search</h1>
          <Link 
            href="/settings" 
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <Cog6ToothIcon className="h-5 w-5 mr-2" />
            Manage Sources
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Source Selection */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Sources</h2>
            
            {isLoading ? (
              <p className="text-gray-500">Loading sources...</p>
            ) : sources.length === 0 ? (
              <p className="text-gray-500">No sources found. Add some in the settings.</p>
            ) : (
              <div className="space-y-2">
                <div className="text-sm text-gray-500 mb-2">
                  {selectedSources.length} of {sources.length} selected
                </div>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  <ul>
                    {sources.map((source) => (
                      <li key={source.name} className="flex items-center">
                        <input
                          type="checkbox"
                          id={source.name}
                          checked={selectedSources.includes(source.name)}
                          onChange={() => toggleSource(source.name)}
                          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <label htmlFor={source.name} className="ml-3 text-sm text-gray-700">
                          {source.name} ({source.article_count} articles)
                        </label>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Search and Results */}
          <div className="lg:col-span-3">
            <div className="bg-white p-6 rounded-lg shadow mb-6">
              <form onSubmit={handleSearch} className="space-y-4">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Search across your RSS feeds..."
                      className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isSearching || !query.trim()}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSearching ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </form>
              
              {error && (
                <div className="mt-4 p-4 bg-red-50 rounded-md">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}
            </div>

            {/* Search Results */}
            <div className="space-y-4">
              {results.map((result, index) => (
                <div key={index} className="bg-white p-6 rounded-lg shadow">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900">{result.title}</h3>
                      {result.summary && (
                        <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                          {result.summary}
                        </p>
                      )}
                      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500">
                        <div className="flex items-center">
                          <span className="font-medium">Source:</span>
                          <span className="ml-1 text-indigo-600">
                            {result.source_url ? new URL(result.source_url).hostname : 'Unknown'}
                          </span>
                        </div>
                        {result.published && (
                          <div className="flex items-center">
                            <span className="font-medium">Published:</span>
                            <span className="ml-1">
                              {new Date(result.published).toLocaleDateString()}
                            </span>
                          </div>
                        )}
                        <div className="flex items-center">
                          <span className="font-medium">Score:</span>
                          <span className="ml-1">
                            {result.score.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <a
                      href={result.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-4 inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 whitespace-nowrap"
                    >
                      Read Article
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

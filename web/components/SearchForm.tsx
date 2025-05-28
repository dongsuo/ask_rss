import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchFeeds } from '@/lib/api';
import { MagnifyingGlassIcon, XCircleIcon } from '@heroicons/react/24/outline';
import FeedSourceList from './FeedSourceList';

export default function SearchForm() {
  const [query, setQuery] = useState('');
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const { data: results = [], refetch, isFetching, error } = useQuery({
    queryKey: ['search', query, selectedSources],
    queryFn: () => searchFeeds(query, selectedSources),
    enabled: false, // Disable automatic query on mount
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    try {
      await refetch();
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSourceToggle = (url: string, isSelected: boolean) => {
    setSelectedSources(prev => 
      isSelected 
        ? [...prev, url] 
        : prev.filter(sourceUrl => sourceUrl !== url)
    );
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search in your feeds..."
            className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
            disabled={isSearching}
          />
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <div className="sticky top-4">
            <FeedSourceList 
              selectedSources={selectedSources} 
              onSelectSource={handleSourceToggle} 
            />
          </div>
        </div>
        
        <div className="lg:col-span-3 space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <XCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Error performing search
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    {error instanceof Error ? error.message : 'An unknown error occurred'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {isFetching && (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          )}

          {!isFetching && results.length > 0 && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">
                Found {results.length} result{results.length !== 1 ? 's' : ''}
              </p>
              <div className="space-y-4">
                {results.map((result, index) => (
                  <div key={`${result.link}-${index}`} className="rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between">
                      <h3 className="text-lg font-medium text-indigo-600 hover:underline">
                        <a href={result.link} target="_blank" rel="noopener noreferrer">
                          {result.title}
                        </a>
                      </h3>
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                        {new URL(result.source_url).hostname}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      {new Date(result.published).toLocaleDateString()}
                      <span className="mx-2">•</span>
                      Score: {result.score.toFixed(2)}
                    </p>
                    <p className="mt-2 text-sm text-gray-700 line-clamp-3">
                      {result.summary}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!isFetching && query && results.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No results found for "{query}"</p>
              <p className="text-sm text-gray-400 mt-1">Try different keywords or check your search query</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';
import { listFeedSources } from '@/lib/api';
import { TrashIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface FeedSourceListProps {
  selectedSources: string[];
  onSelectSource: (url: string, isSelected: boolean) => void;
}

export default function FeedSourceList({ selectedSources, onSelectSource }: FeedSourceListProps) {
  const { data: sources = [], isLoading, error, refetch } = useQuery({
    queryKey: ['feedSources'],
    queryFn: listFeedSources,
  });

  if (isLoading) {
    return <div className="text-gray-500">Loading feed sources...</div>;
  }

  if (error) {
    return (
      <div className="text-red-600">
        Error loading feed sources: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  if (sources.length === 0) {
    return <div className="text-gray-500">No feed sources added yet.</div>;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Feed Sources</h3>
        <button
          onClick={() => refetch()}
          className="text-gray-500 hover:text-gray-700"
          title="Refresh sources"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>
      <div className="max-h-60 overflow-y-auto rounded-md border border-gray-200">
        <ul className="divide-y divide-gray-200">
          {sources.map((source) => (
            <li key={source.url} className="p-3 hover:bg-gray-50">
              <div className="flex items-center">
                <input
                  id={`source-${source.url}`}
                  name="source"
                  type="checkbox"
                  checked={selectedSources.includes(source.url)}
                  onChange={(e) => onSelectSource(source.url, e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor={`source-${source.url}`} className="ml-3 flex-1 min-w-0">
                  <div className="flex justify-between">
                    <p className="truncate text-sm font-medium text-gray-700">
                      {source.url}
                    </p>
                    <span className="text-xs text-gray-500">
                      {source.article_count || 0} articles
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">
                    {source.status} • Last updated: {source.last_processed || 'Never'}
                  </p>
                </label>
                <button
                  type="button"
                  className="ml-2 text-gray-400 hover:text-red-500"
                  onClick={() => {}}
                  title="Remove feed"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

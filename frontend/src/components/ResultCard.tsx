import type { SearchResult } from '../types';

interface ResultCardProps {
  result: SearchResult;
  isSelected: boolean;
  onClick: () => void;
}

export function ResultCard({ result, isSelected, onClick }: ResultCardProps) {
  const relevancePercent = Math.round(result.score * 100);

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-lg border transition-all
                  ${isSelected 
                    ? 'border-blue-500 bg-blue-50 shadow-md' 
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                  }`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
          Page {result.page}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded
                         ${relevancePercent >= 70 ? 'bg-green-100 text-green-700' : 
                           relevancePercent >= 50 ? 'bg-yellow-100 text-yellow-700' : 
                           'bg-slate-100 text-slate-600'}`}>
          {relevancePercent}% match
        </span>
      </div>
      <p className="text-sm text-slate-700 line-clamp-3">{result.text}</p>
    </button>
  );
}

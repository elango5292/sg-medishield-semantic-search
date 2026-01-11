import { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import type { SearchResult, Coordinates } from '../types';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
  pdfUrl: string;
  selectedResult: SearchResult | null;
}

export function PDFViewer({ pdfUrl, selectedResult }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1);
  const containerRef = useRef<HTMLDivElement>(null);
  const [pageDimensions, setPageDimensions] = useState<{ width: number; height: number } | null>(null);

  useEffect(() => {
    if (selectedResult?.page) {
      setPageNumber(selectedResult.page);
    }
  }, [selectedResult]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const onPageLoadSuccess = ({ width, height }: { width: number; height: number }) => {
    setPageDimensions({ width, height });
  };

  const getHighlightStyle = (): React.CSSProperties | null => {
    if (!selectedResult?.coordinates || !pageDimensions) return null;

    try {
      const coords: Coordinates = JSON.parse(selectedResult.coordinates);
      const points = coords.points;
      
      const scaleX = pageDimensions.width / coords.layout_width;
      const scaleY = pageDimensions.height / coords.layout_height;

      const minX = Math.min(...points.map(p => p[0])) * scaleX;
      const minY = Math.min(...points.map(p => p[1])) * scaleY;
      const maxX = Math.max(...points.map(p => p[0])) * scaleX;
      const maxY = Math.max(...points.map(p => p[1])) * scaleY;

      return {
        position: 'absolute',
        left: `${minX}px`,
        top: `${minY}px`,
        width: `${maxX - minX}px`,
        height: `${maxY - minY}px`,
        backgroundColor: 'rgba(59, 130, 246, 0.25)',
        border: '2px solid rgba(59, 130, 246, 0.6)',
        borderRadius: '2px',
        pointerEvents: 'none',
      };
    } catch {
      return null;
    }
  };

  const highlightStyle = selectedResult?.page === pageNumber ? getHighlightStyle() : null;

  return (
    <div className="flex flex-col h-full bg-slate-100 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-slate-200">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPageNumber(p => Math.max(1, p - 1))}
            disabled={pageNumber <= 1}
            className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-40"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span className="text-sm text-slate-600">
            Page {pageNumber} of {numPages}
          </span>
          <button
            onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}
            disabled={pageNumber >= numPages}
            className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-40"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setScale(s => Math.max(0.5, s - 0.1))}
            className="p-1.5 rounded hover:bg-slate-100"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <span className="text-sm text-slate-600 w-12 text-center">{Math.round(scale * 100)}%</span>
          <button
            onClick={() => setScale(s => Math.min(2, s + 0.1))}
            className="p-1.5 rounded hover:bg-slate-100"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
      </div>
      
      <div ref={containerRef} className="flex-1 overflow-auto p-4 flex justify-center">
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<div className="text-slate-500">Loading PDF...</div>}
          error={<div className="text-red-500">Failed to load PDF</div>}
        >
          <div className="relative shadow-lg">
            <Page
              pageNumber={pageNumber}
              scale={scale}
              onLoadSuccess={onPageLoadSuccess}
              renderTextLayer={true}
              renderAnnotationLayer={true}
            />
            {highlightStyle && <div style={highlightStyle} />}
          </div>
        </Document>
      </div>
    </div>
  );
}

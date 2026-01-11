import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import Box from '@cloudscape-design/components/box';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import type { SearchResult, Coordinates } from '../types';

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
  pdfUrl: string;
  selectedResult: SearchResult | null;
}

export function PDFViewer({ pdfUrl, selectedResult }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1);
  const [pageDimensions, setPageDimensions] = useState<{
    width: number;
    height: number;
  } | null>(null);

  useEffect(() => {
    if (selectedResult?.page) {
      setPageNumber(selectedResult.page);
    }
  }, [selectedResult]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const onPageLoadSuccess = ({
    width,
    height,
  }: {
    width: number;
    height: number;
  }) => {
    setPageDimensions({ width, height });
  };

  const getHighlightStyle = (): React.CSSProperties | null => {
    if (!selectedResult?.coordinates || !pageDimensions) return null;

    try {
      const coords: Coordinates = JSON.parse(selectedResult.coordinates);
      const points = coords.points;

      const scaleX = pageDimensions.width / coords.layout_width;
      const scaleY = pageDimensions.height / coords.layout_height;

      const minX = Math.min(...points.map((p) => p[0])) * scaleX;
      const minY = Math.min(...points.map((p) => p[1])) * scaleY;
      const maxX = Math.max(...points.map((p) => p[0])) * scaleX;
      const maxY = Math.max(...points.map((p) => p[1])) * scaleY;

      return {
        position: 'absolute',
        left: `${minX}px`,
        top: `${minY}px`,
        width: `${maxX - minX}px`,
        height: `${maxY - minY}px`,
        backgroundColor: 'rgba(255, 153, 0, 0.25)',
        border: '3px solid #ff9900',
        borderRadius: '4px',
        pointerEvents: 'none',
        boxShadow: '0 0 12px rgba(255, 153, 0, 0.4)',
      };
    } catch {
      return null;
    }
  };

  const highlightStyle =
    selectedResult?.page === pageNumber ? getHighlightStyle() : null;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#232f3e',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '8px 16px',
          backgroundColor: '#232f3e',
          borderBottom: '1px solid #3a4553',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <SpaceBetween size="xs" direction="horizontal" alignItems="center">
          <Button
            iconName="angle-left"
            variant="icon"
            onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
            disabled={pageNumber <= 1}
          />
          <Box variant="span" color="text-status-inactive">
            Page {pageNumber} of {numPages}
          </Box>
          <Button
            iconName="angle-right"
            variant="icon"
            onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))}
            disabled={pageNumber >= numPages}
          />
        </SpaceBetween>

        <SpaceBetween size="xs" direction="horizontal" alignItems="center">
          <Button
            iconName="zoom-out"
            variant="icon"
            onClick={() => setScale((s) => Math.max(0.5, s - 0.1))}
          />
          <Box variant="span" color="text-status-inactive" fontSize="body-s">
            {Math.round(scale * 100)}%
          </Box>
          <Button
            iconName="zoom-in"
            variant="icon"
            onClick={() => setScale((s) => Math.min(2, s + 0.1))}
          />
        </SpaceBetween>
      </div>

      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          backgroundColor: '#394150',
        }}
      >
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <Box textAlign="center" padding="l" color="text-status-inactive">
              Loading PDF...
            </Box>
          }
          error={
            <Box textAlign="center" padding="l" color="text-status-error">
              Failed to load PDF
            </Box>
          }
        >
          <div
            style={{
              position: 'relative',
              boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
              borderRadius: '4px',
              overflow: 'hidden',
            }}
          >
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

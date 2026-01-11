# MediShield Life Document Search

A semantic search interface for MediShield Life policy documents.

## Development

```bash
npm install
npm run dev
```

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=https://your-api-gateway-url.amazonaws.com
VITE_PDF_URL=./medishield.pdf
```

## Deployment

The app deploys automatically to GitHub Pages on push to `main`.

### GitHub Repository Settings

1. Go to Settings → Pages → Source: GitHub Actions
2. Go to Settings → Variables → Actions → New repository variable:
   - `VITE_API_URL`: Your API Gateway URL
   - `VITE_PDF_URL`: (optional) URL to PDF file, defaults to `./medishield.pdf`

## Features

- Semantic search powered by Gemini embeddings
- PDF viewer with coordinate-based highlighting
- Relevance scoring for search results
- Responsive design

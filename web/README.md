# RSS Feed Manager - Web Interface

A modern web interface for managing and searching RSS feeds with semantic search capabilities.

## Features

- Add and manage RSS feed sources
- Semantic search across all your feeds
- Filter search results by source
- Clean, responsive UI built with Next.js and Tailwind CSS

## Prerequisites

- Node.js 18 or later
- npm or yarn
- Backend server running (see the server README for setup)

## Getting Started

1. Install dependencies:

```bash
npm install
# or
yarn install
```

2. Create a `.env.local` file in the root directory and add your backend URL:

```bash
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1' > .env.local
```

Or create it manually with the following content:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

3. Start the development server:

```bash
npm run dev
# or
yarn dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

- `/app` - Next.js app router pages and layouts
- `/components` - Reusable UI components
- `/lib` - API client and utilities
- `/public` - Static files

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Dependencies

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- @tanstack/react-query - Data fetching and caching
- axios - HTTP client
- @heroicons/react - Icons

## License

MIT

## Packages
recharts | For analytics charts (fake vs real distribution)
framer-motion | For smooth page transitions, progress bars, and result reveals
lucide-react | Icons (already in base, but emphasizing use)
react-dropzone | For handling image uploads elegantly
clsx | Utility for conditional class names
tailwind-merge | Utility for merging tailwind classes

## Notes
Tailwind Config - extend fontFamily:
fontFamily: {
  display: ["var(--font-display)"],
  body: ["var(--font-body)"],
}
Authentication uses Replit Auth (useAuth hook).
API routes defined in shared/routes.ts should be used for data fetching.

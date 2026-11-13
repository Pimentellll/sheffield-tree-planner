import type { ReactNode } from 'react'

const Svg = ({ children, size = 20 }: { children: ReactNode; size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
)
export const IconMap = () => <Svg><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Z" /><path d="M9 4v14M15 6v14" /></Svg>
export const IconSliders = () => <Svg><path d="M4 7h10M18 7h2M4 12h4M12 12h8M4 17h12" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="12" r="2" /><circle cx="18" cy="17" r="2" /></Svg>
export const IconCompare = () => <Svg><rect x="3" y="4" width="8" height="16" rx="1.5" /><rect x="13" y="4" width="8" height="16" rx="1.5" /></Svg>
export const IconReport = () => <Svg><path d="M6 3h8l4 4v14H6V3Z" /><path d="M14 3v4h4M9 13h6M9 17h6" /></Svg>
export const IconDownload = () => <Svg size={16}><path d="M12 4v11m-4-4 4 4 4-4M5 20h14" /></Svg>
export const IconRefresh = () => <Svg size={18}><path d="M4 12a8 8 0 0 1 14-5.3L20 9M20 4v5h-5M20 12a8 8 0 0 1-14 5.3L4 15M4 20v-5h5" /></Svg>
export const IconCheck = () => <Svg size={16}><path d="m5 12 5 5 9-10" /></Svg>
export const IconAlert = () => <Svg size={16}><path d="M12 4 3 20h18L12 4Z" /><path d="M12 10v4M12 17h0" /></Svg>
export const IconChat = () => <Svg size={16}><path d="M4 5h16v11H9l-5 4V5Z" /></Svg>
export const IconArrow = () => <Svg size={16}><path d="M5 12h14m-5-5 5 5-5 5" /></Svg>
export const IconLock = () => <Svg size={12}><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></Svg>
export const IconTree = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="9" cy="9" r="5" /><circle cx="15" cy="10" r="4" /><path d="M12 13v8M9 21h6" /></svg>
)

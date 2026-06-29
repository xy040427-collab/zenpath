USE search_replace tool to make ONE targeted edit to this EXISTING file:

FILE TO EDIT: /home/xiaoyu/projects/gaokao-volunteer/frontend/src/components/layout/Navbar.tsx

EDIT 1 — Add isChat detection (after line 12, after "const isHome = ..."):
  ADD: const isChat = location.pathname === '/chat';

EDIT 2 — Modify the nav className (around line 31-35). Change:
  className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
    isScrolled
      ? 'bg-white/80 backdrop-blur-xl border-b border-[#E0D8CC]/30 shadow-[0_1px_8px_rgba(26,46,34,0.04)]'
      : 'bg-transparent border-b border-transparent'
  }`}

  TO:
  className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
    isChat
      ? 'bg-white/95 backdrop-blur-xl border-b border-[#E0D8CC]'
      : isScrolled
      ? 'bg-white/80 backdrop-blur-xl border-b border-[#E0D8CC]/30 shadow-[0_1px_8px_rgba(26,46,34,0.04)]'
      : 'bg-transparent border-b border-transparent'
  }`}

DO NOT write a new file. Use search_replace on the EXISTING file. DO NOT read or explore other files. Apply ONLY these 2 edits and stop.
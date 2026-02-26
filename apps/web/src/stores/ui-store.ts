import { create } from "zustand";

interface ProjectSidebarStore {
  collapsed: boolean;
  toggle: () => void;
  setCollapsed: (collapsed: boolean) => void;
}

export const useProjectSidebarStore = create<ProjectSidebarStore>((set) => ({
  collapsed: false,
  toggle: () => set((state) => ({ collapsed: !state.collapsed })),
  setCollapsed: (collapsed) => set({ collapsed }),
}));

interface MobileMenuStore {
  open: boolean;
  setOpen: (open: boolean) => void;
  toggle: () => void;
}

export const useMobileMenuStore = create<MobileMenuStore>((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
  toggle: () => set((state) => ({ open: !state.open })),
}));

interface MobileMoreSheetStore {
  open: boolean;
  setOpen: (open: boolean) => void;
}

export const useMobileMoreSheetStore = create<MobileMoreSheetStore>((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
}));

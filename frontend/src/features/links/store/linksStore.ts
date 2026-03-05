import { create } from "zustand";
import type { ShortURL, CreateLinkPayload, PaginatedResponse } from "@/types";
import { getLinksApi, createLinkApi, deleteLinkApi } from "../api/linksApi";

interface LinksState {
  links: ShortURL[];
  pagination: PaginatedResponse<ShortURL>["pagination"] | null;
  isLoading: boolean;
  fetchLinks: (page?: number) => Promise<void>;
  createLink: (payload: CreateLinkPayload) => Promise<ShortURL>;
  deleteLink: (linkId: string) => Promise<void>;
}

export const useLinksStore = create<LinksState>((set) => ({
  links: [],
  pagination: null,
  isLoading: false,

  fetchLinks: async (page = 1) => {
    set({ isLoading: true });
    try {
      const data = await getLinksApi(page);
      set({ links: data.results, pagination: data.pagination });
    } finally {
      set({ isLoading: false });
    }
  },

  createLink: async (payload) => {
    const link = await createLinkApi(payload);
    set((state) => ({ links: [link, ...state.links] }));
    return link;
  },

  deleteLink: async (linkId) => {
    await deleteLinkApi(linkId);
    set((state) => ({ links: state.links.filter((l) => l.id !== linkId) }));
  },
}));

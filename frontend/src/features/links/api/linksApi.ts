import apiClient from "@/api/client";
import type {
  CreateLinkPayload,
  LinkAnalytics,
  LinkStats,
  PaginatedResponse,
  ShortURL,
} from "@/types";

export interface LinksListResponse extends PaginatedResponse<ShortURL> {
  stats: LinkStats;
}

export async function getLinksApi(page = 1, pageSize = 20): Promise<LinksListResponse> {
  const { data } = await apiClient.get("/links/", { params: { page, page_size: pageSize } });
  return data;
}

export async function createLinkApi(payload: CreateLinkPayload): Promise<ShortURL> {
  const { data } = await apiClient.post("/links/", payload);
  return data;
}

export async function deleteLinkApi(linkId: string): Promise<void> {
  await apiClient.delete(`/links/${linkId}/`);
}

export async function getLinkAnalyticsApi(linkId: string, days = 30): Promise<LinkAnalytics> {
  const { data } = await apiClient.get(`/links/${linkId}/analytics/`, { params: { days } });
  return data;
}

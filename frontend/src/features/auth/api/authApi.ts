import apiClient from "@/api/client";
import type { AuthTokens, LoginPayload, RegisterPayload, User } from "@/types";

export async function loginApi(
  payload: LoginPayload
): Promise<{ access: string; refresh: string; user: User }> {
  const { data } = await apiClient.post("/auth/login/", payload);
  return data;
}

export async function registerApi(
  payload: RegisterPayload
): Promise<{ tokens: AuthTokens; user: User }> {
  const { data } = await apiClient.post("/auth/register/", payload);
  return data;
}

export async function logoutApi(refresh: string): Promise<void> {
  await apiClient.post("/auth/logout/", { refresh });
}

export async function getMeApi(): Promise<User> {
  const { data } = await apiClient.get("/users/me/");
  return data;
}

const DEFAULT_USER_ID = "u1";

export function resolveUserId(search: string): string {
  const value = new URLSearchParams(search).get("userId")?.trim();
  return value ? value : DEFAULT_USER_ID;
}

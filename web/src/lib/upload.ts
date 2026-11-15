import { api, type Schemas, unwrap } from "@/api/client";

export type MediaKind = Schemas["UploadRequest"]["kind"];
export type UploadScope = "admin" | "me";

export function kindOf(file: File): MediaKind | null {
  if (file.type.startsWith("image/")) return "image";
  if (file.type.startsWith("audio/")) return "audio";
  if (file.type.startsWith("video/")) return "video";
  return null;
}

export async function uploadFile(
  file: File,
  scope: UploadScope,
  isPublic = false,
): Promise<Schemas["MediaAssetOut"]> {
  const kind = kindOf(file);
  if (!kind) throw new Error(`Unsupported file type: ${file.type}`);
  const body = { kind, contentType: file.type, sizeBytes: file.size, filename: file.name, isPublic };
  const ticket =
    scope === "admin"
      ? await unwrap(api.POST("/api/admin/media/uploads", { body }))
      : await unwrap(api.POST("/api/me/media/uploads", { body }));
  const put = await fetch(ticket.uploadUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type },
  });
  if (!put.ok) throw new Error(`Upload failed with ${put.status}`);
  const path = { params: { path: { asset_id: ticket.asset.id } } };
  return scope === "admin"
    ? unwrap(api.POST("/api/admin/media/{asset_id}/complete", path))
    : unwrap(api.POST("/api/me/media/{asset_id}/complete", path));
}

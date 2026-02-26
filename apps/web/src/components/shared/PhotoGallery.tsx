"use client";

import { Camera } from "lucide-react";

interface PhotoGalleryProps {
  photos: Array<{
    id: string;
    caption?: string | null;
    location?: string | null;
    created_at: string;
    file_id?: string | null;
  }>;
  onPhotoClick?: (photoId: string) => void;
}

export function PhotoGallery({ photos, onPhotoClick }: PhotoGalleryProps) {
  if (photos.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <Camera className="h-8 w-8 mx-auto mb-2" />
        <p className="text-sm">No photos yet</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
      {photos.map((photo) => (
        <div
          key={photo.id}
          onClick={() => onPhotoClick?.(photo.id)}
          className="aspect-square rounded-lg border bg-gray-100 overflow-hidden cursor-pointer hover:ring-2 hover:ring-[#2E75B6] transition-all group relative"
        >
          <div className="w-full h-full flex items-center justify-center bg-gray-200">
            <Camera className="h-8 w-8 text-gray-400" />
          </div>
          {photo.caption && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <p className="text-white text-xs truncate">{photo.caption}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

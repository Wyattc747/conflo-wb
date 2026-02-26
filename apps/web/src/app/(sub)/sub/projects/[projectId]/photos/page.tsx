"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Camera, MapPin } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { FilterBar } from "@/components/shared/FilterBar";
import { PhotoGallery } from "@/components/shared/PhotoGallery";
import type { Photo } from "@/types/photo";

const MOCK_PHOTOS: Photo[] = [
  {
    id: "1",
    project_id: "p1",
    file_id: "file1",
    caption: "Foundation excavation complete - Grid A",
    tags: ["foundation"],
    location: "Grid A-C, Level 0",
    uploaded_by_name: "John Smith",
    created_at: "2026-02-15T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    file_id: "file2",
    caption: "Steel erection in progress - Level 3",
    tags: ["steel"],
    location: "Level 3",
    uploaded_by_name: "Mike Chen",
    created_at: "2026-02-22T11:30:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    file_id: "file3",
    caption: "Site overview",
    tags: ["aerial"],
    location: "Site overview",
    uploaded_by_name: "John Smith",
    created_at: "2026-02-24T08:30:00Z",
  },
];

export default function SubPhotosPage() {
  const params = useParams();
  const [search, setSearch] = useState("");

  let filtered = MOCK_PHOTOS;
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        (p.caption && p.caption.toLowerCase().includes(s)) ||
        (p.location && p.location.toLowerCase().includes(s))
    );
  }

  const hasData = MOCK_PHOTOS.length > 0;

  return (
    <div>
      <PageHeader title="Photos" subtitle="View project photos" />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search photos..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[]}
          />
          <div className="mb-4">
            <span className="text-sm text-gray-500">{filtered.length} photos</span>
          </div>
          <PhotoGallery
            photos={filtered}
            onPhotoClick={(photoId) => console.log("open lightbox", photoId)}
          />
        </>
      ) : (
        <EmptyState
          icon={Camera}
          title="No photos yet"
          description="Project photos will appear here."
        />
      )}
    </div>
  );
}

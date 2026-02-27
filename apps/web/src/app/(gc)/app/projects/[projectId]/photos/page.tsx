"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Plus, Camera, MapPin } from "lucide-react";
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
    linked_type: "DAILY_LOG",
    linked_id: "dl1",
    caption: "Foundation excavation complete - Grid A",
    tags: ["foundation", "excavation"],
    location: "Grid A-C, Level 0",
    latitude: 39.7392,
    longitude: -104.9903,
    uploaded_by_name: "John Smith",
    captured_at: "2026-02-15T09:30:00Z",
    created_at: "2026-02-15T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    file_id: "file2",
    linked_type: "DAILY_LOG",
    linked_id: "dl1",
    caption: "Rebar placement for footings",
    tags: ["rebar", "foundation"],
    location: "Grid A-C, Level 0",
    uploaded_by_name: "John Smith",
    captured_at: "2026-02-15T10:15:00Z",
    created_at: "2026-02-15T10:30:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    file_id: "file3",
    linked_type: "PUNCH_LIST",
    linked_id: "pl1",
    caption: "Drywall damage - Stairwell B, 2nd floor",
    tags: ["punch", "drywall"],
    location: "Stairwell B, Level 2",
    uploaded_by_name: "Sarah Johnson",
    captured_at: "2026-02-20T14:00:00Z",
    created_at: "2026-02-20T14:15:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    file_id: "file4",
    caption: "Steel erection in progress - Level 3",
    tags: ["steel", "erection"],
    location: "Level 3",
    uploaded_by_name: "Mike Chen",
    captured_at: "2026-02-22T11:00:00Z",
    created_at: "2026-02-22T11:30:00Z",
  },
  {
    id: "5",
    project_id: "p1",
    file_id: "file5",
    linked_type: "INSPECTION",
    linked_id: "insp1",
    caption: "Fire stopping inspection - Room 204",
    tags: ["inspection", "fire"],
    location: "Room 204, Level 2",
    uploaded_by_name: "Jane Doe",
    captured_at: "2026-02-23T15:00:00Z",
    created_at: "2026-02-23T15:20:00Z",
  },
  {
    id: "6",
    project_id: "p1",
    file_id: "file6",
    caption: "Site overview - aerial drone shot",
    tags: ["aerial", "overview"],
    location: "Site overview",
    uploaded_by_name: "John Smith",
    captured_at: "2026-02-24T08:00:00Z",
    created_at: "2026-02-24T08:30:00Z",
  },
];

export default function PhotosPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [linkedTypeFilter, setLinkedTypeFilter] = useState("");

  let filtered = MOCK_PHOTOS;
  if (linkedTypeFilter) filtered = filtered.filter((p) => p.linked_type === linkedTypeFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        (p.caption && p.caption.toLowerCase().includes(s)) ||
        (p.location && p.location.toLowerCase().includes(s)) ||
        p.tags.some((t) => t.toLowerCase().includes(s))
    );
  }

  const hasData = MOCK_PHOTOS.length > 0;

  return (
    <div>
      <PageHeader
        title="Photos"
        subtitle="Browse and manage project photos"
        action={
          <button
            onClick={() => console.log("upload photo")}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2 w-full sm:w-auto justify-center"
          >
            <Plus className="h-4 w-4" />
            Upload Photos
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search photos..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "linked_type",
                label: "All Sources",
                value: linkedTypeFilter,
                onChange: setLinkedTypeFilter,
                options: [
                  { label: "Daily Log", value: "DAILY_LOG" },
                  { label: "Punch List", value: "PUNCH_LIST" },
                  { label: "Inspection", value: "INSPECTION" },
                  { label: "Unlinked", value: "" },
                ],
              },
            ]}
          />

          {/* Photo count and date info */}
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-500">{filtered.length} photos</span>
          </div>

          <PhotoGallery
            photos={filtered}
            onPhotoClick={(photoId) => console.log("open lightbox", photoId)}
          />

          {/* Photo details list below gallery */}
          <div className="mt-6 space-y-2">
            {filtered.map((photo) => (
              <div key={photo.id} className="flex items-center gap-3 sm:gap-4 p-3 bg-white rounded-lg border border-gray-200 hover:bg-gray-50">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded bg-gray-200 flex items-center justify-center flex-shrink-0">
                  <Camera className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs sm:text-sm font-medium truncate">{photo.caption || "Untitled"}</p>
                  <div className="flex items-center gap-2 sm:gap-3 mt-0.5">
                    {photo.location && (
                      <span className="text-[10px] sm:text-xs text-gray-500 flex items-center gap-0.5 truncate">
                        <MapPin className="h-3 w-3 flex-shrink-0" />{photo.location}
                      </span>
                    )}
                    <span className="text-[10px] sm:text-xs text-gray-400 flex-shrink-0">
                      {new Date(photo.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="hidden sm:flex items-center gap-1">
                  {photo.tags.slice(0, 2).map((tag) => (
                    <span key={tag} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px]">
                      {tag}
                    </span>
                  ))}
                </div>
                <span className="hidden md:inline text-xs text-gray-400">{photo.uploaded_by_name}</span>
              </div>
            ))}
          </div>
        </>
      ) : (
        <EmptyState
          icon={Camera}
          title="No photos yet"
          description="Upload your first photo to start documenting project progress."
          actionLabel="Upload Photos"
          onAction={() => console.log("upload")}
        />
      )}
    </div>
  );
}

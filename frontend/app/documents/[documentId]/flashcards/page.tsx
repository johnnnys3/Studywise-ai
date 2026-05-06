"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/common/AppShell";
import { PageHeader } from "@/components/common/PageHeader";
import { api } from "@/lib/api";
import type { Flashcard } from "@/types";

export default function FlashcardsPage() {
  const params = useParams<{ documentId: string }>();
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [flipped, setFlipped] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    api.flashcards(params.documentId)
      .then((existing) => existing.length ? setCards(existing) : api.createFlashcards(params.documentId).then(setCards))
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load flashcards."));
  }, [params.documentId]);

  return (
    <AppShell title="Flashcards">
      <PageHeader eyebrow="Review" title="Generated flashcards" description="Review key ideas from processed chunks. Spaced repetition is planned after the MVP." />
      {error ? <p className="mb-6 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {cards.map((card) => (
          <button key={card.id} onClick={() => setFlipped((current) => ({ ...current, [card.id]: !current[card.id] }))} className="min-h-48 rounded-lg border border-study-line bg-white p-5 text-left hover:shadow-academic sm:min-h-56 sm:p-6">
            <p className="text-xs font-semibold uppercase text-study-accent">Page {card.source_page}</p>
            <p className="reading-copy mt-4 break-words text-base text-study-navy sm:text-lg">{flipped[card.id] ? card.back : card.front}</p>
            <p className="mt-5 text-xs text-slate-500">Click to flip</p>
          </button>
        ))}
      </div>
    </AppShell>
  );
}

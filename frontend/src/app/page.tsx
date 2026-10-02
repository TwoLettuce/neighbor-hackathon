"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

type EventResult = {
  id: number;
  title: string;
  start_time: string;
  format: string;
  venue: string;
  city: string;
  state: string;
  organizer_name: string;
  career_fields: string[];
  distance_miles: number | null;
  match_score: number;
  match_explanation: string;
  source_url: string;
};

const formatOptions = [
  { value: "IN_PERSON", label: "In person" },
  { value: "HYBRID", label: "Hybrid" },
  { value: "LIVE_VIRTUAL", label: "Live virtual networking" },
];

const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

function Icon({ name }: { name: "pin" | "calendar" | "arrow" | "people" }) {
  const paths = {
    pin: (
      <>
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </>
    ),
    calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M16 3v4M8 3v4M3 10h18" />
      </>
    ),
    arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
    people: (
      <>
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
      </>
    ),
  };
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="size-4"
    >
      {paths[name]}
    </svg>
  );
}

function pretty(value: string) {
  return value
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function Home() {
  const [career, setCareer] = useState("Software Engineer");
  const [location, setLocation] = useState("Provo, UT");
  const [radius, setRadius] = useState("50");
  const [formats, setFormats] = useState([
    "IN_PERSON",
    "HYBRID",
    "LIVE_VIRTUAL",
  ]);
  const [events, setEvents] = useState<EventResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function search(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!career.trim() || !location.trim() || formats.length === 0) {
      setError("Enter a career and location, and select at least one format.");
      return;
    }
    setLoading(true);
    const params = new URLSearchParams({
      career,
      location,
      radius_miles: radius,
    });
    formats.forEach((format) => params.append("formats", format));
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/events/search/?${params}`,
      );
      const payload = await response.json();
      if (!response.ok) {
        const message = Object.values(payload).flat().join(" ");
        throw new Error(message || "Search failed. Please check your entries.");
      }
      setEvents(payload.events);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to reach the search service.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-white/10 bg-ink text-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 md:px-8">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-xl bg-coral font-serif text-xl font-bold">
              N
            </span>
            <span className="font-serif text-xl font-semibold tracking-tight">
              Job&Weave
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-white/60 md:block">
              Career connections, closer to home.
            </span>
            <Link
              href="/events/new"
              className="rounded-lg border border-white/20 px-4 py-2 text-sm font-bold transition hover:border-mint/60 hover:text-mint"
            >
              Add event
            </Link>
          </div>
        </nav>
        <div className="mx-auto max-w-6xl px-5 pb-16 pt-12 md:px-8 md:pb-24 md:pt-20">
          <p className="mb-4 text-xs font-semibold uppercase tracking-[0.24em] text-mint">
            Discover your professional community
          </p>
          <h1 className="max-w-3xl font-serif text-4xl leading-[1.08] tracking-tight sm:text-6xl">
            The right room can change your career.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-white/70">
            Find nearby events where you can meet the people doing the work you
            want to do—not just watch another webinar.
          </p>
        </div>
      </header>

      <section className="mx-auto -mt-8 max-w-6xl px-5 md:-mt-10 md:px-8">
        <form
          onSubmit={search}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_22px_70px_rgba(17,31,38,0.12)] md:p-7"
        >
          <div className="grid gap-5 md:grid-cols-[1.2fr_1fr_0.55fr]">
            <label className="field-label">
              Career or keywords
              <input
                value={career}
                onChange={(event) => setCareer(event.target.value)}
                placeholder="e.g. Software Engineer, Rust, hackathon"
                className="field-input"
              />
            </label>
            <label className="field-label">
              Location
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                  <Icon name="pin" />
                </span>
                <input
                  value={location}
                  onChange={(event) => setLocation(event.target.value)}
                  placeholder="City, State"
                  className="field-input pl-10"
                />
              </div>
            </label>
            <label className="field-label">
              Radius
              <select
                value={radius}
                onChange={(event) => setRadius(event.target.value)}
                className="field-input appearance-none"
              >
                {[10, 25, 50, 100].map((miles) => (
                  <option key={miles} value={miles}>
                    {miles} miles
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="mt-6 flex flex-col gap-5 border-t border-slate-100 pt-5 md:flex-row md:items-end md:justify-between">
            <fieldset>
              <legend className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">
                Event formats
              </legend>
              <div className="flex flex-wrap gap-2">
                {formatOptions.map((option) => {
                  const checked = formats.includes(option.value);
                  return (
                    <label
                      key={option.value}
                      className={`cursor-pointer rounded-full border px-3.5 py-2 text-sm font-medium transition ${
                        checked
                          ? "border-teal bg-teal/8 text-teal"
                          : "border-slate-200 text-slate-500 hover:border-slate-300"
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="sr-only"
                        checked={checked}
                        onChange={() =>
                          setFormats(
                            checked
                              ? formats.filter((item) => item !== option.value)
                              : [...formats, option.value],
                          )
                        }
                      />
                      <span className="mr-2">{checked ? "✓" : "+"}</span>
                      {option.label}
                    </label>
                  );
                })}
              </div>
            </fieldset>
            <button
              disabled={loading}
              className="flex min-h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-coral px-7 font-bold text-white shadow-lg shadow-coral/20 transition hover:-translate-y-0.5 hover:bg-[#d7563e] disabled:cursor-wait disabled:opacity-60"
            >
              {loading ? "Searching…" : "Find events"}{" "}
              {!loading && <Icon name="arrow" />}
            </button>
          </div>
          {error && (
            <p
              role="alert"
              className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </p>
          )}
        </form>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-14 md:px-8 md:py-20">
        <div className="mb-7 flex items-end justify-between">
          <div>
            <p className="eyebrow">Curated for connection</p>
            <h2 className="font-serif text-3xl text-ink">
              {events
                ? `${events.length} events worth your time`
                : "Meet your next opportunity"}
            </h2>
          </div>
          {events && (
            <span className="hidden text-sm text-slate-500 sm:block">
              Ranked by career fit & networking potential
            </span>
          )}
        </div>

        {loading && (
          <div className="grid gap-5 md:grid-cols-2">
            {[1, 2, 3, 4].map((item) => (
              <div
                key={item}
                className="h-72 animate-pulse rounded-2xl border border-slate-200 bg-white"
              />
            ))}
          </div>
        )}
        {!loading && events?.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
            <h3 className="font-serif text-2xl text-ink">
              No strong matches yet
            </h3>
            <p className="mt-2 text-slate-500">
              Try broader keywords, a larger radius, or another event format.
            </p>
          </div>
        )}
        {!loading && events === null && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
            <span className="mx-auto mb-4 grid size-12 place-items-center rounded-full bg-mint/20 text-teal">
              <Icon name="people" />
            </span>
            <h3 className="font-serif text-2xl text-ink">
              Search beyond the job board
            </h3>
            <p className="mx-auto mt-2 max-w-lg text-slate-500">
              We evaluate topic fit and real opportunities to interact, so
              developer meetups can surface even without your exact job title.
            </p>
          </div>
        )}
        {!loading && events && events.length > 0 && (
          <div className="grid gap-5 md:grid-cols-2">
            {events.map((item) => (
              <article
                key={item.id}
                className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:border-teal/30 hover:shadow-xl hover:shadow-slate-200/60"
              >
                <div className="flex items-start justify-between gap-5">
                  <div>
                    <div className="mb-3 flex flex-wrap gap-2">
                      <span className="tag bg-mint/20 text-teal">
                        {pretty(item.format)}
                      </span>
                      {item.career_fields.slice(0, 2).map((field) => (
                        <span
                          key={field}
                          className="tag bg-slate-100 text-slate-600"
                        >
                          {pretty(field)}
                        </span>
                      ))}
                    </div>
                    <h3 className="font-serif text-2xl leading-tight text-ink">
                      {item.title}
                    </h3>
                  </div>
                  <div className="shrink-0 text-right">
                    <span className="font-serif text-2xl font-bold text-coral">
                      {Math.round(item.match_score * 100)}
                    </span>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Match
                    </p>
                  </div>
                </div>
                <div className="mt-5 space-y-2 text-sm text-slate-600">
                  <p className="flex items-center gap-2">
                    <Icon name="calendar" />
                    {new Intl.DateTimeFormat("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    }).format(new Date(item.start_time))}
                  </p>
                  <p className="flex items-center gap-2">
                    <Icon name="pin" />
                    {item.format === "LIVE_VIRTUAL"
                      ? "Online"
                      : `${item.venue} · ${item.city}, ${item.state}`}
                    {item.distance_miles !== null &&
                      ` · ${item.distance_miles} mi`}
                  </p>
                </div>
                <p className="mt-5 border-l-2 border-mint pl-4 text-sm leading-6 text-slate-600">
                  {item.match_explanation}
                </p>
                <div className="mt-auto flex items-end justify-between gap-4 pt-6">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-400">
                      Hosted by
                    </p>
                    <p className="mt-1 text-sm font-semibold text-ink">
                      {item.organizer_name}
                    </p>
                  </div>
                  {item.source_url && (
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm font-bold text-teal hover:text-coral"
                    >
                      Event details <Icon name="arrow" />
                    </a>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-8 text-sm text-slate-500 sm:flex-row sm:justify-between md:px-8">
          <p>
            Job&apos;n&apos;Weave aggregates events and sends you to the original source to
            register.
          </p>
          <p>Scores indicate relevance—not probability.</p>
        </div>
      </footer>
    </main>
  );
}

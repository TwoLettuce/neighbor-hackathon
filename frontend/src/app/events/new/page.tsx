"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

type CreatedEvent = {
  id: number;
  title: string;
  start_time: string;
  format: string;
  venue_name: string;
  city: string;
  state_region: string;
  source: string;
};

type FieldErrors = Record<string, string[] | string>;

const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

const inputClass =
  "field-input aria-invalid:border-red-400 aria-invalid:ring-2 aria-invalid:ring-red-100";

function messageFor(errors: FieldErrors, field: string) {
  const value = errors[field];
  return Array.isArray(value) ? value.join(" ") : value;
}

export default function NewEventPage() {
  const [format, setFormat] = useState("IN_PERSON");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [created, setCreated] = useState<CreatedEvent | null>(null);
  const needsLocation = format === "IN_PERSON" || format === "HYBRID";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors({});

    const form = new FormData(event.currentTarget);
    const startTime = String(form.get("start_time") ?? "");
    const endTime = String(form.get("end_time") ?? "");
    if (endTime && new Date(endTime) < new Date(startTime)) {
      setErrors({ end_time: "End time cannot be before start time." });
      return;
    }

    const optionalFields = [
      "description",
      "end_time",
      "organizer_name",
      "organizer_url",
      "venue_name",
      "address",
      "city",
      "state_region",
      "event_url",
    ];
    const payload: Record<string, string> = {
      title: String(form.get("title") ?? "").trim(),
      start_time: startTime,
      format,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      country: "US",
    };
    optionalFields.forEach((field) => {
      const value = String(form.get(field) ?? "").trim();
      if (value) payload[field] = value;
    });

    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/events/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const responsePayload = await response.json();
      if (!response.ok) {
        setErrors(responsePayload);
        return;
      }
      setCreated(responsePayload);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      setErrors({
        non_field_errors:
          "Unable to reach the event service. Check your connection and try again.",
      });
    } finally {
      setLoading(false);
    }
  }

  if (created) {
    return (
      <main className="grid min-h-screen place-items-center px-5 py-12">
        <section className="w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-xl shadow-slate-200/60 md:p-12">
          <span className="mx-auto grid size-14 place-items-center rounded-full bg-mint/25 text-2xl font-bold text-teal">
            ✓
          </span>
          <p className="eyebrow mt-6">Published to the community</p>
          <h1 className="font-serif text-4xl text-ink">{created.title}</h1>
          <p className="mx-auto mt-4 max-w-lg leading-7 text-slate-600">
            Your event is approved and stored as a community submission. It can
            now appear in the same ranked searches as other events.
          </p>
          <div className="mt-7 rounded-2xl bg-background p-5 text-left text-sm text-slate-600">
            <p className="font-semibold text-ink">
              {new Intl.DateTimeFormat("en-US", {
                dateStyle: "full",
                timeStyle: "short",
              }).format(new Date(created.start_time))}
            </p>
            <p className="mt-1">
              {created.format === "LIVE_VIRTUAL"
                ? "Online"
                : [created.venue_name, created.city, created.state_region]
                    .filter(Boolean)
                    .join(" · ")}
            </p>
          </div>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Link
              href="/"
              className="rounded-xl bg-coral px-6 py-3 font-bold text-white transition hover:bg-[#d7563e]"
            >
              Discover events
            </Link>
            <button
              type="button"
              onClick={() => setCreated(null)}
              className="rounded-xl border border-slate-200 px-6 py-3 font-bold text-teal transition hover:border-teal/30"
            >
              Add another event
            </button>
          </div>
        </section>
      </main>
    );
  }

  const generalError =
    messageFor(errors, "non_field_errors") || messageFor(errors, "detail");

  return (
    <main className="min-h-screen">
      <header className="border-b border-white/10 bg-ink text-white">
        <nav className="mx-auto flex max-w-4xl items-center justify-between px-5 py-5 md:px-8">
          <Link href="/" className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-xl bg-coral font-serif text-xl font-bold">
              N
            </span>
            <span className="font-serif text-xl font-semibold tracking-tight">
              Job&Weave
            </span>
          </Link>
          <Link href="/" className="text-sm font-semibold text-white/70 hover:text-white">
            ← Back to discovery
          </Link>
        </nav>
        <div className="mx-auto max-w-4xl px-5 pb-14 pt-8 md:px-8 md:pb-16">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-mint">
            Share an opportunity
          </p>
          <h1 className="font-serif text-4xl tracking-tight sm:text-5xl">
            Add a community event
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-white/70">
            Help local professionals find the rooms where real connections happen.
          </p>
        </div>
      </header>

      <section className="mx-auto -mt-6 max-w-4xl px-5 pb-20 md:px-8">
        <form
          onSubmit={submit}
          className="space-y-9 rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_22px_70px_rgba(17,31,38,0.12)] md:p-9"
        >
          {generalError && (
            <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
              {generalError}
            </p>
          )}

          <fieldset className="space-y-5">
            <legend className="font-serif text-2xl text-ink">Event details</legend>
            <div className="grid gap-5 md:grid-cols-2">
              <Field label="Event title" required error={messageFor(errors, "title")} wide>
                <input name="title" required maxLength={300} className={inputClass} />
              </Field>
              <Field label="Format" required error={messageFor(errors, "format")}>
                <select
                  name="format"
                  value={format}
                  onChange={(event) => setFormat(event.target.value)}
                  className={inputClass}
                >
                  <option value="IN_PERSON">In person</option>
                  <option value="HYBRID">Hybrid</option>
                  <option value="LIVE_VIRTUAL">Live virtual</option>
                  <option value="WEBINAR">Webinar</option>
                  <option value="OTHER">Other</option>
                </select>
              </Field>
              <Field
                label="Description"
                error={messageFor(errors, "description")}
                wide
                hint="Include the topics, audience, and opportunities to connect."
              >
                <textarea
                  name="description"
                  rows={5}
                  className={`${inputClass} min-h-32 py-3`}
                />
              </Field>
              <Field label="Starts" required error={messageFor(errors, "start_time")}>
                <input
                  name="start_time"
                  type="datetime-local"
                  required
                  className={inputClass}
                />
              </Field>
              <Field label="Ends" error={messageFor(errors, "end_time")}>
                <input name="end_time" type="datetime-local" className={inputClass} />
              </Field>
            </div>
          </fieldset>

          <fieldset className="space-y-5 border-t border-slate-100 pt-8">
            <legend className="font-serif text-2xl text-ink">Location</legend>
            <div className="grid gap-5 md:grid-cols-2">
              <Field
                label="Venue name"
                required={needsLocation}
                error={messageFor(errors, "venue_name")}
              >
                <input
                  name="venue_name"
                  required={needsLocation}
                  disabled={!needsLocation}
                  className={inputClass}
                />
              </Field>
              <Field label="Street address" error={messageFor(errors, "address")}>
                <input name="address" disabled={!needsLocation} className={inputClass} />
              </Field>
              <Field
                label="City"
                required={needsLocation}
                error={messageFor(errors, "city")}
              >
                <input
                  name="city"
                  required={needsLocation}
                  disabled={!needsLocation}
                  className={inputClass}
                />
              </Field>
              <Field
                label="State or region"
                required={needsLocation}
                error={messageFor(errors, "state_region")}
              >
                <input
                  name="state_region"
                  required={needsLocation}
                  disabled={!needsLocation}
                  className={inputClass}
                />
              </Field>
            </div>
            {needsLocation && (
              <p className="text-sm leading-6 text-slate-500">
                Known Utah cities are geocoded automatically. Other locations are
                saved without coordinates until broader geocoding is configured.
              </p>
            )}
          </fieldset>

          <fieldset className="space-y-5 border-t border-slate-100 pt-8">
            <legend className="font-serif text-2xl text-ink">Organizer & links</legend>
            <div className="grid gap-5 md:grid-cols-2">
              <Field label="Organizer or company" error={messageFor(errors, "organizer_name")}>
                <input name="organizer_name" className={inputClass} />
              </Field>
              <Field label="Organizer website" error={messageFor(errors, "organizer_url")}>
                <input
                  name="organizer_url"
                  type="url"
                  placeholder="https://"
                  className={inputClass}
                />
              </Field>
              <Field
                label="Event or registration URL"
                error={messageFor(errors, "event_url")}
                wide
              >
                <input
                  name="event_url"
                  type="url"
                  placeholder="https://"
                  className={inputClass}
                />
              </Field>
            </div>
          </fieldset>

          <div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-7 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-500">
              Community submissions are visible immediately.
            </p>
            <button
              disabled={loading}
              className="min-h-12 rounded-xl bg-coral px-8 font-bold text-white shadow-lg shadow-coral/20 transition hover:-translate-y-0.5 hover:bg-[#d7563e] disabled:cursor-wait disabled:opacity-60"
            >
              {loading ? "Publishing…" : "Publish event"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

function Field({
  label,
  required = false,
  error,
  hint,
  wide = false,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  hint?: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className={`field-label ${wide ? "md:col-span-2" : ""}`}>
      <span>
        {label}
        {required && <span className="ml-1 text-coral">*</span>}
      </span>
      {children}
      {hint && !error && (
        <span className="text-xs font-normal normal-case tracking-normal text-slate-500">
          {hint}
        </span>
      )}
      {error && (
        <span className="text-xs font-semibold normal-case tracking-normal text-red-600">
          {error}
        </span>
      )}
    </label>
  );
}

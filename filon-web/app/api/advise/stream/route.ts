import { NextRequest } from "next/server";

import { API } from "@/lib/api";

export const dynamic = "force-dynamic";

const ALLOWED_PARAMS = ["q", "budget", "country", "locale"] as const;

export async function GET(request: NextRequest) {
  const upstream = new URL("/api/advise/stream", API);
  for (const key of ALLOWED_PARAMS) {
    const value = request.nextUrl.searchParams.get(key);
    if (value !== null) upstream.searchParams.set(key, value);
  }

  try {
    const response = await fetch(upstream, {
      cache: "no-store",
      headers: { Accept: "text/event-stream" },
      signal: request.signal,
    });

    if (!response.ok || !response.body) {
      return new Response(null, { status: response.status || 502 });
    }

    return new Response(response.body, {
      status: 200,
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Content-Type": "text/event-stream; charset=utf-8",
        "X-Accel-Buffering": "no",
      },
    });
  } catch {
    return new Response(null, { status: 502 });
  }
}

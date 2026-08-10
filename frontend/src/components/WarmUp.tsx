"use client";

import { useEffect } from "react";

const HEALTH_URL = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/health`;

export default function WarmUp() {
  useEffect(() => {
    // fire-and-forget: boots a sleeping Render instance (~50s) in parallel with
    // the user reading the page, so login doesn't eat the cold start.
    fetch(HEALTH_URL, { keepalive: true }).catch(() => {});
  }, []);
  return null;
}
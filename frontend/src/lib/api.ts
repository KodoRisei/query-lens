import type { QueryReview, ReviewRequest } from "@/types/review";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.ok) return res.json() as Promise<T>;
  let code = "UNKNOWN_ERROR";
  let message = `HTTP ${res.status}`;
  try {
    const body = await res.json();
    code = body?.error?.code ?? code;
    message = body?.error?.message ?? body?.detail?.message ?? message;
  } catch {
    // non-JSON error body — keep defaults
  }
  throw new ApiError(res.status, code, message);
}

export async function createReview(req: ReviewRequest): Promise<QueryReview> {
  const res = await fetch(`${BASE_URL}/api/v1/queries/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse<QueryReview>(res);
}

export async function getReview(id: string): Promise<QueryReview> {
  const res = await fetch(`${BASE_URL}/api/v1/queries/review/${id}`);
  return handleResponse<QueryReview>(res);
}

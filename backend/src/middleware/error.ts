import { Request, Response, NextFunction } from "express";

export interface AuthenticatedRequest extends Request {
  user?: {
    id: number;
    email: string;
    role: string;
    status: string;
  };
}

export function errorHandler(
  err: any,
  _req: Request,
  res: Response,
  _next: NextFunction
): Response {
  console.error("Error:", err);

  if (err.type === "entity.parse.failed") {
    return res.status(400).json({ error: { message: "Invalid JSON body" } });
  }

  const status = err.statusCode || err.status || 500;
  const message =
    status === 500 ? "Internal server error" : err.message || "An error occurred";

  return res.status(status).json({ error: { message } });
}

export function notFoundHandler(_req: Request, res: Response): Response {
  return res.status(404).json({ error: { message: "Not found" } });
}

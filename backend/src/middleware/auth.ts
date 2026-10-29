import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { getDb } from "../database";
import { config } from "../config";

export interface AuthenticatedRequest extends Request {
  user?: {
    id: number;
    email: string;
    role: string;
    status: string;
  };
}

export function authenticateToken(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): void | Response {
  const authHeader = req.headers["authorization"];
  const token = authHeader && authHeader.split(" ")[1]; // Bearer <token>

  if (!token) {
    return res.status(401).json({ error: { message: "Missing authorization header" } });
  }

  jwt.verify(token, config.jwtSecret, (err, decoded: any) => {
    if (err) {
      if (err.name === "TokenExpiredError") {
        return res.status(401).json({ error: { message: "Token has expired" } });
      }
      return res.status(401).json({ error: { message: "Invalid token" } });
    }

    const userId = decoded?.userId;
    if (!userId) {
      return res.status(401).json({ error: { message: "Invalid token payload" } });
    }

    const db = getDb();
    const user = db
      .prepare("SELECT id, email, role, status FROM users WHERE id = ?")
      .get(userId) as
      | { id: number; email: string; role: string; status: string }
      | undefined;

    if (!user) {
      return res.status(401).json({ error: { message: "User not found" } });
    }

    if (user.status !== "active") {
      return res.status(403).json({ error: { message: "Account is inactive" } });
    }

    req.user = user;
    next();
  });
}

export function requireRole(...allowedRoles: string[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void | Response => {
    if (!req.user) {
      return res.status(401).json({ error: { message: "Authentication required" } });
    }
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: { message: "Insufficient permissions" } });
    }
    next();
  };
}

export const requireShopkeeper = requireRole("shopkeeper", "admin");
export const requireVendor = requireRole("vendor", "admin");
export const requireAdmin = requireRole("admin");

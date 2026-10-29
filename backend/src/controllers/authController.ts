import { Request, Response } from "express";
import { getDb } from "../database";
import { config } from "../config";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";

interface RegisterBody {
  email: string;
  password: string;
  role?: string;
  business_name: string;
  address?: string;
  phone?: string;
  gst_number?: string;
}

interface LoginBody {
  email: string;
  password: string;
}

function generateToken(userId: number): string {
  return jwt.sign(
    { userId },
    config.jwtSecret,
    { expiresIn: config.jwtExpiresIn } as jwt.SignOptions
  );
}

function generateTokenResponse(userId: number) {
  const token = generateToken(userId);
  const expiresInSeconds =
    parseInt(config.jwtExpiresIn.replace(/[^0-9]/g, ""), 10) * 86400 || 7 * 24 * 3600;
  return {
    access_token: token,
    token_type: "bearer",
    expires_in: expiresInSeconds,
  };
}

/** POST /api/auth/register */
export async function register(req: Request, res: Response): Promise<void> {
  const { email, password, role = "shopkeeper", business_name, address, phone, gst_number } =
    req.body as RegisterBody;

  const db = getDb();

  const existing = db.prepare("SELECT id FROM users WHERE email = ?").get(email);
  if (existing) {
    res.status(409).json({ error: { message: "Email already registered" } });
    return;
  }

  const passwordHash = await bcrypt.hash(password, 10);

  const userInsert = db
    .prepare(
      "INSERT INTO users (email, password_hash, role, status) VALUES (?, ?, ?, 'active')"
    )
    .run(email, passwordHash, role);

  const userId = userInsert.lastInsertRowid as number;

  db.prepare(
    "INSERT INTO business_profiles (user_id, business_name, address, phone, gst_number) VALUES (?, ?, ?, ?, ?)"
  ).run(userId, business_name, address || null, phone || null, gst_number || null);

  const user = db
    .prepare("SELECT id, email, role, status FROM users WHERE id = ?")
    .get(userId) as { id: number; email: string; role: string; status: string };

  res.status(201).json({
    user: { id: user.id, email: user.email, role: user.role, status: user.status },
    ...generateTokenResponse(userId),
  });
}

/** POST /api/auth/login */
export async function login(req: Request, res: Response): Promise<void> {
  const { email, password } = req.body as LoginBody;

  const db = getDb();

  const user = db
    .prepare(
      "SELECT id, email, password_hash, role, status FROM users WHERE email = ?"
    )
    .get(email) as
    | { id: number; email: string; password_hash: string; role: string; status: string }
    | undefined;

  if (!user) {
    res.status(401).json({ error: { message: "Invalid email or password" } });
    return;
  }

  const passwordValid = await bcrypt.compare(password, user.password_hash);
  if (!passwordValid) {
    res.status(401).json({ error: { message: "Invalid email or password" } });
    return;
  }

  if (user.status !== "active") {
    res.status(403).json({ error: { message: "Account is inactive" } });
    return;
  }

  res.json({
    user: { id: user.id, email: user.email, role: user.role, status: user.status },
    ...generateTokenResponse(user.id),
  });
}

/** POST /api/auth/logout */
export function logout(_req: Request, res: Response): void {
  // JWT is stateless; client clears its stored token on logout.
  res.json({ status: "ok", message: "Logged out" });
}

/** GET /api/auth/me */
export function me(req: Request, res: Response): void {
  const user = (req as any).user as {
    id: number;
    email: string;
    role: string;
    status: string;
  };
  res.json({ user: { id: user.id, email: user.email, role: user.role, status: user.status } });
}

/** GET /api/auth/me/profile */
export function getProfile(req: Request, res: Response): void {
  const user = (req as any).user as { id: number };
  const db = getDb();

  const profile = db
    .prepare(
      "SELECT id, user_id, business_name, address, phone, gst_number, created_at, updated_at FROM business_profiles WHERE user_id = ?"
    )
    .get(user.id);

  if (!profile) {
    res.status(404).json({ error: { message: "Business profile not found. Complete your profile setup." } });
    return;
  }

  res.json({ profile });
}

/** PATCH /api/auth/me/profile */
export function updateProfile(req: Request, res: Response): void {
  const user = (req as any).user as { id: number };
  const db = getDb();

  const existing = db
    .prepare("SELECT id FROM business_profiles WHERE user_id = ?")
    .get(user.id);
  if (!existing) {
    res.status(404).json({ error: { message: "Business profile not found" } });
    return;
  }

  const fields = ["business_name", "address", "phone", "gst_number"];
  const updates: string[] = [];
  const values: any[] = [];

  for (const field of fields) {
    if (req.body[field] !== undefined) {
      updates.push(`${field} = ?`);
      values.push(req.body[field]);
    }
  }

  if (updates.length === 0) {
    res.status(400).json({ error: { message: "No fields to update" } });
    return;
  }

  updates.push("updated_at = datetime('now')");
  values.push(user.id);

  db.prepare(
    `UPDATE business_profiles SET ${updates.join(", ")} WHERE user_id = ?`
  ).run(...values);

  const profile = db
    .prepare(
      "SELECT id, user_id, business_name, address, phone, gst_number, created_at, updated_at FROM business_profiles WHERE user_id = ?"
    )
    .get(user.id);

  res.json({ profile });
}

/** POST /api/auth/me/profile/complete */
export function completeProfile(req: Request, res: Response): void {
  const user = (req as any).user as { id: number };
  const { business_name } = req.body as { business_name: string };
  const db = getDb();

  const existing = db
    .prepare("SELECT id FROM business_profiles WHERE user_id = ?")
    .get(user.id);
  if (existing) {
    res.status(400).json({ error: { message: "Profile already exists. Use PATCH to update." } });
    return;
  }

  if (!business_name || !business_name.trim()) {
    res.status(400).json({ error: { message: "business_name is required" } });
    return;
  }

  const insert = db
    .prepare(
      "INSERT INTO business_profiles (user_id, business_name, address, phone, gst_number) VALUES (?, ?, ?, ?, ?)"
    )
    .run(user.id, business_name.trim(), null, null, null);

  const profile = db
    .prepare(
      "SELECT id, user_id, business_name, address, phone, gst_number, created_at, updated_at FROM business_profiles WHERE id = ?"
    )
    .get(insert.lastInsertRowid);

  res.status(201).json({ profile });
}

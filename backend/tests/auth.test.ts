import { describe, it, beforeAll, afterAll, expect } from "vitest";
import request from "supertest";
import { app } from "../src/index";
import { initializeDatabase, getDb, closeDb } from "../src/database";

const TEST_DB = "./data/test.db";

describe("Auth API", () => {
  beforeAll(async () => {
    await initializeDatabase(TEST_DB);
    // Start from a clean slate on every run
    const db = getDb();
    db.exec("DELETE FROM business_profiles; DELETE FROM users;");
  });

  afterAll(() => {
    closeDb();
  });

  it("GET /health returns ok", async () => {
    const res = await request(app).get("/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });

  it("POST /api/auth/register creates a user and returns a token", async () => {
    const res = await request(app)
      .post("/api/auth/register")
      .send({
        email: "alice@example.com",
        password: "Password123",
        role: "shopkeeper",
        business_name: "Alice Traders",
      });
    expect(res.status).toBe(201);
    expect(res.body.user.email).toBe("alice@example.com");
    expect(res.body.user.role).toBe("shopkeeper");
    expect(res.body.access_token).toBeDefined();
  });

  it("POST /api/auth/register rejects duplicate email", async () => {
    const res = await request(app)
      .post("/api/auth/register")
      .send({
        email: "alice@example.com",
        password: "Password123",
        role: "shopkeeper",
        business_name: "Alice Traders",
      });
    expect(res.status).toBe(409);
  });

  it("POST /api/auth/login returns a token for valid credentials", async () => {
    const res = await request(app)
      .post("/api/auth/login")
      .send({ email: "alice@example.com", password: "Password123" });
    expect(res.status).toBe(200);
    expect(res.body.access_token).toBeDefined();
    expect(res.body.user.email).toBe("alice@example.com");
  });

  it("POST /api/auth/login rejects wrong password", async () => {
    const res = await request(app)
      .post("/api/auth/login")
      .send({ email: "alice@example.com", password: "WrongPassword" });
    expect(res.status).toBe(401);
  });

  it("GET /api/auth/me requires authentication", async () => {
    const res = await request(app).get("/api/auth/me");
    expect(res.status).toBe(401);
  });

  it("GET /api/auth/me returns user with valid token", async () => {
    const login = await request(app)
      .post("/api/auth/login")
      .send({ email: "alice@example.com", password: "Password123" });
    const token = login.body.access_token;

    const res = await request(app)
      .get("/api/auth/me")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.user.email).toBe("alice@example.com");
  });

  it("POST /api/auth/me/profile/complete returns 400 when profile already exists", async () => {
    // register already creates a business profile
    const reg = await request(app)
      .post("/api/auth/register")
      .send({
        email: "bob@example.com",
        password: "Password123",
        role: "vendor",
        business_name: "Bob Vendors",
      });
    const token = reg.body.access_token;

    const res = await request(app)
      .post("/api/auth/me/profile/complete")
      .set("Authorization", `Bearer ${token}`)
      .send({ business_name: "Bob Vendors Updated" });
    expect(res.status).toBe(400);
  });

  it("GET /api/auth/me/profile returns the business profile created at registration", async () => {
    const login = await request(app)
      .post("/api/auth/login")
      .send({ email: "bob@example.com", password: "Password123" });
    const token = login.body.access_token;

    const res = await request(app)
      .get("/api/auth/me/profile")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.profile.business_name).toBe("Bob Vendors");
  });

  it("PATCH /api/auth/me/profile updates the business profile", async () => {
    const login = await request(app)
      .post("/api/auth/login")
      .send({ email: "bob@example.com", password: "Password123" });
    const token = login.body.access_token;

    const res = await request(app)
      .patch("/api/auth/me/profile")
      .set("Authorization", `Bearer ${token}`)
      .send({ phone: "+1-555-0100" });
    expect(res.status).toBe(200);
    expect(res.body.profile.phone).toBe("+1-555-0100");
  });

  it("POST /api/auth/logout returns ok", async () => {
    const login = await request(app)
      .post("/api/auth/login")
      .send({ email: "alice@example.com", password: "Password123" });
    const token = login.body.access_token;

    const res = await request(app)
      .post("/api/auth/logout")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });

  it("GET /api/auth/me rejects expired/malformed token", async () => {
    const res = await request(app)
      .get("/api/auth/me")
      .set("Authorization", "Bearer not-a-real-token");
    expect(res.status).toBe(401);
  });
});

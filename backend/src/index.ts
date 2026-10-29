import express from "express";
import cors from "cors";
import dotenv from "dotenv";

import { config } from "./config";
import { initializeDatabase } from "./database";
import authRouter from "./routes/auth";
import { errorHandler } from "./middleware/error";

dotenv.config();

const app = express();
const PORT = config.port;

// CORS
const corsOrigins = config.corsOrigins.map((o) => o.trim()).filter(Boolean);
app.use(
  cors({
    origin: corsOrigins,
    credentials: true,
  })
);

// Body parsing
app.use(express.json());

// Health check
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "stocktalk-backend",
    version: "1.0.0",
  });
});

// API routes
app.use("/api/auth", authRouter);

// 404 handler
app.use((_req, res) => {
  res.status(404).json({ error: { message: "Not found" } });
});

// Error handler
app.use(errorHandler);

// Initialize database and start server only when run directly (not when imported for tests)
if (process.env.NODE_ENV !== "test") {
  initializeDatabase()
    .then(() => {
      app.listen(PORT, () => {
        console.log(`StockTalk backend listening on http://localhost:${PORT}`);
      });
    })
    .catch((err) => {
      console.error("Failed to initialize database:", err);
      process.exit(1);
    });
}

export { app };

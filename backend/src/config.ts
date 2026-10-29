import dotenv from "dotenv";

dotenv.config();

function required(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const config = {
  appName: required("APP_NAME", "StockTalk Backend"),
  port: parseInt(process.env.PORT || "8000", 10),
  nodeEnv: required("NODE_ENV", "development"),
  databaseFile: required("DATABASE_FILE", "./data/stocktalk_dev.db"),
  jwtSecret: required("JWT_SECRET", "change-me-in-production"),
  jwtExpiresIn: required("JWT_EXPIRES_IN", "7d"),
  corsOrigins: (process.env.CORS_ORIGINS || "http://localhost:5173,http://localhost:5174,http://localhost:3000").split(","),
};

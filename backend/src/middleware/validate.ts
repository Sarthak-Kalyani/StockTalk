import { Request, Response, NextFunction } from "express";
import { validationResult } from "express-validator";

export function validateRequest(req: Request, res: Response, next: NextFunction): void | Response {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ error: { message: errors.array()[0].msg } });
  }
  next();
}

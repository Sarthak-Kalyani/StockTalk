import { Router } from "express";
import {
  register,
  login,
  logout,
  me,
  completeProfile,
  getProfile,
  updateProfile,
} from "../controllers/authController";
import { authenticateToken, requireRole } from "../middleware/auth";
import { body, param } from "express-validator";
import { validateRequest } from "../middleware/validate";

const router = Router();

// Public auth routes
router.post(
  "/register",
  [
    body("email").isEmail().normalizeEmail().withMessage("Valid email is required"),
    body("password")
      .isLength({ min: 8 })
      .withMessage("Password must be at least 8 characters"),
    body("role")
      .optional()
      .isIn(["shopkeeper", "vendor"])
      .withMessage("Role must be shopkeeper or vendor"),
    body("business_name")
      .notEmpty()
      .trim()
      .withMessage("Business name is required"),
  ],
  validateRequest,
  register
);

router.post(
  "/login",
  [
    body("email").isEmail().normalizeEmail().withMessage("Valid email is required"),
    body("password").notEmpty().withMessage("Password is required"),
  ],
  validateRequest,
  login
);

router.post("/logout", authenticateToken, logout);

// Protected routes
router.get("/me", authenticateToken, me);

router.get("/me/profile", authenticateToken, getProfile);
router.patch(
  "/me/profile",
  authenticateToken,
  [
    body("business_name")
      .optional()
      .trim()
      .notEmpty()
      .withMessage("Business name cannot be empty"),
    body("phone").optional().trim().notEmpty().withMessage("Phone cannot be empty"),
    body("gst_number").optional().trim().notEmpty().withMessage("GST number cannot be empty"),
  ],
  validateRequest,
  updateProfile
);

router.post(
  "/me/profile/complete",
  authenticateToken,
  [
    body("business_name")
      .notEmpty()
      .trim()
      .withMessage("Business name is required"),
  ],
  validateRequest,
  completeProfile
);

export default router;

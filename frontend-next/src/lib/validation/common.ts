import { z } from "zod";

export const requiredText = (label: string, max = 255) =>
  z.string().trim().min(1, `${label} is required`).max(max, `${label} must be ${max} characters or fewer`);

export const optionalText = (max = 1000) =>
  z
    .string()
    .max(max, `Must be ${max} characters or fewer`)
    .optional()
    .transform((value) => {
      const trimmed = String(value || "").trim();
      return trimmed ? trimmed : undefined;
    });

export const optionalNullableText = (max = 1000) =>
  z
    .string()
    .max(max, `Must be ${max} characters or fewer`)
    .optional()
    .transform((value) => {
      const trimmed = String(value || "").trim();
      return trimmed ? trimmed : null;
    });

export const positiveId = (label: string) => z.number().int().positive(`${label} is required`);

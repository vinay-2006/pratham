-- Migration 007: Add Grad-CAM URL column to imaging_results
-- Run this in Supabase SQL Editor

ALTER TABLE imaging_results
ADD COLUMN IF NOT EXISTS gradcam_url TEXT DEFAULT '';

COMMENT ON COLUMN imaging_results.gradcam_url IS
  'Signed URL to the Grad-CAM heatmap overlay image stored in Supabase Storage';

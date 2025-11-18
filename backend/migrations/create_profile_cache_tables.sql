-- Migration: Create profile scoring cache and recommended jobs cache tables
-- Created: 2025-01-17
-- Description: Caches profile scoring analysis and recommended jobs to avoid repeated LLM calls

-- Profile scoring cache table
CREATE TABLE IF NOT EXISTS profile_scoring_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cv_profile_id UUID NOT NULL REFERENCES cv_profiles(id) ON DELETE CASCADE,
    scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    strengths TEXT[] DEFAULT ARRAY[]::TEXT[],
    weaknesses TEXT[] DEFAULT ARRAY[]::TEXT[],
    recommendations JSONB DEFAULT '[]'::JSONB,
    competitor_insights JSONB DEFAULT '{}'::jsonb,
    basic_metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS profile_scoring_cache_user_idx ON profile_scoring_cache(user_id);
CREATE INDEX IF NOT EXISTS profile_scoring_cache_cv_profile_idx ON profile_scoring_cache(cv_profile_id);

-- Recommended jobs cache table
CREATE TABLE IF NOT EXISTS recommended_jobs_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_ids UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS recommended_jobs_cache_user_idx ON recommended_jobs_cache(user_id);
CREATE INDEX IF NOT EXISTS recommended_jobs_cache_expires_idx ON recommended_jobs_cache(expires_at);


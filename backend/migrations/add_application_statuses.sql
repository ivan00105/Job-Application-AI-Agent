-- Migration to add application status constraints and update existing records
-- This migration adds a CHECK constraint to ensure only valid statuses are used

-- First, update any existing 'draft' statuses to 'saved' (more user-friendly)
UPDATE applications SET status = 'saved' WHERE status = 'draft' OR status IS NULL;

-- Add CHECK constraint for valid statuses
-- Note: PostgreSQL doesn't support ALTER COLUMN ... ADD CONSTRAINT directly,
-- so we'll need to drop and recreate if constraint exists, or add it if it doesn't
DO $$
BEGIN
    -- Drop existing constraint if it exists
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'applications_status_check'
    ) THEN
        ALTER TABLE applications DROP CONSTRAINT applications_status_check;
    END IF;
    
    -- Add new constraint with all valid statuses
    ALTER TABLE applications ADD CONSTRAINT applications_status_check 
    CHECK (status IN (
        'saved',
        'applied', 
        'interviewing',
        'offer',
        'accepted',
        'rejected',
        'declined',
        'withdrawn',
        'not_interested'
    ));
END $$;

-- Update default status to 'saved' instead of 'draft'
ALTER TABLE applications ALTER COLUMN status SET DEFAULT 'saved';

-- Add index for status filtering (already exists, but ensure it's there)
CREATE INDEX IF NOT EXISTS applications_status_idx ON applications(status);


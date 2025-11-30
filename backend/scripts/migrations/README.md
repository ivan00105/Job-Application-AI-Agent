# Database Migrations

This folder contains database migration scripts that set up the initial database schema.

## Main Migration

- `run_migration.py` - **Main database migration** - Creates the complete database schema from `backend/migrations/initialised_schema.sql`
  - This includes ALL tables: core tables, coding questions, multiple choice questions, game library, interview tables, etc.

## Additional Migrations (Optional)

These are for incremental updates to existing databases:

- `run_interview_migration.py` - Interview data migration
- `run_preparation_migration.py` - Preparation data migration
- `run_profile_cache_migration.py` - Profile cache migration
- `run_status_migration.py` - Status migration

## Usage

### For New Database Setup (Recommended)

Run the main migration from the `backend` directory:

```bash
python scripts/migrations/run_migration.py
```

This will create the complete database schema including all tables.

### For Existing Databases

If you need to add specific tables incrementally, you can run the individual migration scripts.

## Note

- The main `run_migration.py` script uses `initialised_schema.sql` which contains the complete database structure
- Individual schema files (`coding_questions_schema.sql`, `game_library_schema.sql`, etc.) have been consolidated into `initialised_schema.sql`
- These scripts are typically run once during initial setup. After the database is set up, these scripts are not needed for normal application operation.


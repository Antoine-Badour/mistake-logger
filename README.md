# Mistake Logger

A name-only SAT mistake tracker that can be hosted on Vercel and synced with Supabase.

## What changed

- Replaced the old Render/Python setup with a Vercel-friendly static site.
- Added a Supabase-backed data layer that works with just a name and no email login.
- Falls back to browser local storage if Supabase is not configured yet.

## Setup for Supabase

1. Create a Supabase project.
2. In the SQL editor, run:

```sql
create table if not exists mistakes (
  id bigserial primary key,
  username text not null,
  website text,
  unit text,
  concept text,
  note text,
  details text,
  done boolean default false,
  created_at timestamp with time zone default now()
);

create index if not exists mistakes_username_idx on mistakes (username);
```

3. Copy the project URL and anon key into your Vercel environment variables:

- SUPABASE_URL = https://prjkktsdmvbmdqduvqzz.supabase.co
- SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByamtrdHNkbXZibWRxZHV2cXp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMyNDAzNjAsImV4cCI6MjA5ODgxNjM2MH0.Fxa2UoeUhQMDpt_HqeFLeBB-BLqXuTAOeqlYupsx-0M

4. In Supabase, go to Authentication > Policies or the table editor and allow anonymous reads/writes for the mistakes table if needed.

5. Deploy to Vercel.

## Local preview

Open the project folder and run a simple static server, for example:

```bash
python -m http.server 8000
```

Then visit http://localhost:8000


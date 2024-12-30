-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing tables
DROP TABLE IF EXISTS public.habits CASCADE;
DROP TABLE IF EXISTS public.habit_entries CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create habits table
CREATE TABLE IF NOT EXISTS public.habits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    color TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_archived BOOLEAN DEFAULT FALSE,
    streak_count INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0
);

-- Create habit entries table
CREATE TABLE IF NOT EXISTS public.habit_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    habit_id UUID NOT NULL REFERENCES public.habits(id),
    user_id UUID NOT NULL REFERENCES public.users(id),
    completed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.habit_entries ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own habits"
    ON public.habits
    FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can create their own habits"
    ON public.habits
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own habits"
    ON public.habits
    FOR UPDATE
    USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own habits"
    ON public.habits
    FOR DELETE
    USING (user_id = auth.uid());

CREATE POLICY "Users can view their own habit entries"
    ON public.habit_entries
    FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can create their own habit entries"
    ON public.habit_entries
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Grant necessary permissions
GRANT ALL ON public.habits TO authenticated;
GRANT ALL ON public.habit_entries TO authenticated; 
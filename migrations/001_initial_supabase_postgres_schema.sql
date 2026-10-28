-- ============================================================================
-- QueryMind 2.0 – Supabase PostgreSQL Schema Migration
-- Migration: 001_initial_supabase_postgres_schema.sql
-- Description: Complete Relational Schema, Foreign Keys, Indexes & RLS Policies
-- ============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. USERS TABLE (Integrated with Supabase Auth auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_uid UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'faculty', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON public.users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);

-- 3. STUDENTS TABLE
CREATE TABLE IF NOT EXISTS public.students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    division VARCHAR(5) NOT NULL,
    user_id UUID REFERENCES public.users(user_id) ON DELETE SET NULL,
    enrollment_year INT DEFAULT 2024,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_students_division ON public.students(division);
CREATE INDEX IF NOT EXISTS idx_students_user_id ON public.students(user_id);

-- 4. SUBJECTS TABLE
CREATE TABLE IF NOT EXISTS public.subjects (
    subject_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(50) NOT NULL,
    credits INT NOT NULL DEFAULT 4 CHECK (credits > 0)
);

CREATE INDEX IF NOT EXISTS idx_subjects_department ON public.subjects(department);

-- 5. MARKS TABLE (Relational Join & Aggregation Core)
CREATE TABLE IF NOT EXISTS public.marks (
    mark_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES public.students(student_id) ON DELETE CASCADE,
    subject_id INT NOT NULL REFERENCES public.subjects(subject_id) ON DELETE CASCADE,
    marks NUMERIC(5, 2) NOT NULL CHECK (marks >= 0 AND marks <= 100),
    exam_type VARCHAR(20) DEFAULT 'Final',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_student_subject UNIQUE (student_id, subject_id, exam_type)
);

CREATE INDEX IF NOT EXISTS idx_marks_student_subject ON public.marks(student_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_marks_score ON public.marks(marks);

-- 6. ATTENDANCE TABLE (Attendance Tracking & Defaulter Queries)
CREATE TABLE IF NOT EXISTS public.attendance (
    att_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES public.students(student_id) ON DELETE CASCADE,
    subject_id INT NOT NULL REFERENCES public.subjects(subject_id) ON DELETE CASCADE,
    attended INT NOT NULL CHECK (attended >= 0),
    total_classes INT NOT NULL CHECK (total_classes > 0),
    percentage NUMERIC(5, 2) GENERATED ALWAYS AS (ROUND((attended::numeric / total_classes::numeric) * 100, 2)) STORED,
    CONSTRAINT uq_attendance_student_subject UNIQUE (student_id, subject_id)
);

CREATE INDEX IF NOT EXISTS idx_attendance_student ON public.attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_percentage ON public.attendance(percentage);

-- 7. QUERY LOGS (Auditing Voice vs Text Input Modes)
CREATE TABLE IF NOT EXISTS public.query_logs (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(user_id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    input_mode VARCHAR(10) NOT NULL DEFAULT 'text' CHECK (input_mode IN ('voice', 'text')),
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    row_count INT DEFAULT 0,
    exec_time_ms NUMERIC(8, 2) DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_logs_user_date ON public.query_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_logs_mode ON public.query_logs(input_mode);

-- 8. AUDIT LOGS
CREATE TABLE IF NOT EXISTS public.audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(user_id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    target_table VARCHAR(50),
    ip_address INET,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON public.audit_logs(timestamp DESC);

-- ============================================================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.marks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.query_logs ENABLE ROW LEVEL SECURITY;

-- Students can read their own profile
CREATE POLICY "Student can view own record"
    ON public.students FOR SELECT
    USING (
        auth.uid() IN (SELECT auth_uid FROM public.users WHERE users.user_id = students.user_id)
        OR EXISTS (SELECT 1 FROM public.users WHERE auth_uid = auth.uid() AND role IN ('faculty', 'admin'))
    );

-- Students can read their own marks
CREATE POLICY "Student can view own marks"
    ON public.marks FOR SELECT
    USING (
        student_id IN (
            SELECT s.student_id FROM public.students s
            JOIN public.users u ON s.user_id = u.user_id
            WHERE u.auth_uid = auth.uid()
        )
        OR EXISTS (SELECT 1 FROM public.users WHERE auth_uid = auth.uid() AND role IN ('faculty', 'admin'))
    );

-- Faculty and Admin can inspect all attendance records
CREATE POLICY "Faculty and admin view attendance"
    ON public.attendance FOR SELECT
    USING (
        EXISTS (SELECT 1 FROM public.users WHERE auth_uid = auth.uid() AND role IN ('faculty', 'admin'))
        OR student_id IN (
            SELECT s.student_id FROM public.students s
            JOIN public.users u ON s.user_id = u.user_id
            WHERE u.auth_uid = auth.uid()
        )
    );

-- Users can only read their own query logs, Admins can inspect all
CREATE POLICY "User view own query logs"
    ON public.query_logs FOR SELECT
    USING (
        user_id IN (SELECT user_id FROM public.users WHERE auth_uid = auth.uid())
        OR EXISTS (SELECT 1 FROM public.users WHERE auth_uid = auth.uid() AND role = 'admin')
    );

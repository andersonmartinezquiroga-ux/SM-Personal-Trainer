create table students (
  id text primary key,
  name text not null,
  email text,
  goal text,
  level text,
  weight_kg numeric,
  active boolean default true
);

create table workouts (
  id text primary key,
  title text not null,
  subtitle text
);

create table exercises (
  id text primary key,
  workout_id text references workouts(id) on delete cascade,
  name text not null,
  sets integer not null,
  reps text not null
);

create table assignments (
  id text primary key,
  student_id text references students(id) on delete cascade,
  workout_id text references workouts(id) on delete cascade,
  assigned_date date not null,
  completed boolean default false
);

create table progress_entries (
  id text primary key,
  student_id text references students(id) on delete cascade,
  date date not null,
  weight_kg numeric,
  waist_cm numeric,
  chest_cm numeric,
  arm_cm numeric
);

create table if not exists traders (
  id bigserial primary key,
  phone text not null unique,
  language text default 'twi',
  goods_type text[] default '{}',
  market text,
  working_cap numeric,
  susu_day text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists interactions (
  id bigserial primary key,
  trader_phone text not null,
  incoming_message text,
  transcription text,
  claude_input text,
  claude_output text,
  final_reply text,
  distress_flag boolean not null default false,
  fraud_flag boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists credit_customers (
  id bigserial primary key,
  trader_phone text not null,
  customer_name text not null,
  amount_owed numeric not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

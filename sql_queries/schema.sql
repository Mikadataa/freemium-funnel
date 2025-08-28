-- Canonical freemium analytics schema
CREATE TABLE IF NOT EXISTS users (
    user_id        BIGINT PRIMARY KEY,
    signup_ts      TIMESTAMP NOT NULL,
    channel        TEXT,
    country        TEXT,
    device         TEXT
);

CREATE TABLE IF NOT EXISTS events (
    event_id    BIGSERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(user_id),
    event_ts    TIMESTAMP NOT NULL,
    event_type  TEXT NOT NULL CHECK (event_type IN ('signup','session_start','session_end','activate','subscribe','cancel')),
    device      TEXT,
    source      TEXT
);
CREATE INDEX IF NOT EXISTS ix_events_user_ts ON events(user_id, event_ts);

CREATE TABLE IF NOT EXISTS subscriptions (
    sub_id     BIGSERIAL PRIMARY KEY,
    user_id    BIGINT REFERENCES users(user_id),
    start_ts   TIMESTAMP NOT NULL,
    plan       TEXT,
    price      NUMERIC(10,2),
    cancel_ts  TIMESTAMP NULL
);
CREATE INDEX IF NOT EXISTS ix_sub_user_start ON subscriptions(user_id, start_ts);

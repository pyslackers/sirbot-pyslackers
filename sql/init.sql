CREATE SCHEMA slack;

CREATE TABLE slack.messages (
  id TEXT PRIMARY KEY NOT NULL,
  text TEXT,
  "user" TEXT,
  channel TEXT,
  raw JSONB
);

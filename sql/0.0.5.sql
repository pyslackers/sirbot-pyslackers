CREATE TABLE slack.recordings (
  id SERIAL PRIMARY KEY,
  start TEXT NOT NULL,
  "end" TEXT DEFAULT NULL,
  "user" TEXT,
  "channel" TEXT,
  created TIMESTAMP WITH TIME ZONE DEFAULT now()
)

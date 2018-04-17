DROP TABLE IF EXISTS slack.recordings;

CREATE TABLE slack.recordings (
  id SERIAL PRIMARY KEY,
  start TIMESTAMP WITH TIME ZONE NOT NULL,
  "end" timestamp WITH TIME ZONE NOT NULL,
  "user" TEXT NOT NULL,
  channel TEXT NOT NULL,
  comment TEXT,
  created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

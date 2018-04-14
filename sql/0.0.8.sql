CREATE TABLE slack.reports (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
  "user" TEXT NOT NULL,
  channel TEXT,
  comment TEXT NOT NULL
)

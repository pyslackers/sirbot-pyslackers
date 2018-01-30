ALTER TABLE slack.messages ADD COLUMN time TIMESTAMP;
UPDATE slack.messages SET time = to_timestamp(left(id, 10)::INT);

CREATE TABLE IF NOT EXISTS quiz_attempts(
 id BIGSERIAL PRIMARY KEY,
 participant_id TEXT NOT NULL REFERENCES participants(id),
 event_id TEXT NOT NULL REFERENCES events(id),
 request_id TEXT NOT NULL,
 question_index INTEGER NOT NULL,
 choice INTEGER NOT NULL,
 correct BOOLEAN NOT NULL,
 is_first BOOLEAN NOT NULL,
 response TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(participant_id,request_id)
);
CREATE INDEX IF NOT EXISTS quiz_attempts_event_question ON quiz_attempts(event_id,question_index);
ALTER TABLE participants ADD COLUMN IF NOT EXISTS quiz_tracking_started_at TEXT;
UPDATE participants SET quiz_tracking_started_at=created_at WHERE attempts=0 AND quiz_tracking_started_at IS NULL;
ALTER TABLE participants ALTER COLUMN quiz_tracking_started_at SET DEFAULT CURRENT_TIMESTAMP::TEXT;

-- Append an option to the original three-choice snapshots without changing answer indices.
UPDATE events SET questions=(SELECT jsonb_agg(CASE WHEN item->>'prompt'='對於沒有症狀的一般族群，哪一項乳癌篩檢說法較正確？' AND jsonb_array_length(item->'choices')=3 THEN jsonb_set(item,'{choices}',(item->'choices') || '["只要沒有摸到腫塊，就不需要依建議接受定期乳癌篩檢。"]'::jsonb) ELSE item END ORDER BY ord) FROM jsonb_array_elements(questions::jsonb) WITH ORDINALITY AS q(item,ord))::text;
UPDATE events SET questions=(SELECT jsonb_agg(CASE WHEN item->>'prompt'='對於適合接受乳房保留手術並依建議接受放射治療的病人，哪一項比較正確？' AND jsonb_array_length(item->'choices')=3 THEN jsonb_set(item,'{choices}',(item->'choices') || '["全乳切除後，任何病人都完全不需要再接受其他治療。"]'::jsonb) ELSE item END ORDER BY ord) FROM jsonb_array_elements(questions::jsonb) WITH ORDINALITY AS q(item,ord))::text;
UPDATE events SET questions=(SELECT jsonb_agg(CASE WHEN item->>'prompt'='腫瘤多基因表現檢測在乳癌化學治療決策中的角色，哪一項較正確？' AND jsonb_array_length(item->'choices')=3 THEN jsonb_set(item,'{choices}',(item->'choices') || '["多基因表現檢測分數低，就能保證未來完全不會復發。"]'::jsonb) ELSE item END ORDER BY ord) FROM jsonb_array_elements(questions::jsonb) WITH ORDINALITY AS q(item,ord))::text;

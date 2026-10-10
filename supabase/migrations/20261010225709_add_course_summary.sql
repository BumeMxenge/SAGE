-- The short outline shown on an elective card, one or two sentences written by the LLM from the
-- course's passage at load time and reviewed as a courses delta (null = not written yet). It is
-- not handbook text, so it is never cited. The table's existing grants and policy cover it.
alter table public.courses add column summary text;

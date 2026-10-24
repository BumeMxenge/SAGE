-- A citation is keyed by its number in the reply, not by the passage it quotes. The advisor quotes a
-- table one row a citation, so one reply often quotes a passage more than once, and the old key,
-- (message_id, passage_id), refused the second quote after the question and reply were saved,
-- losing every source of that reply. The position was already unique in a reply, so it becomes the
-- key and its separate constraint goes. The table's grants and policy are unchanged.
alter table public.message_citations
  drop constraint message_citations_pkey,
  drop constraint message_citations_message_id_position_key,
  add primary key (message_id, position);

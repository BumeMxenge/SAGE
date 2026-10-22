-- A plan course's choices now hold each choice group's alternatives that fit the rest of the plan,
-- as a list, so the planner can offer them to pick from, and one left is fixed. The engine stored
-- only the alternative every way of attending a plan shared, so each stored value becomes a one-item
-- list. A value that is already a list stays as it is, so a row written by the new code before this
-- ran stays right. The table's existing grants and policy cover the column.
update public.plan_courses
set choices = (
  select jsonb_object_agg(
    pair.key,
    case jsonb_typeof(pair.value)
      when 'string' then jsonb_build_array(pair.value)
      else pair.value
    end
  )
  from jsonb_each(choices) as pair
)
where choices <> '{}'::jsonb;

comment on column public.plan_courses.choices is
  'Each choice group''s alternatives that fit the rest of the plan, sorted, such as {"lab": ["A", "B"]}; one left is fixed. Null = none recorded, so every alternative shows.';

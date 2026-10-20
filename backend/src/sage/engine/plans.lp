% Every valid plan for one student's year, from the facts engine/facts.py writes for her. A plan takes
% each required course and a set of electives with none to spare, its courses' entry rules can still
% hold, it meets every year rule she still owes, and it attends one alternative of each choice group
% with no two of its meetings clashing. Each answer set is one way of attending one plan, and the
% solver reports each plan once, by its courses alone.

% The facts' predicates, any of which one student's facts may leave out
#defined required/1.
#defined elective/1.
#defined course/2.
#defined switch/1.
#defined need/3.
#defined counts/2.
#defined floor/1.
#defined entry/2.
#defined node/2.
#defined child/2.
#defined planned/2.
#defined maybe/2.
#defined unknown/1.
#defined meeting/6.
#defined alternative/3.
#defined option/3.
#defined untimed/1.
#defined extra/1.

% Each requirement holds while its switch is on, so a plan that can't exist can be traced to the
% requirements that rule it out
{ on(X) : switch(X) }.

% Her required courses, and any set of electives
take(C) :- required(C), on(take(C)).
{ take(C) : elective(C) }.

% A course's entry rule as her record leaves it, met when the plan takes what it needs, and possible
% when it could still hold
met(N) :- planned(N, X), take(X).
met(N) :- node(N, all), met(M) : child(N, M).
met(N) :- node(N, any), child(N, M), met(M).
possible(N) :- met(N).
possible(N) :- unknown(N).
possible(N) :- maybe(N, X), take(X).
possible(N) :- node(N, all), possible(M) : child(N, M).
possible(N) :- node(N, any), child(N, M), possible(M).
:- take(C), entry(C, N), not possible(N).

% A course is conditional when its rule only possibly holds (unsure), or a meeting of it has no
% printed time
unsure(C) :- take(C), entry(C, N), not met(N).
conditional(C) :- unsure(C).
conditional(C) :- take(C), untimed(C).

% The year rules she still has to meet: so many more courses, or credits, from those that count
taken(R, N) :- need(R, courses, _), N = #count { C : take(C), counts(R, C) }.
got(R, S) :- need(R, credits, _), S = #sum { Cr, C : take(C), counts(R, C), course(C, Cr) }.
total(S) :- S = #sum { Cr, C : take(C), course(C, Cr) }.
:- need(R, courses, K), on(rule(R)), taken(R, N), N < K.
:- need(R, credits, K), on(rule(R)), got(R, S), S < K.
:- floor(K), on(floor), total(S), S < K.

% No spare elective: each one is needed, as dropping it would break a year rule or the minimum
needed(C) :- take(C), counts(R, C), need(R, courses, K), taken(R, K).
needed(C) :- take(C), counts(R, C), need(R, credits, K), got(R, S), course(C, Cr), S - Cr < K.
needed(C) :- take(C), floor(K), total(S), course(C, Cr), S - Cr < K.
:- take(C), elective(C), not needed(C).

% A course to try beside a finished plan, when the facts offer some
{ add(C) : extra(C) } 1.

% Each course attended, one alternative of each of its choice groups, and the meetings that brings
attend(C) :- take(C).
attend(C) :- add(C).
1 { pick(C, G, X) : option(C, G, X) } 1 :- attend(C), option(C, G, _).
attends(M) :- attend(C), meeting(M, C, _, _, _, _), not alternative(M, _, _).
attends(M) :- pick(C, G, X), meeting(M, C, _, _, _, _), alternative(M, G, X).

% Terms that overlap: the same term, a quarter and its semester, and the full year with both
% semesters and every quarter. Winter and summer overlap only themselves.
inside(q1, sem1).
inside(q2, sem1).
inside(q3, sem2).
inside(q4, sem2).
overlap(T, T) :- meeting(_, _, _, _, _, T).
overlap(Q, S) :- inside(Q, S).
overlap(S, Q) :- inside(Q, S).
overlap(full_year, T) :- inside(T, _).
overlap(full_year, T) :- inside(_, T).
overlap(T, full_year) :- overlap(full_year, T).

% Two meetings clash on the same day in overlapping terms when their times overlap. Meetings that
% only touch, one ending as the other starts, don't.
:- attends(M), attends(N), M < N, meeting(M, _, D, S1, E1, T1), meeting(N, _, D, S2, E2, T2),
   overlap(T1, T2), S1 < E2, S2 < E1.

#show take/1.
#show conditional/1.
#show unsure/1.
#show pick/3.
#show add/1.

% Grounded only to list plans, so each one comes once, by its courses alone. clingo works out the
% brave and cautious solves' consequences over projected atoms alone, so they leave this part out.
#program plans.
#project take/1.

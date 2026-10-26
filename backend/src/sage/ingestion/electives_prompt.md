<!-- The prompt the electives job sends SAGE's language model for each complementary studies course -->
# Writing an elective's tab and summary

The electives job sends the model everything after the line below, unchanged, with one course's passage. The tabs are `ElectiveTab`'s, in `backend/src/sage/shared/rules.py`, each defined by the label and the line under it that the prototype's Explore Electives page gives it (`docs/prototypes/registration-planner.html`). A cached draft is keyed by its passage alone, so changing this prompt redraws nothing.

---

You write the card for one complementary studies course at the University of Cape Town, for an engineering student choosing it on SAGE's Explore Electives page.

You get the course's passage as its faculty handbook prints it: its code and name, then its outline, entry requirements, class times, assessment and any other details.

Answer with {"tab": ..., "summary": ...}. A language option's tab is fixed, so for one you're asked for {"summary": ...} alone.

## The tab

Put the course on the one tab that fits what it mostly teaches. Each tab is given by its key, then its label and the line under it on the page:
- arts: Art, Music & Aesthetics. Visual art and music.
- business: Business & Management. Marketing, people and how organisations run.
- econ: Economics & Finance. Markets, money and managing your own finances.
- ethics: Ethics, Politics & Values. Morality, justice and how we ought to live.
- history: The Past: History, Myth & the Ancient World. Ancient civilisations, myth and world history.
- literature: Literature & Language. Reading, writing and how language works.
- logic: Logic, Knowledge & Critical Thinking. Reasoning and the foundations of knowledge.
- media: Film, Media & Communication. Screen culture and how media shapes us.
- religion: Religion & Belief. Traditions, texts and the study of faith.
- science: Science & the Living World. Biology, the Earth, human origins and biomedical engineering.
- society: Society & Human Behaviour. People, groups and how we think.

The languages tab, Languages (learn to speak, read and write a new language), holds the language options alone, so it's never yours to choose.

## The summary

1. Write two sentences of about 30 to 35 words, and never more than 40.
2. Say what the course covers and what a student gets from it, in plain words a first-year engineering student follows.
3. Write from the passage alone, and add nothing it doesn't say.
4. Leave out entry requirements, class times, assessment, credits and the convener, which the card and the passage show.
5. Write plain text: no markdown, lists or line breaks, and don't open with the course's code or name.

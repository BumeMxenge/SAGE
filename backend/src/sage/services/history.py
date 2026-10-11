# Her course history by year, newest first, with each year's average and her cumulative one. The
# averages follow the transcript's Term GPA rule, so they match the figures UCT prints.
from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from sage.domain.base import Row
from sage.domain.students import CourseHistoryLine, average


class HistoryYear(Row):
    academic_year: int
    year_of_study: int  # her first year is 1
    credits: int  # from every line, results or not
    average: Decimal | None
    lines: tuple[CourseHistoryLine, ...]


class History(Row):
    cumulative_average: Decimal | None
    years: tuple[HistoryYear, ...]  # newest first


def summary(lines: Sequence[CourseHistoryLine], intake_year: int) -> History:
    by_year: dict[int, list[CourseHistoryLine]] = defaultdict(list)
    for line in lines:
        by_year[line.academic_year].append(line)
    return History(
        cumulative_average=average(lines),
        years=tuple(
            HistoryYear(
                academic_year=year,
                year_of_study=year - intake_year + 1,
                credits=sum(line.credits for line in year_lines),
                average=average(year_lines),
                lines=tuple(
                    sorted(year_lines, key=lambda line: (line.course_code, line.term))
                ),
            )
            for year, year_lines in sorted(by_year.items(), reverse=True)
        ),
    )

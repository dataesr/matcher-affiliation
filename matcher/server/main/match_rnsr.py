import re

from matcher.server.main.matcher import Matcher
from matcher.server.main.utils import remove_ref_index

DEFAULT_STRATEGIES = [
    ['rnsr_code_number', 'rnsr_supervisor_acronym', 'rnsr_supervisor_name', 'rnsr_urban_unit'],
    ['rnsr_code_number', 'rnsr_supervisor_name', 'rnsr_urban_unit'],
    ['rnsr_code_number', 'rnsr_acronym'],
    ['rnsr_code_number', 'rnsr_name'],
    ['rnsr_code_number', 'rnsr_supervisor_acronym'],
    ['rnsr_code_number', 'rnsr_supervisor_name'],
    ['rnsr_code_number', 'rnsr_urban_unit'],
    ['rnsr_acronym', 'rnsr_name', 'rnsr_supervisor_name', 'rnsr_urban_unit'],
    ['rnsr_acronym', 'rnsr_name', 'rnsr_supervisor_acronym', 'rnsr_urban_unit'],
    ['rnsr_acronym', 'rnsr_name', 'rnsr_urban_unit'],
    ['rnsr_acronym', 'rnsr_supervisor_acronym', 'rnsr_urban_unit'],
    ['rnsr_acronym', 'rnsr_supervisor_name', 'rnsr_urban_unit'],
    ['rnsr_name', 'rnsr_supervisor_acronym', 'rnsr_urban_unit'],
    ['rnsr_name', 'rnsr_supervisor_name', 'rnsr_urban_unit'],
    ['rnsr_name', 'rnsr_acronym', 'rnsr_supervisor_acronym'],
    ['rnsr_name', 'rnsr_acronym', 'rnsr_supervisor_name'],
    ['rnsr_name', 'rnsr_urban_unit'],
    ['rnsr_acronym', 'rnsr_urban_unit'],
    ['rnsr_name', 'rnsr_acronym']
]


# Done here rather than in synonym settings in ES as they seem to cause highlight bugs
def pre_treatment_rnsr(query: str = '') -> str:
    # If query starts with a digit that can be a reference index
    query = remove_ref_index(query)
    rgx = re.compile("(?i)(unit. mixte de recherche)( |)(S)( |)([0-9])")
    return rgx.sub("umr\\3\\5", query).lower()


def match_rnsr(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    if 'year' in conditions:
        strategies_with_year = [strategy + ['rnsr_year'] for strategy in strategies.copy()]
        strategies = strategies_with_year
    matcher = Matcher()
    return matcher.match(conditions=conditions, strategies=strategies, pre_treatment_query=pre_treatment_rnsr)

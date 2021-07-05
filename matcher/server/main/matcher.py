from matcher.server.main.elastic_utils import get_index_name
from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.logger import get_logger

logger = get_logger(__name__)

def identity(x: str = '') -> str:
    return x


class Matcher:
    def __init__(self) -> None:
        self.es = MyElastic()

    def match(self, conditions: dict, strategies: list, pre_treatment_query=None, field: str = 'ids')\
            -> dict:
        if conditions is None:
            conditions = {}
        if pre_treatment_query is None:
            pre_treatment_query = identity
        verbose = conditions.get('verbose', False)
        index_prefix = conditions.get('index_prefix', '')
        query = conditions.get('query', '')
        logs = f'<h1> &#128269; {query}</h1>'
        for strategy in strategies:
            strategy_results = None
            all_hits = {}
            logs += f'<br/> - Matching strategy : {strategy}<br/>'
            for criterion in strategy:
                criterion_without_source = '_'.join(criterion.split('_')[1:])
                if criterion_without_source in conditions:
                    criterion_query = conditions[criterion_without_source]
                    #logger.debug(f"using {criterion_query} for criterion {criterion_without_source}")
                else:
                    criterion_query = pre_treatment_query(query)
                body = {'query': {'percolate': {'field': 'query', 'document': {'content': criterion_query}}},
                        '_source': {'includes': [field]},
                        'highlight': {'fields': {'content': {'type': 'fvh'}}}}
                index = get_index_name(index_name=criterion, source='', index_prefix=index_prefix)
                hits = self.es.search(index=index, body=body).get('hits', []).get('hits', [])
                all_hits[criterion] = hits
                highlights = [hit.get('highlight', {}).get('content') for hit in hits]
                #logs += '<br /><br />'.join(['<br />'.join(highlight) for highlight in highlights if highlight]) + '<br />'
                criteria_results = [hit.get('_source', {}).get(field) for hit in hits]
                criteria_results = [item for sublist in criteria_results for item in sublist]
                criteria_results = list(set(criteria_results))
                if strategy_results is None:
                    strategy_results = criteria_results
                else:
                    # Intersection
                    strategy_results = [result for result in strategy_results if result in criteria_results]
                logs += f'Criteria : {criterion} : {len(criteria_results)} matches <br/>'
            logs += f'Strategy has {len(strategy_results)} possibilities that match all criteria<br/>'
            # Strategies stopped as soon as a first result is met
            all_highlights = {}
            if len(strategy_results) > 0:
                logs += f'<hr>Results: {strategy_results}'
                for matching_criteria in all_hits:
                    for hit in all_hits[matching_criteria]:
                        matching_ids = list(set(hit['_source'][field]) & set(strategy_results))
                        for matching_id in matching_ids:
                            if matching_id not in all_highlights:
                                all_highlights[matching_id] = {}
                            all_highlights[matching_id][matching_criteria] = hit.get('highlight', {}).get('content', [])
                for matching_id in all_highlights:
                    logs += f'<br/><hr>Explanation for {matching_id} :<br/>'
                    for matching_criteria in all_highlights[matching_id]:
                        logs += f'{matching_criteria} : {all_highlights[matching_id][matching_criteria]}<br/>'
                final_res = {'results': strategy_results, 'highlights': all_highlights}
                if verbose:
                    final_res['logs'] = logs
                return final_res
        logs += "<br/> No results found"
        final_res = {'results': [], 'highlights': {}}
        if verbose:
            final_res['logs'] = logs
        return final_res
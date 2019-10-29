import pytest
from FireEyeHelix import Client, build_search_groupby_result, list_alerts_command, get_alert_by_id_command, \
    get_alert_notes_command, create_alert_note_command, get_events_by_alert_command, get_endpoints_by_alert_command, \
    get_cases_by_alert_command, add_list_item_command, get_list_items_command, update_list_item_command, \
    list_rules_command, edit_rule_command, search_command
from test_data.response_constants import ALERT_RESP, ALERTS_RESP, SEARCH_AGGREGATIONS_SINGLE_RESP, \
    SEARCH_AGGREGATIONS_MULTI_RESP, NOTES_GET_RESP, NOTES_CREATE_RESP, EVENTS_BY_ALERT_RESP, ENDPOINTS_BY_ALERT_RESP, \
    CASES_BY_ALERT_RESP, LIST_ITEMS_RESP, LIST_SINGLE_ITEM_RESP, RULE_RESP, SEARCH_MULTI_RESP
from test_data.result_constants import EXPECTED_AGGREGATIONS_MULTI_RSLT, EXPECTED_AGGREGATIONS_SINGLE_RSLT, \
    EXPECTED_ALERT_RSLT, EXPECTED_ALERTS_RSLT, EXPECTED_NOTES_GET_RSLT, EXPECTED_NOTES_CREATE_RSLT, \
    EXPECTED_EVENTS_BY_ALERT_RSLT, EXPECTED_ENDPOINTS_BY_ALERT_RSLT, EXPECTED_CASES_NY_ALERT_RSLT, \
    EXPECTED_SINGLE_LIST_ITEM_RSLT, EXPECTED_LIST_ITEMS_RSLT, EXPECTED_LIST_ITEMS_UPDATE_RSLT, EXPECTED_RULES_RSLT, \
    EXPECTED_SEARCH_RSLT


def test_build_search_groupby_result():
    separator = '|%$,$%|'
    assert build_search_groupby_result(SEARCH_AGGREGATIONS_SINGLE_RESP, separator) == EXPECTED_AGGREGATIONS_SINGLE_RSLT
    assert build_search_groupby_result(SEARCH_AGGREGATIONS_MULTI_RESP, separator) == EXPECTED_AGGREGATIONS_MULTI_RSLT


@pytest.mark.parametrize('command,args,response,expected_result', [
    (list_alerts_command, {'limit': 2}, ALERTS_RESP, EXPECTED_ALERTS_RSLT),
    (get_alert_by_id_command, {'id': 3232}, ALERT_RESP, EXPECTED_ALERT_RSLT),
    (get_alert_notes_command, {'id': 3232}, NOTES_GET_RESP, EXPECTED_NOTES_GET_RSLT),
    (create_alert_note_command, {'note': 'This is a note test', 'alert_id': 3232}, NOTES_CREATE_RESP,
     EXPECTED_NOTES_CREATE_RSLT),
    (get_events_by_alert_command, {'alert_id': 3232}, EVENTS_BY_ALERT_RESP, EXPECTED_EVENTS_BY_ALERT_RSLT),
    (get_endpoints_by_alert_command, {'alert_id': 3232, 'offset': 0}, ENDPOINTS_BY_ALERT_RESP,
     EXPECTED_ENDPOINTS_BY_ALERT_RSLT),
    (get_cases_by_alert_command, {'alert_id': 3232, 'offset': 0, 'limit': 1}, CASES_BY_ALERT_RESP,
     EXPECTED_CASES_NY_ALERT_RSLT),
    (add_list_item_command, {'list_id': 3232, 'value': 'test', 'type': 'misc', 'risk': 'Low'}, LIST_SINGLE_ITEM_RESP,
     EXPECTED_SINGLE_LIST_ITEM_RSLT),
    (get_list_items_command, {'list_id': 3232, 'offset': 0}, LIST_ITEMS_RESP, EXPECTED_LIST_ITEMS_RSLT),
    (update_list_item_command, {'list_id': 3232, 'value': 'test', 'type': 'misc', 'risk': 'Low', 'item_id': 163},
     LIST_SINGLE_ITEM_RESP, EXPECTED_LIST_ITEMS_UPDATE_RSLT),
    (list_rules_command, {'offset': 1}, RULE_RESP, EXPECTED_RULES_RSLT),
    (edit_rule_command, {'rule_id': '1.1.1', 'enabled': 'true'}, RULE_RESP, EXPECTED_RULES_RSLT),
    (search_command,
     {'query': 'domain:google.com', 'start': '4 days ago', 'groupby': 'subject', 'limit': 1, 'page_size': 2,
      'offset': 1}, SEARCH_MULTI_RESP, EXPECTED_SEARCH_RSLT)
])  # noqa: E124
def test_commands(command, args, response, expected_result, mocker):
    headers = {
        'accept': 'application/json',
        'x-fireeye-api-key': ''
    }
    client = Client(base_url='https://apps.fireeye.com/helix', verify=False, proxy=True, headers=headers)
    mocker.patch.object(client, '_http_request', return_value=response)
    res = command(client, args)
    import json
    with open('test_data/test.json', 'w+') as test_data:
        json.dump(res[1], test_data)
    assert expected_result == res[1]

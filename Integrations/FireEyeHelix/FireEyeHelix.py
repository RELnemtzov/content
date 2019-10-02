import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

''' IMPORTS '''
from typing import Dict, Tuple, List, Optional, Union, AnyStr, Any
import urllib3

# Disable insecure warnings
urllib3.disable_warnings()

"""GLOBALS/PARAMS
Attributes:
    INTEGRATION_NAME:
        Name of the integration as shown in the integration UI, for example: Microsoft Graph User.

    INTEGRATION_COMMAND_NAME:
        Command names should be written in all lower-case letters,
        and each word separated with a hyphen, for example: msgraph-user.

    INTEGRATION_CONTEXT_NAME:
        Context output names should be written in camel case, for example: MSGraphUser.
"""
INTEGRATION_NAME = 'FireEye Helix'
# lowercase with `-` dividers
INTEGRATION_COMMAND_NAME = 'helix'
# No dividers
INTEGRATION_CONTEXT_NAME = 'FireEye'


class Client(BaseClient):
    def test_module_request(self) -> Dict:
        """Performs basic GET request to check if the API is reachable and authentication is successful.

        Returns:
            Response content
        """
        return self._http_request('GET', '/healthcheck', resp_type='content')

    def list_alerts_request(self, limit: Union[int, str] = None, offset: Union[int, str] = None) -> Dict:
        """Returns all alerts by sending a GET request.

        Args:
            limit: The maximum number of alerts to return.
            offset: The initial index from which to return the results.
            # event_created_date_after: Optional[Union[str, datetime]] = None, todo: CHANGE THIS AND BELOW
            # event_created_date_before: Optional[Union[str, datetime]] = None
            # event_created_date_after: Returns events created after this date.
            # event_created_date_before: Returns events created before this date.

        Returns:
            Response from API.
        """
        suffix = '/api/v3/alerts'
        # Dictionary of params for the request
        params = assign_params(
            limit=limit,
            offset=offset
        )
        # Send a request using our http_request wrapper
        return self._http_request('GET', suffix, params=params)

    def get_alert_by_id_request(self, _id: Union[int, str]) -> Dict:
        """Return a single alert by sending a GET request.

        Args:
            _id: ID  of the alert to get.

        Returns:
            Response from API.
        """
        suffix = f'/api/v3/alerts/{_id}'
        return self._http_request('GET', suffix)

    def update_alert_by_id_request(self, body: Dict) -> Dict:
        """Updates a single alert by sending a POST request.

        Args:
            body: Request body to update dictionary.

        Returns:
            Response from API.
        """
        suffix = f'/api/v3/alerts'
        return self._http_request('POST', suffix, json_data=body)

    def create_alert_note(self, _id: Union[int, str], note: str) -> Dict:
        """Creates a single note for an alert by sending a POST request.

        Args:
            _id: Alert ID to create .
            note: Note to add to alert.

        Returns:
            Response from API.
        """
        suffix = f'/api/v3/alerts/{_id}/notes'
        body = assign_params(note=note)
        return self._http_request('POST', suffix, json_data=body)

    def create_alert_case(self, alert_id: Union[int, str], name: str, status: str = None,
                          severity: Union[int, str] = None, tags: str = None, priority: str = None, state: str = None,
                          info_links: str = None, assigned_to: str = None, total_days_unresolved: str = None,
                          description: str = None) -> Dict:
        """Creates a single case for an alert by sending a POST request.

        Args:
            alert_id: Alert ID to create case for.
            name: Name of the case.
            status: Status of the case.
            severity: Severity of the case.
            tags: Tags of the case.
            priority: Priority of the case.
            state: State of the case.
            info_links: Info links of the case.
            assigned_to: Assignee list.
            total_days_unresolved: Total days the case is unresolved.
            description: Description of the case.

        Returns:
            Response from API.
        """
        suffix = f'/api/v3/alerts/{alert_id}/cases'
        body = assign_params(
            status=status,
            severity=severity,
            tags=tags,
            name=name,
            priority=priority,
            state=state,
            info_links=info_links,
            assigned_to=assigned_to,
            total_days_unresolved=total_days_unresolved,
            description=description
        )
        return self._http_request('POST', suffix, json_data=body)


''' HELPER FUNCTIONS '''


def build_transformed_dict(src: Union[Dict, List], trans_dict: Dict) -> Union[Dict, List]:
    """Builds a dictionary according to a conversion map

    Args:
        src (dict): original dictionary to build from
        trans_dict (dict): dict in the format { 'OldKey': 'NewKey', ...}

    Returns: src copy with changed keys
    """
    if isinstance(src, list):
        return [build_transformed_dict(x, trans_dict) for x in src]
    res: Dict[str, Any] = {}
    for key, val in trans_dict.items():
        if isinstance(val, dict):
            # handle nested list
            sub_res = res
            item_val = [build_transformed_dict(item, val) for item in (demisto.get(src, key) or [])]
            key = underscoreToCamelCase(key)
            for sub_key in key.split('.')[:-1]:
                if sub_key not in sub_res:
                    sub_res[sub_key] = {}
                sub_res = sub_res[sub_key]
            sub_res[key.split('.')[-1]] = item_val
        elif '.' in val:
            # handle nested vals
            update_nested_value(res, val, to_val=demisto.get(src, key))
        else:
            res[val] = demisto.get(src, key)
    return res


def update_nested_value(src_dict: Dict[str, Any], to_key: str, to_val: Any):
    """
    Updates nested value according to transformation dict structure where 'a.b' key will create {'a': {'b': val}}
    Args:
        src_dict (dict): The original dict
        to_key (str): Key to transform to (expected to contain '.' to mark nested)
        to_val (any): The value that'll be put under the nested key
    """
    sub_res = src_dict
    to_key_lst = to_key.split('.')
    for sub_to_key in to_key_lst[:-1]:
        if sub_to_key not in sub_res:
            sub_res[sub_to_key] = {}
        sub_res = sub_res[sub_to_key]
    sub_res[to_key_lst[-1]] = to_val


''' COMMANDS '''


def test_module(client: Client, *_) -> Tuple[str, Dict, Dict]:
    """Performs a basic GET request to check if the API is reachable and authentication is successful.

    Args:
        client: Client object with request
        args: Usually demisto.args()

    Returns:
        'ok' if test successful.

    Raises:
        DemistoException: If test failed.
    """
    client.test_module_request()
    return 'ok', {}, {}


def fetch_incidents(
        client: Client,
        fetch_time: str,
        last_run: Optional[datetime] = None) -> Tuple[List, datetime]:
    """Uses to fetch incidents into Demisto
    Documentation: https://github.com/demisto/content/tree/master/docs/fetching_incidents

    Args:
        client: Client object with request
        fetch_time: From when to fetch if first time, e.g. `3 days`
        last_run: Last fetch object occurs.

    Returns:
        incidents, new last_run

    Examples:
        >>> client = Client('https://example.net/v1')
        >>> fetch_incidents(client, '3 days', datetime(2010, 1, 1, 0, 0))
    """
    timestamp_format = '%Y-%m-%dT%H:%M:%S'
    # Get incidents from API
    if not last_run:  # if first time running
        new_last_run, _ = parse_date_range(fetch_time)
        new_last_run = new_last_run.strftime(timestamp_format)
    else:
        new_last_run = last_run
    incidents: List = list()
    raw_response = client.list_alerts_request(event_created_date_after=new_last_run)  # TODO: Adjust this
    events = raw_response.get('event')
    if events:
        # Creates incident entry
        incidents = [{
            'name': f"{INTEGRATION_NAME}: {event.get('eventId')}",
            'occurred': event.get('createdAt'),
            'rawJSON': json.dumps(event)
        } for event in events]

        last_incident_timestamp = incidents[-1].get('occurred')
        new_last_run = datetime.strptime(last_incident_timestamp, timestamp_format)
    # Return results
    return incidents, new_last_run


def list_alerts(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Lists all alerts and return outputs in Demisto's format

    Args:
        client: Client object with request
        args: Usually demisto.args()

    Returns:
        Outputs
    """
    limit = args.get('limit')
    offset = args.get('offset')
    raw_response = client.list_alerts_request(limit=limit, offset=offset)
    alerts = raw_response.get('results')
    if alerts:
        title = f'{INTEGRATION_NAME} - List alerts:'
        context_entry = build_transformed_dict(alerts, {})  # TODO: edit this
        context = {
            f'{INTEGRATION_CONTEXT_NAME}.Alert(val.ID && val.ID === obj.ID)': context_entry  # TODO: Edit this
        }
        # Creating human readable for War room
        human_readable = tableToMarkdown(title, context_entry)
        # Return data to Demisto
        return human_readable, context, raw_response
    else:
        return f'{INTEGRATION_NAME} - Could not find any alerts.', {}, {}


def get_alert_by_id(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Get alert by id and return outputs in Demisto's format

    Args:
        client: Client object with request
        args: Usually demisto.args()

    Returns:
        Outputs
    """
    _id = args.get('id')
    raw_response = client.get_alert_by_id_request(_id=_id)
    if raw_response:
        title = f'{INTEGRATION_NAME} - Alert {_id}:'
        context_entry = build_transformed_dict(raw_response, {})  # TODO: edit this
        context = {
            f'{INTEGRATION_CONTEXT_NAME}.Alert(val.ID && val.ID === obj.ID)': context_entry  # TODO: Edit this
        }
        # Creating human readable for War room
        human_readable = tableToMarkdown(title, context_entry)
        # Return data to Demisto
        return human_readable, context, raw_response
    else:
        return f'{INTEGRATION_NAME} - Could not find any alerts.', {}, {}


def update_alert_by_id(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Lists all events and return outputs in Demisto's format

    Args:
        client: Client object with request
        args: Usually demisto.args()

    Returns:
        Outputs
    """
    _id = args.get('id')
    raw_response = client.update_alert_by_id_request(body=args)
    if raw_response:
        title = f'{INTEGRATION_NAME} - Updated Alert {_id}:'
        context_entry = build_transformed_dict(raw_response, {})  # TODO: edit this
        context = {
            f'{INTEGRATION_CONTEXT_NAME}.Alert(val.ID && val.ID === obj.ID)': context_entry  # TODO: Edit this
        }
        # Creating human readable for War room
        human_readable = tableToMarkdown(title, context_entry)
        # Return data to Demisto
        return human_readable, context, raw_response
    else:
        return f'{INTEGRATION_NAME} - Could not find any alerts.', {}, {}


def create_alert_note(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Create a note for an alert

    Args:
        client: Client object with request
        args: Usually demisto.args()

    Returns:
        Outputs
    """
    _id = args.get('id')
    note = args.get('note')
    raw_response = client.create_alert_note(_id=_id, note=note)
    if raw_response:
        title = f'{INTEGRATION_NAME} - Updated Alert {_id}:'
        context_entry = build_transformed_dict(raw_response, {})  # TODO: edit this
        context = {
            f'{INTEGRATION_CONTEXT_NAME}.Note(val.ID && val.ID === obj.ID)': context_entry  # TODO: Edit this
        }
        # Creating human readable for War room
        human_readable = tableToMarkdown(title, context_entry)
        # Return data to Demisto
        return human_readable, context, raw_response
    else:
        return f'{INTEGRATION_NAME} - Could not find any alerts.', {}, {}


def create_alert_case(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Create a note for a case

    Args:
        client: Client object with request
        args: Usually demisto.args()

    Returns:
        Outputs
    """
    _id = args.get('id')
    note = args.get('note')
    raw_response = client.create_alert_case(_id=_id, note=note)
    if raw_response:
        title = f'{INTEGRATION_NAME} - Updated Alert {_id}:'
        context_entry = build_transformed_dict(raw_response, {})  # TODO: edit this
        context = {
            f'{INTEGRATION_CONTEXT_NAME}.Note(val.ID && val.ID === obj.ID)': context_entry  # TODO: Edit this
        }
        # Creating human readable for War room
        human_readable = tableToMarkdown(title, context_entry)
        # Return data to Demisto
        return human_readable, context, raw_response
    else:
        return f'{INTEGRATION_NAME} - Could not find any cases.', {}, {}


''' COMMANDS MANAGER / SWITCH PANEL '''


def main():  # pragma: no cover
    params = demisto.params()
    base_url = f"{params.get('url', '').rstrip('/')}"
    if not base_url.endswith('/helix/id'):
        base_url += '/helix/id'
    base_url += f"/{params.get('h_id')}"
    verify_ssl = not params.get('insecure', False)
    proxy = params.get('proxy')
    headers = {
        'accept': 'application/json',
        'x-fireeye-api-key': params.get('token')
    }
    client = Client(base_url=base_url, verify=verify_ssl, proxy=proxy, headers=headers)
    command = demisto.command()
    demisto.info(f'Command being called is {command}')

    # Switch case
    commands = {
        'test-module': test_module,
        'fetch-incidents': fetch_incidents,
        f'{INTEGRATION_COMMAND_NAME}-list-alerts': list_alerts,
        f'{INTEGRATION_COMMAND_NAME}-get-alert-by-id': get_alert_by_id,
        f'{INTEGRATION_COMMAND_NAME}-update-alert': update_alert_by_id,
        f'{INTEGRATION_COMMAND_NAME}-alert-create-note': create_alert_note,
        f'{INTEGRATION_COMMAND_NAME}-alert-create-case': create_alert_case,
    }
    try:
        if command == 'fetch-incidents':
            incidents, new_last_run = commands[command](client, last_run=demisto.getLastRun())
            demisto.incidents(incidents)
            demisto.setLastRun(new_last_run)
        elif command in commands:
            return_outputs(*commands[command](client, demisto.args()))
    # Log exceptions
    except Exception as e:
        err_msg = f'Error in {INTEGRATION_NAME} Integration [{e}]'
        return_error(err_msg, error=e)


if __name__ == 'builtins':  # pragma: no cover
    main()
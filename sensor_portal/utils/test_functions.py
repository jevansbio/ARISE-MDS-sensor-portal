def api_check_post(api_client, api_url, payload, check_key=None):
    """
    Function to test if object can be created and read through the API.

    Args:
        api_client (rest_framework.tests.APIclient): API client with a forced log in.
        api_url (string): URL to which the api_client will POST.
        payload (dict): data to POST.
        check_key (string): key to check in returned data.
    """
    response_create = api_client.post(
        api_url, data=payload, format="json")
    print(f"{response_create.data}")

    assert response_create.status_code == 201
    if check_key:
        assert response_create.data[check_key] == payload[check_key]
    response_id = response_create.data["id"]

    response_read = api_client.get(
        f"{api_url}{response_id}/", format="json")
    print(f"Response: {response_read.data}")
    assert response_read.status_code == 200
    if check_key:
        assert response_read.data[check_key] == payload[check_key]
    if "owner" in response_read.data.keys():
        assert response_read.data["owner"] == api_client.handler._force_user.username


def api_check_update(api_client, api_url, new_value, check_key=None):
    """
    Function to test if object can be updated and read through the API.

    Args:
        api_client (rest_framework.tests.APIclient): API client with a forced log in.
        api_url (string): URL which the api_client will PATCH.
        new_value (any): New value in the PATCH.
        check_key (string): Key which will be PATCHed and checked in the returned data.
    """
    response_update = api_client.patch(
        api_url, data={check_key: new_value}, format="json")
    print(f"Response: {response_update.data}")
    assert response_update.status_code == 200
    if check_key:
        assert response_update.data[check_key] == new_value

    response_read = api_client.get(
        api_url, format="json")
    print(f"Response: {response_read.data}")
    assert response_read.status_code == 200
    if check_key:
        assert response_read.data[check_key] == new_value


def api_check_delete(api_client, api_url):
    """
    Function to test if object can be deleted through the API.

    Args:
        api_client (rest_framework.tests.APIclient): API client with a forced log in.
        api_url (string): URL which the api_client will DELETE.
    """

    response_delete = api_client.delete(
        api_url, format="json")
    print(f"Response: {response_delete.data}")
    assert response_delete.status_code == 204

    response_read = api_client.get(
        api_url, format="json")
    print(f"Response: {response_read.data}")
    assert response_read.status_code == 404

import datetime
import logging
import os
from typing import Optional

import openapi_client
from authentication.arise_dsi_api_authentication import \
    AriseDsiApiAuthentication

logger = logging.getLogger(__name__)


class ARISEDSIClient:

    def __init__(self):
        self.arise_dsi_url = os.environ.get("ARISE_DSI_URL")
        self.authentication_server_url = os.environ.get(
            "ARISE_AUTHENTICATION_SERVER_URL")
        self.authentication_realm = "Arise"
        self.authentication_client_id = "arise_dsi_api"
        self.openapi_client_configuration = None
        self.offline_refresh_token = os.environ.get("OFFLINE_REFRESH_TOKEN")

    def initialise_authentication(self) -> None:
        if self.authentication_server_url is None:
            logger.error("No ARISE_AUTHENTICATION_SERVER_URL var set")
            return

        if self.offline_refresh_token is None:
            logger.error("No OFFLINE_REFRESH_TOKEN var set")
            return

        arise_dsi_api_authentication = None

        arise_dsi_api_authentication = AriseDsiApiAuthentication(
            self.authentication_server_url,
            self.authentication_realm,
            self.authentication_client_id,
            offline_refresh_token=self.offline_refresh_token,
        )

        arise_dsi_api_authentication.initialise(
            update_access_token_callback=self.update_access_token)

        self.openapi_client_configuration = openapi_client.Configuration(
            host=self.arise_dsi_url,
            access_token=arise_dsi_api_authentication.get_active_access_token()
        )

    def update_access_token(self, access_token: str) -> None:
        logger.info(f"Update ARISE DSI API access token: {access_token}.")
        if self.openapi_client_configuration:
            self.openapi_client_configuration.access_token = access_token

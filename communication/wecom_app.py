"""AIS WeCom application notification.

Sends one text message through a self-built WeCom application. It is the
simplest synchronous implementation: fetch a token, then post the message. No
group is required.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from config.logging_config import get_logger
from utils.constants import EnvVar
from utils.exceptions import AISException

_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
_SEND_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
_RECIPIENT = "@all"
_DEFAULT_TIMEOUT_SECONDS = 10.0
_LOGGER_NAME = "wecom"
_CONTENT_TYPE = "application/json"


class WeComAppNotifier:
    """Sends a text message through a self-built WeCom application."""

    def __init__(
        self,
        corp_id: str | None,
        app_secret: str | None,
        agent_id: str | None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Create the notifier for one WeCom application.

        Args:
            corp_id: Company identifier of the WeCom enterprise.
            app_secret: Secret of the self-built application.
            agent_id: Agent identifier of the self-built application.
            timeout_seconds: Timeout of a single request.
        """
        self._corp_id = corp_id
        self._app_secret = app_secret
        self._agent_id = agent_id
        self._timeout_seconds = timeout_seconds
        self._logger = get_logger(_LOGGER_NAME)

    def send(self, content: str) -> None:
        """Send one text message to every member of the enterprise.

        When the application credentials are not configured the message is not
        sent and a clear warning is logged instead. When WeCom answers with an
        error code the code and message are logged and raised, so a rejected
        message can never look like a delivered one.

        Args:
            content: Message body.

        Raises:
            AISException: When WeCom rejects the request.
            urllib.error.URLError: When the WeCom API cannot be reached.
        """
        if not self._corp_id or not self._app_secret or not self._agent_id:
            self._logger.warning(
                "WeCom application not configured (%s / %s / %s); message not sent",
                EnvVar.WECOM_CORP_ID.value,
                EnvVar.WECOM_APP_SECRET.value,
                EnvVar.WECOM_AGENT_ID.value,
            )
            return

        token = self._fetch_token()
        payload = json.dumps(
            {
                "touser": _RECIPIENT,
                "msgtype": "text",
                "agentid": int(self._agent_id),
                "text": {"content": content},
            }
        )
        answer = self._post(f"{_SEND_URL}?access_token={token}", payload)
        self._raise_on_error(answer, "message")
        self._logger.info("message sent through the WeCom application")

    def _fetch_token(self) -> str:
        """Return an access token for the application.

        Raises:
            AISException: When WeCom rejects the token request.
        """
        query = urllib.parse.urlencode(
            {"corpid": self._corp_id, "corpsecret": self._app_secret}
        )
        with urllib.request.urlopen(
            f"{_TOKEN_URL}?{query}", timeout=self._timeout_seconds
        ) as reply:
            answer = json.loads(reply.read().decode("utf-8"))
        self._raise_on_error(answer, "token")
        return str(answer["access_token"])

    def _post(self, url: str, payload: str) -> dict[str, object]:
        """Post one JSON payload and return the decoded answer."""
        request = urllib.request.Request(
            url,
            data=payload.encode("utf-8"),
            headers={"Content-Type": _CONTENT_TYPE},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as reply:
            return json.loads(reply.read().decode("utf-8"))

    def _raise_on_error(self, answer: dict[str, object], stage: str) -> None:
        """Raise when WeCom answered with a non-zero error code."""
        errcode = int(answer.get("errcode", -1))
        if errcode == 0:
            return
        message = (
            f"WeCom rejected the {stage} request: errcode={errcode} "
            f"errmsg={answer.get('errmsg')!r}"
        )
        self._logger.error("%s", message)
        raise AISException(message)

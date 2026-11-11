"""Gmail API adapter. Sync code depends on this small surface so tests can fake it."""

from __future__ import annotations

from dataclasses import dataclass, field

from googleapiclient.errors import HttpError


class GmailClientError(Exception):
    pass


class HistoryExpired(GmailClientError):
    """Gmail historyId is too old. Caller should fall back to a full search."""


class MessageGone(GmailClientError):
    pass


@dataclass
class HistoryPage:
    message_ids: list[str]
    latest_history_id: str


@dataclass
class MessagePage:
    ids: list[str]
    exhausted: bool


@dataclass
class GmailApiClient:
    service: object
    profile: dict = field(default_factory=dict)

    def get_profile(self) -> dict:
        if self.profile:
            return self.profile
        self.profile = self.service.users().getProfile(userId="me").execute()
        return self.profile

    def list_history(self, start_history_id: str, limit: int) -> HistoryPage:
        ids: list[str] = []
        page_token = None
        latest = start_history_id
        try:
            while len(ids) < limit:
                response = (
                    self.service.users()
                    .history()
                    .list(
                        userId="me",
                        startHistoryId=start_history_id,
                        historyTypes=["messageAdded"],
                        pageToken=page_token,
                        maxResults=min(100, max(limit - len(ids), 1)),
                    )
                    .execute()
                )
                latest = str(response.get("historyId", latest))
                for item in response.get("history", []):
                    for added in item.get("messagesAdded", []):
                        message = added.get("message") or {}
                        message_id = message.get("id")
                        if message_id:
                            ids.append(message_id)
                page_token = response.get("nextPageToken")
                if not page_token:
                    break
        except HttpError as error:
            status = getattr(getattr(error, "resp", None), "status", None)
            if status == 404:
                raise HistoryExpired("gmail history cursor expired") from error
            raise GmailClientError("gmail history list failed") from error
        unique = list(dict.fromkeys(ids))
        return HistoryPage(message_ids=unique[:limit], latest_history_id=latest)

    def list_messages(self, query: str, limit: int) -> MessagePage:
        ids: list[str] = []
        page_token = None
        exhausted = True
        try:
            while len(ids) < limit:
                response = (
                    self.service.users()
                    .messages()
                    .list(
                        userId="me",
                        q=query,
                        pageToken=page_token,
                        maxResults=min(100, max(limit - len(ids), 1)),
                    )
                    .execute()
                )
                for message in response.get("messages", []):
                    if message.get("id"):
                        ids.append(message["id"])
                page_token = response.get("nextPageToken")
                if not page_token:
                    exhausted = True
                    break
                if len(ids) >= limit:
                    exhausted = False
                    break
        except HttpError as error:
            raise GmailClientError("gmail message list failed") from error
        return MessagePage(ids=list(dict.fromkeys(ids))[:limit], exhausted=exhausted or len(ids) < limit)

    def get_message(self, message_id: str) -> dict:
        try:
            return (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except HttpError as error:
            status = getattr(getattr(error, "resp", None), "status", None)
            if status == 404:
                raise MessageGone(message_id) from error
            raise GmailClientError(f"gmail get failed for {message_id}") from error

"""Base widget classes for XRPL Dashboard."""

from __future__ import annotations

from abc import abstractmethod
from typing import TypeVar

from rustual.reactive import reactive
from rustual.screen import ModalScreen
from rustual.widgets import Static

T = TypeVar("T")


class DataWidget(Static):
    """Base class for data-displaying widgets with revision-based refresh.

    Subclasses should:
    - Override `_refresh()` to update widget content
    - Increment `revision` from parent App to trigger refresh
    """

    DEFAULT_CSS = """
    DataWidget {
        width: 100%;
        height: 100%;
        border: solid $primary;
        background: $surface;
    }

    DataWidget .widget-title {
        text-style: bold;
        padding: 0 2;
        height: auto;
        dock: top;
        background: $panel;
        border-bottom: solid $border;
    }
    """

    revision = reactive(0)

    def _get_store(self):
        """Get the state store from the app."""
        return self.app.store

    def watch_revision(self) -> None:
        """React to revision changes by refreshing."""
        self._refresh()

    @abstractmethod
    def _refresh(self) -> None:
        """Refresh widget content. Override in subclasses."""
        pass


class BaseModal(ModalScreen[T]):
    """Base modal with common patterns."""

    DEFAULT_CSS = """
    BaseModal {
        align: center middle;
    }

    BaseModal > Container {
        width: 64;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2 3;
    }

    BaseModal .modal-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        margin: 0;
    }

    BaseModal .button-bar {
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    BaseModal Button {
        margin: 0 1;
        min-width: 12;
    }

    BaseModal Input {
        width: 100%;
        margin: 1 0;
    }

    BaseModal Select {
        width: 100%;
        margin: 0 0 1 0;
    }
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(None)

    def _notify_error(self, msg: str) -> None:
        """Show error notification."""
        self.app.notify(msg, severity="error")

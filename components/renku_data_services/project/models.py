"""Models for project."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional, TypeAlias

from renku_data_services.authz.models import Visibility
from renku_data_services.namespace.models import Namespace
from renku_data_services.utils.etag import compute_etag_from_timestamp

Repository = str


@dataclass(frozen=True, eq=True, kw_only=True)
class Project:
    """Project model."""

    id: Optional[str]
    name: str
    slug: str
    namespace: Namespace
    visibility: Visibility
    created_by: str
    creation_date: datetime = field(default_factory=lambda: datetime.now(UTC).replace(microsecond=0))
    updated_at: datetime | None = field(default=None)
    repositories: list[Repository] = field(default_factory=list)
    description: Optional[str] = None
    keywords: Optional[list[str]] = None

    @property
    def etag(self) -> str | None:
        """Entity tag value for this project object."""
        if self.updated_at is None:
            return None
        return compute_etag_from_timestamp(self.updated_at)


ProjectsType: TypeAlias = list[Project]


@dataclass
class ProjectUpdate:
    """Indicates that a project has been updated and retains the old and new values."""

    old: Project
    new: Project

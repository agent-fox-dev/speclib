"""Campaign directory lifecycle management.

Handles creation, opening, spec enumeration, and new-spec provisioning
within a campaign working directory. A campaign is a directory containing
``campaign.yaml`` and one or more numbered spec subdirectories.

Full implementation is provided in task group 4.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CampaignMetadata:
    """Metadata stored in campaign.yaml.

    Attributes:
        name: Human-readable campaign name.
        description: Campaign description.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 last-update timestamp.
    """

    name: str
    description: str
    created_at: str  # ISO 8601
    updated_at: str  # ISO 8601


class Campaign:
    """Stub for campaign directory management.

    Full implementation is provided in task group 4.
    """

    def __init__(self) -> None:
        raise NotImplementedError("Campaign not yet implemented")

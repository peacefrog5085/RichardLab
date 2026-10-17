"""Fail-closed external integration policy for RichardLab Echo."""

from .gateway import Approval, IntegrationGateway, IntegrationPolicyError
from .registry import Capability, IntegrationRegistry

__all__ = [
    "Approval",
    "Capability",
    "IntegrationGateway",
    "IntegrationPolicyError",
    "IntegrationRegistry",
]

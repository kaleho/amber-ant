"""Plaid service module for financial data integration."""

from .client import PlaidClient, get_plaid_client
from .accounts import AccountService
from .transactions import TransactionService
from .institutions import InstitutionService
from .webhooks import WebhookService

__all__ = [
    "PlaidClient",
    "get_plaid_client",
    "AccountService",
    "TransactionService", 
    "InstitutionService",
    "WebhookService"
]
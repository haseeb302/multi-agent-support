"""
LangChain tools (Phase 1).

These tools must be backed by real file data:
- docs/customers.csv
- docs/retention_rules.json
- data/customer_updates.log
"""

from app.tools.customer import get_customer_data, get_customer_data_impl
from app.tools.retention import calculate_retention_offer, calculate_retention_offer_impl
from app.tools.status import update_customer_status, update_customer_status_impl

__all__ = [
    "get_customer_data",
    "get_customer_data_impl",
    "calculate_retention_offer",
    "calculate_retention_offer_impl",
    "update_customer_status",
    "update_customer_status_impl",
]

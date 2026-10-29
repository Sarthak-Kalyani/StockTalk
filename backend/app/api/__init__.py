"""
API Routes Package
"""
from . import auth, inventory, bills, vendors, chat, orders, payments, dashboard

__all__ = ["auth", "inventory", "bills", "vendors", "chat", "orders", "payments", "dashboard"]
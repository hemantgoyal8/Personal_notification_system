from pydantic import BaseModel
from typing import List, Dict, Any
import random
from datetime import datetime

# --- Mock Orders ---
class MockOrder(BaseModel):
    orderId: str
    userId: str # User email or ID
    status: str # e.g., 'processing', 'shipped', 'delivered'
    lastUpdate: datetime = None

# Simple in-memory store for mock orders
mock_orders_store: Dict[str, MockOrder] = {
    "order1001": MockOrder(orderId="order1001", userId="user1@example.com", status="processing", lastUpdate=datetime.utcnow()),
    "order1002": MockOrder(orderId="order1002", userId="user2@example.com", status="shipped", lastUpdate=datetime.utcnow()),
    "order1003": MockOrder(orderId="order1003", userId="user1@example.com", status="shipped", lastUpdate=datetime.utcnow()),
    "order1004": MockOrder(orderId="order1004", userId="user3@example.com", status="processing", lastUpdate=datetime.utcnow()),
}

ORDER_STATUS_FLOW = ["processing", "shipped", "delivered"]

def update_mock_order_status(order_id: str) -> MockOrder | None:
    """Simulates checking and potentially updating an order's status."""
    if order_id in mock_orders_store:
        order = mock_orders_store[order_id]
        now = datetime.utcnow()

        # Avoid updating too frequently or if already delivered
        if order.status == "delivered" or (order.lastUpdate and (now - order.lastUpdate).total_seconds() < 30): # Only update every 30s
             return None # No update needed right now

        current_index = ORDER_STATUS_FLOW.index(order.status)
        # Simple random chance to advance status
        if random.random() < 0.3 and current_index < len(ORDER_STATUS_FLOW) - 1: # 30% chance to advance
            new_status = ORDER_STATUS_FLOW[current_index + 1]
            order.status = new_status
            order.lastUpdate = now
            return order # Return updated order
    return None # Order not found or no update

# --- Mock Users (for promotions, simplified to avoid User Service call initially) ---
class MockUser(BaseModel):
    userId: str
    preferences: Dict[str, bool] = {"promotions": True, "order_updates": True, "recommendations": True}

mock_users_store: Dict[str, MockUser] = {
    "user1@example.com": MockUser(userId="user1@example.com", preferences={"promotions": True, "order_updates": True, "recommendations": True}),
    "user2@example.com": MockUser(userId="user2@example.com", preferences={"promotions": False, "order_updates": True, "recommendations": True}),
    "user3@example.com": MockUser(userId="user3@example.com", preferences={"promotions": True, "order_updates": False, "recommendations": False}),
}

# --- Mock Promotions ---
mock_promotions = [
    {"title": "Flash Sale!", "body": "Get 20% off electronics today!", "link": "/promotions/flash_sale"},
    {"title": "New Arrivals", "body": "Check out the latest fashion trends.", "link": "/collections/new"},
    {"title": "Free Shipping Weekend", "body": "Enjoy free shipping on all orders over $50.", "link": "/"},
]

def get_random_promotion() -> Dict[str, Any]:
    """Selects a random promotion."""
    return random.choice(mock_promotions)
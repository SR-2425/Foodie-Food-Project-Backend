from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Foodie API", version="1.0")

# -------------------------------
# Q1 - Home API
# -------------------------------
@app.get("/")
def welcome_user():
    return {
        "success": True,
        "app": "Foodie",
        "message": "Welcome to Foodie Food Delivery Service 🍔"
    }


# -------------------------------
# Q2 - Menu Data
# -------------------------------
food_menu = [
    {"id": 201, "title": "Paneer Pizza", "price": 349, "category": "Pizza", "available": True},
    {"id": 202, "title": "Chicken Burger", "price": 179, "category": "Burger", "available": True},
    {"id": 203, "title": "Cold Coffee", "price": 120, "category": "Drink", "available": True},
    {"id": 204, "title": "Veg Pasta", "price": 229, "category": "Pasta", "available": False},
    {"id": 205, "title": "French Fries", "price": 99, "category": "Snack", "available": True},
    {"id": 206, "title": "Brownie", "price": 149, "category": "Dessert", "available": True}
]


# -------------------------------
# Q2 - Get Menu
# -------------------------------
@app.get("/menu")
def fetch_menu():
    available_count = sum(1 for item in food_menu if item["available"])

    return {
        "total_items": len(food_menu),
        "available_items": available_count,
        "menu_list": food_menu
    }


# -------------------------------
# Q5 - Menu Summary
# -------------------------------
@app.get("/menu/summary")
def menu_summary():
    total = len(food_menu)
    available = sum(1 for item in food_menu if item["available"])
    unavailable = total - available

    categories = list(set(item["category"] for item in food_menu))

    return {
        "total_items": total,
        "available_items": available,
        "unavailable_items": unavailable,
        "categories": categories
    }


# -------------------------------
# Q10 - Filter Menu
# -------------------------------
@app.get("/menu/filter")
def filter_menu(category: str = None, available: bool = None):

    filtered_items = food_menu

    if category:
        filtered_items = [
            item for item in filtered_items
            if item["category"].lower() == category.lower()
        ]

    if available is not None:
        filtered_items = [
            item for item in filtered_items
            if item["available"] == available
        ]

    return {
        "results_count": len(filtered_items),
        "filtered_menu": filtered_items
    }


# -------------------------------
# Q3 - Get Single Item (ALWAYS LAST)
# -------------------------------
@app.get("/menu/{item_id}")
def fetch_single_item(item_id: int):
    for item in food_menu:
        if item["id"] == item_id:
            return {"status": "success", "data": item}

    return {"status": "error", "message": "Item not found in menu"}


# -------------------------------
# Q4 - Orders Storage
# -------------------------------
orders_data = []
order_counter = 1


@app.get("/orders")
def fetch_orders():
    return {
        "total_orders": len(orders_data),
        "orders_list": orders_data
    }


# -------------------------------
# Q6 - Pydantic Model
# -------------------------------
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: str = "delivery"


# -------------------------------
# Q7 - Helper Functions
# -------------------------------
def find_menu_item(item_id):
    for item in food_menu:
        if item["id"] == item_id:
            return item
    return None


def calculate_bill(price, quantity, order_type="delivery"):
    total_cost = price * quantity
    delivery_charge = 30 if order_type == "delivery" else 0
    final_amount = total_cost + delivery_charge

    return {
        "unit_price": price,
        "quantity": quantity,
        "delivery_charge": delivery_charge,
        "total_amount": final_amount
    }


# -------------------------------
# Q8 + Q9 - Place Order
# -------------------------------
@app.post("/orders")
def place_order(order: OrderRequest):
    global order_counter

    menu_item = find_menu_item(order.item_id)
    if not menu_item:
        return {"status": "error", "message": "Item does not exist"}

    if not menu_item["available"]:
        return {"status": "error", "message": "Item currently unavailable"}

    bill_details = calculate_bill(
        menu_item["price"],
        order.quantity,
        order.order_type
    )

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item_name": menu_item["title"],
        "quantity": order.quantity,
        "order_type": order.order_type,
        "delivery_address": order.delivery_address,
        "bill": bill_details
    }

    orders_data.append(new_order)
    order_counter += 1

    return {"status": "success", "order": new_order}


# -------------------------------
# Q11 - Update Order (PUT)
# -------------------------------
@app.put("/orders/{order_id}")
def update_order(order_id: int, updated_data: OrderRequest):

    for order in orders_data:
        if order["order_id"] == order_id:

            menu_item = find_menu_item(updated_data.item_id)
            if not menu_item:
                return {"status": "error", "message": "Item not found"}

            if not menu_item["available"]:
                return {"status": "error", "message": "Item unavailable"}

            order["customer_name"] = updated_data.customer_name
            order["item_name"] = menu_item["title"]
            order["quantity"] = updated_data.quantity
            order["delivery_address"] = updated_data.delivery_address
            order["order_type"] = updated_data.order_type

            order["bill"] = calculate_bill(
                menu_item["price"],
                updated_data.quantity,
                updated_data.order_type
            )

            return {
                "status": "updated",
                "order": order
            }

    return {
        "status": "error",
        "message": "Order not found"
    }
@app.delete("/orders/{order_id}")
def delete_order(order_id: int):

    for order in orders_data:
        if order["order_id"] == order_id:
            orders_data.remove(order)

            return {
                "status": "deleted",
                "message": f"Order {order_id} removed successfully"
            }

    return {
        "status": "error",
        "message": "Order not found"
    }
@app.get("/orders/search")
def search_orders(customer_name: str):

    matched_orders = [
        order for order in orders_data
        if customer_name.lower() in order["customer_name"].lower()
    ]

    return {
        "results_found": len(matched_orders),
        "orders": matched_orders
    }
@app.get("/orders/sort")
def sort_orders(by: str = "quantity", order: str = "asc"):

    if by not in ["quantity", "total"]:
        return {"status": "error", "message": "Invalid sort field"}

    reverse = True if order == "desc" else False

    if by == "quantity":
        sorted_orders = sorted(orders_data, key=lambda x: x["quantity"], reverse=reverse)
    else:
        sorted_orders = sorted(
            orders_data,
            key=lambda x: x["bill"]["total_amount"],
            reverse=reverse
        )

    return {
        "sorted_by": by,
        "order": order,
        "orders": sorted_orders
    }
@app.get("/orders/paginate")
def paginate_orders(page: int = 1, limit: int = 2):

    start = (page - 1) * limit
    end = start + limit

    paginated_data = orders_data[start:end]

    return {
        "page": page,
        "limit": limit,
        "total_orders": len(orders_data),
        "orders": paginated_data
    }
@app.get("/orders/advanced")
def advanced_orders(
    customer_name: str = None,
    sort_by: str = "quantity",
    order: str = "asc"
):

    filtered = orders_data

    # 🔹 Filter
    if customer_name:
        filtered = [
            o for o in filtered
            if customer_name.lower() in o["customer_name"].lower()
        ]

    # 🔹 Sort
    reverse = True if order == "desc" else False

    if sort_by == "quantity":
        filtered = sorted(filtered, key=lambda x: x["quantity"], reverse=reverse)
    elif sort_by == "total":
        filtered = sorted(filtered, key=lambda x: x["bill"]["total_amount"], reverse=reverse)

    return {
        "results": len(filtered),
        "data": filtered
    }
@app.get("/orders/stats")
def order_stats():

    if not orders_data:
        return {
            "total_orders": 0,
            "total_revenue": 0,
            "average_order_value": 0,
            "highest_order": None
        }

    total_orders = len(orders_data)
    total_revenue = sum(o["bill"]["total_amount"] for o in orders_data)
    avg_value = total_revenue / total_orders

    highest_order = max(orders_data, key=lambda x: x["bill"]["total_amount"])

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_order_value": round(avg_value, 2),
        "highest_order": highest_order
    }
@app.get("/orders/full-summary")
def full_summary():

    total_orders = len(orders_data)

    delivered = len([o for o in orders_data if o.get("status") == "delivered"])
    pending = total_orders - delivered

    total_revenue = sum(o["bill"]["total_amount"] for o in orders_data)

    return {
        "total_orders": total_orders,
        "delivered_orders": delivered,
        "pending_orders": pending,
        "total_revenue": total_revenue,
        "orders": orders_data
    }
@app.get("/orders/{order_id}")
def get_single_order(order_id: int):

    for order in orders_data:
        if order["order_id"] == order_id:
            return {
                "status": "success",
                "order": order
            }

    return {
        "status": "error",
        "message": "Order not found"
    }
@app.put("/orders/status/{order_id}")
def update_order_status(order_id: int, status: str):

    for order in orders_data:
        if order["order_id"] == order_id:
            order["status"] = status

            return {
                "status": "updated",
                "order_id": order_id,
                "new_status": status
            }

    return {
        "status": "error",
        "message": "Order not found"
    }

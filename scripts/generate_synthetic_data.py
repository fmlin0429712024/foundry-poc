#!/usr/bin/env python3
"""Generate synthetic, intentionally-messy source data for the Foundry PoC.

Produces three CSVs into data/raw/:
  - orders_system_a.csv
  - orders_system_b.csv
  - consolidated_customers.csv

See foundry-poc-brief.md for the exact messiness requirements this
implements (null order_ids, mixed date formats, mismatched keys, etc.).
"""
import csv
import random
from pathlib import Path

random.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie",
               "Drew", "Sam", "Reese", "Quinn", "Avery", "Rowan", "Skyler"]
LAST_NAMES = ["Brooks", "Chen", "Diaz", "Evans", "Farrell", "Gomez", "Hale",
              "Iyer", "Jansen", "Kwon", "Lund", "Mercer", "Nolan", "Ortiz"]
COMPANY_SUFFIX = ["Supply Co", "Office Partners", "Workspace Group", "Depot LLC",
                   "Business Solutions", "Enterprises", "& Sons", "Holdings"]
ITEMS = ["Copy Paper (Case)", "Stapler", "Ink Cartridge - Black", "Ink Cartridge - Color",
          "Desk Chair", "Filing Cabinet", "Whiteboard", "Sticky Notes (Pack)",
          "Binder Clips (Box)", "Monitor Stand", "USB Hub", "Desk Lamp",
          "Shredder", "Label Maker", "Envelopes (Box)"]
STATUSES_A = ["Open", "Pending", "Shipped", "Delivered", "Cancelled"]
STATUSES_B = ["open", "pending", "shipped", "delivered", "cancelled"]
ASSIGNEES = ["dpatel", "mklein", "jsantos", "rwong", "abrown", "", ""]


def random_customer_name():
    if random.random() < 0.5:
        return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    return f"{random.choice(LAST_NAMES)} {random.choice(COMPANY_SUFFIX)}"


def random_date_a():
    # system A: date-only, mostly one format but with a couple of stray formats
    m, d, y = random.randint(1, 12), random.randint(1, 28), random.choice([2024, 2025])
    fmt = random.choices(["mdy_slash", "iso", "dmon_y"], weights=[70, 20, 10])[0]
    if fmt == "mdy_slash":
        return f"{m:02d}/{d:02d}/{y}"
    if fmt == "iso":
        return f"{y}-{m:02d}-{d:02d}"
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{d:02d}-{months[m-1]}-{y}"


def random_datetime_b():
    m, d, y = random.randint(1, 12), random.randint(1, 28), random.choice([2024, 2025])
    h, mi = random.randint(0, 23), random.randint(0, 59)
    fmt = random.choices(["iso_dt", "iso_date", "mdy_slash"], weights=[60, 25, 15])[0]
    if fmt == "iso_dt":
        return f"{y}-{m:02d}-{d:02d}T{h:02d}:{mi:02d}:00"
    if fmt == "iso_date":
        return f"{y}-{m:02d}-{d:02d}"
    return f"{m:02d}/{d:02d}/{y}"


# --- consolidated_customers.csv --------------------------------------------
N_CUSTOMERS = 60
customers = []
for i in range(1, N_CUSTOMERS + 1):
    ccid = f"CUST-{i:04d}"
    name = random_customer_name()
    has_a = random.random() < 0.75
    has_b = random.random() < 0.75
    if not has_a and not has_b:
        has_a = True  # every customer must be reachable from at least one system
    sys_a_id = f"A-{1000+i}" if has_a else ""
    sys_b_id = f"B-{2000+i}" if has_b else ""
    customers.append([ccid, name, sys_a_id, sys_b_id])

# duplicate consolidated_customer_id edge case: same id, conflicting name, re-supplied
dup_source = customers[5]
customers.insert(6, [dup_source[0], "DUPLICATE " + dup_source[1], dup_source[2], dup_source[3]])

with open(OUT_DIR / "consolidated_customers.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["consolidated_customer_id", "customer_name", "system_a_customer_id", "system_b_customer_id"])
    w.writerows(customers)

valid_a_ids = [c[2] for c in customers if c[2]]
valid_b_ids = [c[3] for c in customers if c[3]]

# --- orders_system_a.csv ----------------------------------------------------
# headers deliberately inconsistent in casing
HEADERS_A = ["OrderID", "customer_id", "ItemName", "Order_Due_Date", "STATUS", "assignee"]
N_ORDERS_A = 120
rows_a = []
for i in range(N_ORDERS_A):
    if random.random() < 0.06:
        order_id = ""  # true empty-string null
    elif random.random() < 0.03:
        order_id = None  # missing field entirely (csv writer renders as empty too, kept for clarity)
    else:
        order_id = f"A-ORD-{10000+i}"

    if random.random() < 0.08:
        customer_id = f"A-{9900+i}"  # mismatched key, no match in consolidated_customers
    else:
        customer_id = random.choice(valid_a_ids)

    rows_a.append([
        order_id if order_id is not None else "",
        customer_id,
        random.choice(ITEMS),
        random_date_a(),
        random.choice(STATUSES_A),
        random.choice(ASSIGNEES),
    ])

with open(OUT_DIR / "orders_system_a.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(HEADERS_A)
    w.writerows(rows_a)

# --- orders_system_b.csv ----------------------------------------------------
HEADERS_B = ["order_id", "customer_id", "item_name", "dueDateTime", "status", "assignee", "order_placement_date"]
N_ORDERS_B = 110
rows_b = []
for i in range(N_ORDERS_B):
    if random.random() < 0.07:
        order_id = ""
    else:
        order_id = f"B-ORD-{20000+i}"

    if random.random() < 0.08:
        customer_id = f"B-{9900+i}"  # mismatched key
    else:
        customer_id = random.choice(valid_b_ids)

    placement_date = random_date_a()  # irrelevant column, should be dropped by transform

    rows_b.append([
        order_id,
        customer_id,
        random.choice(ITEMS),
        random_datetime_b(),
        random.choice(STATUSES_B),
        random.choice(ASSIGNEES),
        placement_date,
    ])

with open(OUT_DIR / "orders_system_b.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(HEADERS_B)
    w.writerows(rows_b)

print(f"Wrote {len(customers)} customers, {len(rows_a)} system-a orders, {len(rows_b)} system-b orders to {OUT_DIR}")

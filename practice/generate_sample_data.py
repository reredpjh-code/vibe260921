import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "sample.db"

random.seed(42)

NUM_CUSTOMERS = 500
NUM_ORDERS = 10000

SURNAMES = [
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "한", "오", "서", "신", "권", "황", "안", "송", "전", "홍",
    "유", "고", "문", "양", "손", "배", "백", "허", "남", "심",
]
GIVEN_FIRST = [
    "민", "서", "지", "현", "우", "은", "선", "재", "예", "도",
    "수", "하", "준", "유", "채", "다", "성", "가", "태", "소",
]
GIVEN_SECOND = [
    "준", "우", "아", "연", "빈", "호", "린", "율", "훈", "영",
    "진", "원", "경", "환", "형", "미", "나", "람", "결", "규",
]

# (ProductName, Category price range low, Category price range high, UnitsInStock max)
PRODUCTS = [
    ("무선 이어폰", 39000, 129000),
    ("블루투스 스피커", 25000, 89000),
    ("스마트워치", 59000, 259000),
    ("노트북 파우치", 12000, 35000),
    ("기계식 키보드", 45000, 159000),
    ("무선 마우스", 9900, 39000),
    ("보조배터리", 15000, 49000),
    ("USB 허브", 8900, 25000),
    ("공기청정기", 89000, 259000),
    ("가습기", 19000, 59000),
    ("전기포트", 15000, 39000),
    ("에어프라이어", 39000, 129000),
    ("믹서기", 19000, 69000),
    ("커피머신", 49000, 199000),
    ("텀블러", 8900, 29000),
    ("도자기 머그컵", 5900, 19000),
    ("유기농 원두", 12000, 25000),
    ("한라봉 세트", 15000, 35000),
    ("제주 감귤", 12000, 29000),
    ("샤인머스캣", 18000, 45000),
    ("한우 선물세트", 59000, 159000),
    ("전복 세트", 39000, 99000),
    ("김치냉장고용 김치", 9900, 29000),
    ("햇반 세트", 12000, 25000),
    ("라면 세트", 9900, 22000),
    ("견과류 선물세트", 19000, 49000),
    ("홍삼 진액", 39000, 99000),
    ("비타민 세트", 15000, 39000),
    ("샴푸 세트", 12000, 35000),
    ("바디워시", 8900, 25000),
    ("핸드크림 세트", 9900, 29000),
    ("면 티셔츠", 12000, 29000),
    ("청바지", 29000, 79000),
    ("운동화", 39000, 119000),
    ("등산 재킷", 59000, 189000),
    ("백팩", 29000, 89000),
    ("캠핑 텐트", 79000, 259000),
    ("접이식 테이블", 29000, 69000),
    ("휴대용 의자", 15000, 39000),
    ("독서대", 9900, 25000),
]

START_DATE = date(2023, 1, 1)
END_DATE = date(2025, 12, 31)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days


def random_date():
    return START_DATE + timedelta(days=random.randint(0, DATE_RANGE_DAYS))


def generate_customers(n):
    used_names = set()
    customers = []
    for cid in range(1, n + 1):
        while True:
            name = (
                random.choice(SURNAMES)
                + random.choice(GIVEN_FIRST)
                + random.choice(GIVEN_SECOND)
            )
            key = (name, cid)
            if key not in used_names:
                used_names.add(key)
                break
        last_name = name[0]
        first_name = name[1:]
        email = f"customer{cid}@example.com"
        customers.append((cid, first_name, last_name, email))
    return customers


def generate_products():
    products = []
    for pid, (name, low, high) in enumerate(PRODUCTS, start=1):
        unit_price = round(random.uniform(low, high), -2)  # round to nearest 100 won
        units_in_stock = random.randint(0, 300)
        products.append((pid, name, float(unit_price), units_in_stock))
    return products


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    cur.execute("DELETE FROM OrderDetails;")
    cur.execute("DELETE FROM Orders;")
    cur.execute("DELETE FROM Products;")
    cur.execute("DELETE FROM Customers;")

    customers = generate_customers(NUM_CUSTOMERS)
    products = generate_products()

    product_price_map = {p[0]: p[2] for p in products}

    orders = []
    details = []
    detail_id = 1
    product_ids = [p[0] for p in products]

    for order_id in range(1, NUM_ORDERS + 1):
        customer_id = random.randint(1, NUM_CUSTOMERS)
        order_date = random_date().isoformat()
        total_amount = float(random.randint(5000, 100000))
        orders.append((order_id, customer_id, order_date, total_amount))

        num_items = random.randint(1, 3)
        chosen_products = random.sample(product_ids, k=min(num_items, len(product_ids)))
        for pid in chosen_products:
            quantity = random.randint(1, 5)
            unit_price = product_price_map[pid]
            details.append((detail_id, order_id, pid, quantity, unit_price))
            detail_id += 1

    cur.executemany(
        "INSERT INTO Customers (CustomerID, FirstName, LastName, Email) VALUES (?, ?, ?, ?)",
        customers,
    )
    cur.executemany(
        "INSERT INTO Products (ProductID, ProductName, UnitPrice, UnitsInStock) VALUES (?, ?, ?, ?)",
        products,
    )
    cur.executemany(
        "INSERT INTO Orders (OrderID, CustomerID, OrderDate, TotalAmount) VALUES (?, ?, ?, ?)",
        orders,
    )
    cur.executemany(
        "INSERT INTO OrderDetails (OrderDetailID, OrderID, ProductID, Quantity, UnitPrice) "
        "VALUES (?, ?, ?, ?, ?)",
        details,
    )

    conn.commit()

    print(f"Customers: {len(customers)}")
    print(f"Products: {len(products)}")
    print(f"Orders: {len(orders)}")
    print(f"OrderDetails: {len(details)}")

    conn.close()


if __name__ == "__main__":
    main()

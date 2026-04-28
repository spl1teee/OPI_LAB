from sqlalchemy.orm import Session

from .models import Employee, Equipment, Ingredient, Operation, Order, Product, Recipe


def seed_data(db: Session) -> None:
    if db.query(Ingredient).count() > 0:
        return

    ingredients = [
        Ingredient(id=1, name="Мука высшего сорта", unit="кг", current_stock=50, shelf_life=180, expiry_date="2026-10-28", critical_threshold=10),
        Ingredient(id=2, name="Сахар", unit="кг", current_stock=30, shelf_life=365, expiry_date="2027-04-28", critical_threshold=5),
        Ingredient(id=3, name="Сливки 33%", unit="л", current_stock=0.5, shelf_life=7, expiry_date="2026-05-05", critical_threshold=1),
        Ingredient(id=4, name="Масло сливочное", unit="кг", current_stock=15, shelf_life=30, expiry_date="2026-05-28", critical_threshold=3),
        Ingredient(id=5, name="Яйца", unit="шт", current_stock=120, shelf_life=25, expiry_date="2026-05-23", critical_threshold=20),
        Ingredient(id=6, name="Какао-порошок", unit="кг", current_stock=8, shelf_life=365, expiry_date="2027-04-28", critical_threshold=2),
        Ingredient(id=7, name="Манго пюре", unit="кг", current_stock=5, shelf_life=14, expiry_date="2026-05-12", critical_threshold=1),
        Ingredient(id=8, name="Фисташки", unit="кг", current_stock=3, shelf_life=90, expiry_date="2026-07-27", critical_threshold=0.5),
        Ingredient(id=9, name="Яблоки", unit="кг", current_stock=12, shelf_life=14, expiry_date="2026-05-12", critical_threshold=2),
        Ingredient(id=10, name="Карамель", unit="кг", current_stock=4, shelf_life=180, expiry_date="2026-10-28", critical_threshold=1),
    ]
    db.add_all(ingredients)

    equipment = [
        Equipment(id=1, name="Миксер планетарный KitchenAid", type="Миксер", status="Свободно"),
        Equipment(id=2, name="Печь конвекционная UNOX", type="Печь", status="Свободно"),
        Equipment(id=3, name="Холодильная камера Polair", type="Холодильник", status="Свободно"),
        Equipment(id=4, name="Миксер планетарный Dito Sama", type="Миксер", status="Свободно"),
        Equipment(id=5, name="Кондитерская витрина", type="Витрина", status="Свободно"),
    ]
    db.add_all(equipment)

    employees = [
        Employee(id=1, name="Иванова Мария", role="Кондитер", status="Свободен", workload=0),
        Employee(id=2, name="Петров Дмитрий", role="Кондитер", status="Свободен", workload=0),
        Employee(id=3, name="Сидорова Анна", role="Кондитер", status="Свободен", workload=0),
        Employee(id=4, name="Козлов Сергей", role="Технолог", status="Свободен", workload=0),
    ]
    db.add_all(employees)

    products = [
        Product(id=1, name="Торт Прага"),
        Product(id=2, name="Чизкейк манго"),
        Product(id=3, name="Яблочный пирог с карамелью"),
        Product(id=4, name="Макарун фисташковый"),
    ]
    db.add_all(products)

    recipes = [
        Recipe(
            product_id=1,
            ingredients=[{"ingredientId": "1", "amount": 0.5}, {"ingredientId": "2", "amount": 0.3}, {"ingredientId": "3", "amount": 0.3}, {"ingredientId": "4", "amount": 0.2}, {"ingredientId": "5", "amount": 4}, {"ingredientId": "6", "amount": 0.1}],
            equipment=["1", "2", "3"],
            steps=[{"name": "Замес теста", "duration": 30, "equipment": "Миксер планетарный KitchenAid"}, {"name": "Выпечка коржей", "duration": 45, "equipment": "Печь конвекционная UNOX"}, {"name": "Охлаждение", "duration": 60, "equipment": "Холодильная камера Polair"}, {"name": "Приготовление крема", "duration": 20, "equipment": "Миксер планетарный KitchenAid"}, {"name": "Декорирование", "duration": 40, "equipment": "Кондитерская витрина"}],
        ),
        Recipe(
            product_id=2,
            ingredients=[{"ingredientId": "2", "amount": 0.2}, {"ingredientId": "3", "amount": 0.4}, {"ingredientId": "4", "amount": 0.15}, {"ingredientId": "5", "amount": 3}, {"ingredientId": "7", "amount": 0.3}],
            equipment=["1", "2", "3"],
            steps=[{"name": "Замес основы", "duration": 20, "equipment": "Миксер планетарный Dito Sama"}, {"name": "Выпечка основы", "duration": 30, "equipment": "Печь конвекционная UNOX"}, {"name": "Приготовление сырной массы", "duration": 25, "equipment": "Миксер планетарный KitchenAid"}, {"name": "Охлаждение", "duration": 180, "equipment": "Холодильная камера Polair"}, {"name": "Декорирование манго", "duration": 30, "equipment": "Кондитерская витрина"}],
        ),
        Recipe(
            product_id=3,
            ingredients=[{"ingredientId": "1", "amount": 0.4}, {"ingredientId": "2", "amount": 0.25}, {"ingredientId": "4", "amount": 0.15}, {"ingredientId": "5", "amount": 2}, {"ingredientId": "9", "amount": 1.5}, {"ingredientId": "10", "amount": 0.2}],
            equipment=["1", "2"],
            steps=[{"name": "Замес теста", "duration": 25, "equipment": "Миксер планетарный KitchenAid"}, {"name": "Подготовка яблок", "duration": 20, "equipment": "Миксер планетарный Dito Sama"}, {"name": "Выпечка пирога", "duration": 50, "equipment": "Печь конвекционная UNOX"}, {"name": "Карамелизация", "duration": 15, "equipment": "Печь конвекционная UNOX"}],
        ),
        Recipe(
            product_id=4,
            ingredients=[{"ingredientId": "2", "amount": 0.15}, {"ingredientId": "5", "amount": 2}, {"ingredientId": "8", "amount": 0.1}],
            equipment=["1", "2", "3"],
            steps=[{"name": "Приготовление миндальной массы", "duration": 30, "equipment": "Миксер планетарный KitchenAid"}, {"name": "Формирование", "duration": 20, "equipment": "Кондитерская витрина"}, {"name": "Выпечка", "duration": 15, "equipment": "Печь конвекционная UNOX"}, {"name": "Охлаждение", "duration": 30, "equipment": "Холодильная камера Polair"}, {"name": "Сборка и начинка", "duration": 25, "equipment": "Кондитерская витрина"}],
        ),
    ]
    db.add_all(recipes)

    db.add_all(
        [
            Order(id=1, product_name="Торт Прага", quantity=2, due_date="2026-05-05", start_date="2026-05-03", status="Запланирован", created_at="2026-04-27"),
            Order(id=2, product_name="Чизкейк манго", quantity=1, due_date="2026-05-08", start_date=None, status="Запланирован", created_at="2026-04-27"),
        ]
    )
    db.add_all(
        [
            Operation(id=1, order_id=1, name="Замес теста", employee_id=1, equipment_id=1, start_time="2026-05-03T08:00:00", end_time="2026-05-03T08:30:00", product_name="Торт Прага"),
            Operation(id=2, order_id=1, name="Выпечка коржей", employee_id=1, equipment_id=2, start_time="2026-05-03T08:30:00", end_time="2026-05-03T09:15:00", product_name="Торт Прага"),
            Operation(id=3, order_id=1, name="Охлаждение", employee_id=1, equipment_id=3, start_time="2026-05-03T09:15:00", end_time="2026-05-03T10:15:00", product_name="Торт Прага"),
        ]
    )
    db.commit()

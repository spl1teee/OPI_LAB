from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import Employee, Equipment, Operation, Order, Product, Recipe


def recalculate_order_status(order: Order, db: Session) -> None:
    now = datetime.now()
    ops = db.query(Operation).filter(Operation.order_id == order.id).all()
    if not ops:
        order.status = "Запланирован"
        return

    starts = [datetime.fromisoformat(op.start_time) for op in ops]
    ends = [datetime.fromisoformat(op.end_time) for op in ops]

    if any(start <= now <= end for start, end in zip(starts, ends)):
        order.status = "В работе"
    elif all(end < now for end in ends):
        order.status = "Выполнен"
    else:
        order.status = "Запланирован"


def regenerate_order_operations(order: Order, db: Session) -> None:
    db.query(Operation).filter(Operation.order_id == order.id).delete()

    product = db.query(Product).filter(Product.name == order.product_name).first()
    if not product:
        return
    recipe = db.query(Recipe).filter(Recipe.product_id == product.id).first()
    if not recipe:
        return

    employees = db.query(Employee).filter(Employee.role == "Кондитер").order_by(Employee.id).all()
    if not employees:
        employees = db.query(Employee).order_by(Employee.id).all()
    equipment_rows = db.query(Equipment).order_by(Equipment.id).all()
    equipment_by_id = {str(eq.id): eq for eq in equipment_rows}

    if not employees or not equipment_rows:
        return

    now = datetime.now()
    start_date = datetime.fromisoformat(order.start_date) if order.start_date else now
    current = start_date.replace(hour=8, minute=0, second=0, microsecond=0)
    if start_date.date() == now.date():
        current = now.replace(second=0, microsecond=0)

    # Основной шаг планирования: для каждого этапа выбираем доступного исполнителя и оборудование.
    for idx, step in enumerate(recipe.steps):
        duration = max(1, int(step.get("duration", 30)))
        employee = employees[idx % len(employees)]

        recipe_equipment_id = None
        recipe_equipment = recipe.equipment if isinstance(recipe.equipment, list) else []
        if recipe_equipment:
            recipe_equipment_id = str(recipe_equipment[idx % len(recipe_equipment)])
        equipment = equipment_by_id.get(recipe_equipment_id) if recipe_equipment_id else equipment_rows[idx % len(equipment_rows)]
        if equipment is None:
            equipment = equipment_rows[idx % len(equipment_rows)]

        op = Operation(
            order_id=order.id,
            name=step.get("name", f"Этап {idx + 1}"),
            employee_id=employee.id,
            equipment_id=equipment.id,
            start_time=current.isoformat(),
            end_time=(current + timedelta(minutes=duration)).isoformat(),
            product_name=order.product_name,
        )
        db.add(op)
        current = current + timedelta(minutes=duration)

    db.flush()
    recalculate_order_status(order, db)


def sync_resource_statuses(db: Session) -> None:
    now = datetime.now()
    employees = db.query(Employee).all()
    equipment_rows = db.query(Equipment).all()
    operations = db.query(Operation).all()

    active_ops = []
    for op in operations:
        start = datetime.fromisoformat(op.start_time)
        end = datetime.fromisoformat(op.end_time)
        if start <= now <= end:
            active_ops.append(op)

    busy_employee_ids = {op.employee_id for op in active_ops}
    busy_equipment_ids = {op.equipment_id for op in active_ops}

    for employee in employees:
        employee_ops = [op for op in operations if op.employee_id == employee.id]
        total_minutes = 0
        for op in employee_ops:
            start = datetime.fromisoformat(op.start_time)
            end = datetime.fromisoformat(op.end_time)
            total_minutes += max(0, int((end - start).total_seconds() / 60))
        employee.workload = min(100, int((total_minutes / 480) * 100)) if total_minutes > 0 else 0
        employee.status = "Работает" if employee.id in busy_employee_ids else "Свободен"

    for eq in equipment_rows:
        if eq.status == "На ремонте":
            continue
        eq.status = "Работает" if eq.id in busy_equipment_ids else "Свободно"


def run_planning(db: Session) -> dict:
    """Перезапускает планирование для всех заказов, кроме завершенных."""
    orders = db.query(Order).order_by(Order.id).all()
    planned = 0
    for order in orders:
        if order.status == "Выполнен":
            continue
        regenerate_order_operations(order, db)
        planned += 1

    sync_resource_statuses(db)
    db.commit()
    return {"plannedOrders": planned}

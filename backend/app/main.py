from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Employee, Equipment, Ingredient, Operation, Order, Product, Recipe
from .schemas import (
    EmployeeCreate,
    EmployeeOut,
    EquipmentOut,
    IngredientCreate,
    IngredientOut,
    IngredientReceive,
    LoginRequest,
    OperationOut,
    OrderCreate,
    OrderOut,
    OrderUpdate,
    ProductOut,
    RecipeOut,
    StatusUpdate,
)
from .seed import seed_data
from .planning import run_planning

app = FastAPI(title="Confectionery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed_data(db)


def map_ingredient(i: Ingredient) -> IngredientOut:
    return IngredientOut(
        id=str(i.id),
        name=i.name,
        unit=i.unit,
        currentStock=i.current_stock,
        shelfLife=i.shelf_life,
        expiryDate=i.expiry_date,
        criticalThreshold=i.critical_threshold,
    )


def map_order(o: Order) -> OrderOut:
    return OrderOut(
        id=str(o.id),
        productName=o.product_name,
        quantity=o.quantity,
        dueDate=o.due_date,
        startDate=o.start_date,
        status=o.status,
        createdAt=o.created_at,
    )


def map_operation(op: Operation) -> OperationOut:
    return OperationOut(
        id=str(op.id),
        orderId=str(op.order_id),
        name=op.name,
        employeeId=str(op.employee_id),
        equipmentId=str(op.equipment_id),
        startTime=op.start_time,
        endTime=op.end_time,
        productName=op.product_name,
    )


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


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    return {"token": "demo-token", "username": payload.username}


@app.get("/api/ingredients", response_model=list[IngredientOut])
def get_ingredients(db: Session = Depends(get_db)):
    return [map_ingredient(i) for i in db.query(Ingredient).order_by(Ingredient.id).all()]


@app.post("/api/ingredients", response_model=IngredientOut)
def create_ingredient(payload: IngredientCreate, db: Session = Depends(get_db)):
    item = Ingredient(
        name=payload.name,
        unit=payload.unit,
        shelf_life=payload.shelfLife,
        current_stock=0,
        critical_threshold=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return map_ingredient(item)


@app.post("/api/ingredients/{ingredient_id}/receive", response_model=IngredientOut)
def receive_ingredient(ingredient_id: int, payload: IngredientReceive, db: Session = Depends(get_db)):
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    receive_date = datetime.fromisoformat(payload.date)
    expiry = receive_date + timedelta(days=ingredient.shelf_life)

    ingredient.current_stock += payload.quantity
    ingredient.expiry_date = expiry.date().isoformat()
    db.commit()
    db.refresh(ingredient)
    return map_ingredient(ingredient)


@app.get("/api/equipment", response_model=list[EquipmentOut])
def get_equipment(db: Session = Depends(get_db)):
    sync_resource_statuses(db)
    db.commit()
    rows = db.query(Equipment).order_by(Equipment.id).all()
    return [EquipmentOut(id=str(i.id), name=i.name, type=i.type, status=i.status) for i in rows]


@app.patch("/api/equipment/{equipment_id}/status", response_model=EquipmentOut)
def update_equipment_status(equipment_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    row = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Equipment not found")
    row.status = payload.status
    db.commit()
    db.refresh(row)
    return EquipmentOut(id=str(row.id), name=row.name, type=row.type, status=row.status)


@app.delete("/api/equipment/{equipment_id}")
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    row = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Equipment not found")

    db.query(Operation).filter(Operation.equipment_id == equipment_id).delete()
    db.delete(row)
    orders = db.query(Order).all()
    for order in orders:
        recalculate_order_status(order, db)
    db.commit()
    return {"ok": True}


@app.get("/api/employees", response_model=list[EmployeeOut])
def get_employees(db: Session = Depends(get_db)):
    sync_resource_statuses(db)
    db.commit()
    rows = db.query(Employee).order_by(Employee.id).all()
    return [EmployeeOut(id=str(i.id), name=i.name, role=i.role, status=i.status, workload=i.workload) for i in rows]


@app.post("/api/employees", response_model=EmployeeOut)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    row = Employee(name=payload.name, role=payload.role, status="Свободен", workload=0)
    db.add(row)
    db.commit()
    db.refresh(row)
    return EmployeeOut(id=str(row.id), name=row.name, role=row.role, status=row.status, workload=row.workload)


@app.patch("/api/employees/{employee_id}/status", response_model=EmployeeOut)
def update_employee_status(employee_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    row = db.query(Employee).filter(Employee.id == employee_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    row.status = payload.status
    db.commit()
    db.refresh(row)
    return EmployeeOut(id=str(row.id), name=row.name, role=row.role, status=row.status, workload=row.workload)


@app.delete("/api/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    row = db.query(Employee).filter(Employee.id == employee_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.query(Operation).filter(Operation.employee_id == employee_id).delete()
    db.delete(row)
    orders = db.query(Order).all()
    for order in orders:
        recalculate_order_status(order, db)
    db.commit()
    return {"ok": True}


@app.get("/api/products", response_model=list[ProductOut])
def get_products(db: Session = Depends(get_db)):
    rows = db.query(Product).order_by(Product.id).all()
    return [ProductOut(id=str(p.id), name=p.name) for p in rows]


@app.get("/api/recipes", response_model=list[RecipeOut])
def get_recipes(db: Session = Depends(get_db)):
    rows = db.query(Recipe).order_by(Recipe.product_id).all()
    return [RecipeOut(productId=str(r.product_id), ingredients=r.ingredients, equipment=r.equipment, steps=r.steps) for r in rows]


@app.get("/api/orders", response_model=list[OrderOut])
def get_orders(db: Session = Depends(get_db)):
    rows = db.query(Order).order_by(Order.id).all()
    sync_resource_statuses(db)
    for order in rows:
        recalculate_order_status(order, db)
    db.commit()
    return [map_order(o) for o in rows]


@app.post("/api/orders", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = Order(
        product_name=payload.productName,
        quantity=payload.quantity,
        due_date=payload.dueDate,
        start_date=payload.startDate,
        status="Запланирован",
        created_at=datetime.now().date().isoformat(),
    )
    db.add(order)
    db.flush()
    regenerate_order_operations(order, db)
    db.commit()
    db.refresh(order)
    return map_order(order)


@app.put("/api/orders/{order_id}", response_model=OrderOut)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.quantity = payload.quantity
    order.due_date = payload.dueDate
    order.start_date = payload.startDate
    regenerate_order_operations(order, db)
    db.commit()
    db.refresh(order)
    return map_order(order)


@app.delete("/api/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.query(Operation).filter(Operation.order_id == order_id).delete()
    db.delete(order)
    db.commit()
    return {"ok": True}


@app.get("/api/operations", response_model=list[OperationOut])
def get_operations(db: Session = Depends(get_db)):
    rows = db.query(Operation).order_by(Operation.id).all()
    return [map_operation(op) for op in rows]


@app.post("/api/planning/run")
def planning_run(db: Session = Depends(get_db)):
    return run_planning(db)


@app.get("/api/schedule/{date}", response_model=list[OperationOut])
def schedule_by_date(date: str, db: Session = Depends(get_db)):
    try:
        target = datetime.fromisoformat(date).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

    rows = db.query(Operation).order_by(Operation.start_time).all()
    filtered = []
    for op in rows:
        start = datetime.fromisoformat(op.start_time).date()
        if start == target:
            filtered.append(op)
    return [map_operation(op) for op in filtered]

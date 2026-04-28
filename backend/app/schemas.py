from pydantic import BaseModel


class IngredientBase(BaseModel):
    name: str
    unit: str
    currentStock: float
    shelfLife: int
    expiryDate: str | None = None
    criticalThreshold: float


class IngredientCreate(BaseModel):
    name: str
    unit: str
    shelfLife: int


class IngredientReceive(BaseModel):
    quantity: float
    date: str


class IngredientOut(IngredientBase):
    id: str


class EquipmentOut(BaseModel):
    id: str
    name: str
    type: str
    status: str


class EmployeeOut(BaseModel):
    id: str
    name: str
    role: str
    status: str
    workload: int


class EmployeeCreate(BaseModel):
    name: str
    role: str


class StatusUpdate(BaseModel):
    status: str


class ProductOut(BaseModel):
    id: str
    name: str


class RecipeOut(BaseModel):
    productId: str
    ingredients: list[dict]
    equipment: list[str]
    steps: list[dict]


class OrderBase(BaseModel):
    productName: str
    quantity: int
    dueDate: str
    startDate: str | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    quantity: int
    dueDate: str
    startDate: str | None = None


class OrderOut(OrderBase):
    id: str
    status: str
    createdAt: str


class OperationOut(BaseModel):
    id: str
    orderId: str
    name: str
    employeeId: str
    equipmentId: str
    startTime: str
    endTime: str
    productName: str


class LoginRequest(BaseModel):
    username: str
    password: str

const API = window.__API_URL || localStorage.getItem("API_URL") || "http://localhost:8000/api";
const state = {
  auth: false,
  page: "orders",
  calendarDate: new Date(),
  orders: [],
  ingredients: [],
  equipment: [],
  employees: [],
  products: [],
  recipes: [],
  operations: [],
};

const app = document.getElementById("app");

async function api(path, options = {}) {
  const r = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function fmtDate(v) {
  if (!v) return "—";
  return new Date(v).toLocaleDateString("ru-RU");
}

function isActiveOperation(operation, now = new Date()) {
  const start = new Date(operation.startTime);
  const end = new Date(operation.endTime);
  return now >= start && now <= end;
}

function getProductsInWork() {
  const active = state.operations.filter((op) => isActiveOperation(op));
  const unique = [...new Set(active.map((op) => op.productName))];
  return unique;
}

function render() {
  if (!state.auth) return renderLogin();
  app.innerHTML = `
    <div class="wrap">
      <div class="card between">
        <h2>Кондитерский цех</h2>
        <div class="tabs">
          ${["orders","warehouse","calendar","techcards","settings"].map(p => `<button class="tab ${state.page===p?"active":""}" data-nav="${p}">${({
            orders:"Заказы", warehouse:"Склад", calendar:"Календарь", techcards:"Техкарты", settings:"Настройки"
          })[p]}</button>`).join("")}
          <button class="secondary" data-logout="1">Выйти</button>
        </div>
      </div>
      <div id="page"></div>
    </div>
  `;
  document.querySelectorAll("[data-nav]").forEach(b => b.onclick = () => { state.page = b.dataset.nav; render(); });
  document.querySelector("[data-logout]").onclick = () => { state.auth = false; render(); };
  if (state.page === "orders") renderOrders();
  if (state.page === "warehouse") renderWarehouse();
  if (state.page === "calendar") renderCalendar();
  if (state.page === "techcards") renderTechCards();
  if (state.page === "settings") renderSettings();
}

function renderLogin() {
  app.innerHTML = `
    <div class="login">
      <div class="card">
        <h2>Вход</h2>
        <div class="row"><input id="u" placeholder="Логин / Email" /></div>
        <div class="row"><input id="p" placeholder="Пароль" type="password" /></div>
        <div class="row"><button id="login">Войти</button></div>
        <div id="msg" class="muted"></div>
      </div>
    </div>`;
  document.getElementById("login").onclick = async () => {
    const username = document.getElementById("u").value;
    const password = document.getElementById("p").value;
    try {
      await api("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
      state.auth = true;
      await loadAll();
      render();
    } catch {
      document.getElementById("msg").innerHTML = '<span class="err">Ошибка авторизации</span>';
    }
  };
}

function renderOrders() {
  const page = document.getElementById("page");
  const productsInWork = getProductsInWork();
  page.innerHTML = `
    <div class="grid-3">
      <div class="card">Всего заказов: <b>${state.orders.length}</b></div>
      <div class="card">В работе (по операциям сейчас): <b>${productsInWork.length}</b></div>
      <div class="card">Выполнено: <b>${state.orders.filter(o=>o.status==="Выполнен").length}</b></div>
    </div>
    <div class="card">
      <h3>Изделия в работе сейчас</h3>
      ${
        productsInWork.length
          ? `<div class="row">${productsInWork
              .map((p) => `<span class="badge green">${p}</span>`)
              .join("")}</div>`
          : `<div class="muted">Сейчас нет активных операций по изделиям</div>`
      }
    </div>
    <div class="card">
      <div class="between"><h3>Заказы</h3><button id="newOrder">Создать заказ</button></div>
      <table><thead><tr><th>ID</th><th>Изделие</th><th>Кол-во</th><th>Не позднее</th><th>Не ранее</th><th>Статус</th><th></th></tr></thead>
      <tbody>${state.orders.map(o=>`<tr>
        <td>${o.id}</td><td>${o.productName}</td><td>${o.quantity}</td><td>${fmtDate(o.dueDate)}</td><td>${fmtDate(o.startDate)}</td><td>${o.status}</td>
        <td><button class="secondary" data-edit="${o.id}">Изм.</button> <button class="danger" data-del="${o.id}">Удал.</button></td>
      </tr>`).join("")}</tbody></table>
    </div>
    <div id="orderForm" class="card hidden"></div>
  `;
  document.getElementById("newOrder").onclick = () => orderForm();
  page.querySelectorAll("[data-edit]").forEach(b => b.onclick = () => orderForm(state.orders.find(o => o.id === b.dataset.edit)));
  page.querySelectorAll("[data-del]").forEach(b => b.onclick = async () => {
    await api(`/orders/${b.dataset.del}`, { method: "DELETE" });
    await Promise.all([loadOrders(), loadOperations()]);
    renderOrders();
  });
}

function orderForm(order) {
  const host = document.getElementById("orderForm");
  host.classList.remove("hidden");
  host.innerHTML = `
    <h3>${order ? "Редактировать" : "Создать"} заказ</h3>
    <div class="row">
      <select id="op">${state.products.map(p => `<option ${order?.productName===p.name?"selected":""}>${p.name}</option>`).join("")}</select>
      <input id="oq" type="number" min="1" value="${order?.quantity || 1}" />
      <input id="od" type="date" value="${order?.dueDate || ""}" />
      <input id="os" type="date" value="${order?.startDate || ""}" />
      <button id="saveOrder">Сохранить</button>
    </div>
  `;
  document.getElementById("saveOrder").onclick = async () => {
    const payload = {
      productName: document.getElementById("op").value,
      quantity: Number(document.getElementById("oq").value),
      dueDate: document.getElementById("od").value,
      startDate: document.getElementById("os").value || undefined,
    };
    if (order) await api(`/orders/${order.id}`, { method: "PUT", body: JSON.stringify({ quantity: payload.quantity, dueDate: payload.dueDate, startDate: payload.startDate }) });
    else await api("/orders", { method: "POST", body: JSON.stringify(payload) });
    await Promise.all([loadOrders(), loadOperations()]);
    renderOrders();
  };
}

function renderWarehouse() {
  const page = document.getElementById("page");
  page.innerHTML = `
    <div class="card">
      <div class="between"><h3>Склад</h3><button id="newIng">Добавить ингредиент</button></div>
      <table><thead><tr><th>Название</th><th>Ед.</th><th>Остаток</th><th>Срок (дн.)</th><th>Годен до</th><th>Порог</th><th></th></tr></thead>
      <tbody>${state.ingredients.map(i=>`<tr>
        <td>${i.name}</td><td>${i.unit}</td><td>${i.currentStock}</td><td>${i.shelfLife}</td><td>${fmtDate(i.expiryDate)}</td><td>${i.criticalThreshold}</td>
        <td><button data-rec="${i.id}">Приход</button></td>
      </tr>`).join("")}</tbody></table>
    </div>
    <div id="ingForm" class="card hidden"></div>
  `;
  document.getElementById("newIng").onclick = () => {
    const f = document.getElementById("ingForm");
    f.classList.remove("hidden");
    f.innerHTML = `<h3>Новый ингредиент</h3><div class="row">
      <input id="in" placeholder="Название" /><input id="iu" placeholder="Единица" />
      <input id="is" type="number" placeholder="Срок дней" /><button id="saveIng">Сохранить</button></div>`;
    document.getElementById("saveIng").onclick = async () => {
      await api("/ingredients", { method: "POST", body: JSON.stringify({
        name: document.getElementById("in").value,
        unit: document.getElementById("iu").value,
        shelfLife: Number(document.getElementById("is").value),
      }) });
      await loadIngredients(); renderWarehouse();
    };
  };
  page.querySelectorAll("[data-rec]").forEach(b => b.onclick = () => receiveForm(b.dataset.rec));
}

function receiveForm(id) {
  const ing = state.ingredients.find(i => i.id === id);
  const f = document.getElementById("ingForm");
  f.classList.remove("hidden");
  f.innerHTML = `<h3>Приход: ${ing.name}</h3><div class="row">
    <input id="rq" type="number" step="0.01" placeholder="Количество" />
    <input id="rd" type="date" value="${new Date().toISOString().slice(0,10)}" />
    <button id="saveRec">Подтвердить</button></div>`;
  document.getElementById("saveRec").onclick = async () => {
    await api(`/ingredients/${id}/receive`, { method: "POST", body: JSON.stringify({
      quantity: Number(document.getElementById("rq").value),
      date: document.getElementById("rd").value,
    }) });
    await loadIngredients(); renderWarehouse();
  };
}

function renderCalendar() {
  const page = document.getElementById("page");
  const monthDate = new Date(state.calendarDate);
  monthDate.setDate(1);
  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  const monthLabel = monthDate.toLocaleDateString("ru-RU", { month: "long", year: "numeric" });
  const firstWeekday = (monthDate.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const opsByDay = {};
  state.operations.forEach((op) => {
    const d = new Date(op.startTime);
    if (d.getFullYear() === year && d.getMonth() === month) {
      const key = d.getDate();
      if (!opsByDay[key]) opsByDay[key] = [];
      opsByDay[key].push(op);
    }
  });

  const cells = [];
  for (let i = 0; i < firstWeekday; i += 1) {
    cells.push('<div class="cal-day empty"></div>');
  }
  for (let day = 1; day <= daysInMonth; day += 1) {
    const dayOps = opsByDay[day] || [];
    cells.push(`
      <div class="cal-day">
        <div class="cal-day-head">${day}</div>
        <div class="cal-events">
          ${dayOps
            .map((op) => {
              const employeeName = (state.employees.find((e) => e.id === op.employeeId) || {}).name || "—";
              return `<div class="cal-event ${isActiveOperation(op) ? "active" : ""}" title="${op.productName} | ${employeeName}">
                <div><b>${op.name}</b></div>
                <div class="muted">${op.productName}</div>
                <div class="muted">👤 ${employeeName}</div>
              </div>`;
            })
            .join("")}
        </div>
      </div>
    `);
  }

  page.innerHTML = `
    <div class="card">
      <div class="between">
        <h3>Календарь операций</h3>
        <div class="row">
          <button id="runPlanning">Запустить планирование</button>
          <button class="secondary" id="prevMonth">←</button>
          <b style="text-transform: capitalize;">${monthLabel}</b>
          <button class="secondary" id="nextMonth">→</button>
        </div>
      </div>
      <div class="cal-weekdays">
        <div>Пн</div><div>Вт</div><div>Ср</div><div>Чт</div><div>Пт</div><div>Сб</div><div>Вс</div>
      </div>
      <div class="calendar-grid">${cells.join("")}</div>
      <div class="muted" style="margin-top:8px;">Зелёным выделены операции, которые выполняются прямо сейчас.</div>
    </div>
  `;

  document.getElementById("prevMonth").onclick = () => {
    state.calendarDate = new Date(year, month - 1, 1);
    renderCalendar();
  };
  document.getElementById("nextMonth").onclick = () => {
    state.calendarDate = new Date(year, month + 1, 1);
    renderCalendar();
  };
  document.getElementById("runPlanning").onclick = async () => {
    try {
      await api("/planning/run", { method: "POST" });
      await Promise.all([loadOrders(), loadOperations(), loadEmployees(), loadEquipment()]);
      renderCalendar();
      alert("Планирование выполнено");
    } catch {
      alert("Ошибка запуска планирования");
    }
  };
}

function renderTechCards() {
  const page = document.getElementById("page");
  page.innerHTML = state.products.map(p => {
    const r = state.recipes.find(x => x.productId === p.id);
    if (!r) return "";
    return `<div class="card"><h3>${p.name}</h3>
      <p><b>Ингредиенты:</b></p>
      <ul>${r.ingredients.map(i => {
        const g = state.ingredients.find(x => x.id === i.ingredientId);
        return `<li>${g?.name || i.ingredientId}: ${i.amount} ${g?.unit || ""}</li>`;
      }).join("")}</ul>
      <p><b>Оборудование:</b> ${r.equipment.map(id => (state.equipment.find(e => e.id === id) || {}).name || id).join(", ")}</p>
      <p><b>Этапы:</b></p><ol>${r.steps.map(s => `<li>${s.name} (${s.duration} мин), ${s.equipment}</li>`).join("")}</ol>
    </div>`;
  }).join("");
}

function renderSettings() {
  const page = document.getElementById("page");
  page.innerHTML = `
    <div class="card">
      <div class="between"><h3>Сотрудники</h3><button id="newEmp">Добавить</button></div>
      <table><thead><tr><th>Имя</th><th>Роль</th><th>Статус</th><th>Изменить статус</th><th>Удаление</th></tr></thead>
      <tbody>${state.employees.map(e=>`<tr>
        <td>${e.name}</td><td>${e.role}</td><td>${e.status}</td>
        <td><select data-emp="${e.id}">
          <option value="Свободен" ${e.status==="Свободен"?"selected":""}>Свободен</option>
          <option value="Работает" ${e.status==="Работает"?"selected":""}>Работает</option>
        </select></td>
        <td><button class="danger" data-del-emp="${e.id}">Удалить</button></td>
      </tr>`).join("")}</tbody></table>
    </div>
    <div class="card">
      <h3>Оборудование</h3>
      <table><thead><tr><th>Название</th><th>Тип</th><th>Статус</th><th>Изменить статус</th><th>Удаление</th></tr></thead>
      <tbody>${state.equipment.map(e=>`<tr>
        <td>${e.name}</td><td>${e.type}</td><td>${e.status}</td>
        <td><select data-eq="${e.id}">
          <option value="Свободно" ${e.status==="Свободно"?"selected":""}>Свободно</option>
          <option value="Работает" ${e.status==="Работает"?"selected":""}>Работает</option>
          <option value="На ремонте" ${e.status==="На ремонте"?"selected":""}>На ремонте</option>
        </select></td>
        <td><button class="danger" data-del-eq="${e.id}">Удалить</button></td>
      </tr>`).join("")}</tbody></table>
    </div>
    <div id="empForm" class="card hidden"></div>
  `;
  document.getElementById("newEmp").onclick = () => {
    const f = document.getElementById("empForm");
    f.classList.remove("hidden");
    f.innerHTML = `<h3>Новый сотрудник</h3><div class="row">
      <input id="en" placeholder="Имя" />
      <select id="er"><option>Кондитер</option><option>Технолог</option><option>Менеджер</option></select>
      <button id="saveEmp">Сохранить</button></div>`;
    document.getElementById("saveEmp").onclick = async () => {
      await api("/employees", { method: "POST", body: JSON.stringify({
        name: document.getElementById("en").value,
        role: document.getElementById("er").value,
      }) });
      await loadEmployees(); renderSettings();
    };
  };
  page.querySelectorAll("[data-emp]").forEach(s => s.onchange = async () => {
    const employeeId = s.dataset.emp;
    const nextStatus = s.value;
    s.disabled = true;
    try {
      await api(`/employees/${employeeId}/status`, { method: "PATCH", body: JSON.stringify({ status: nextStatus }) });
      state.employees = state.employees.map((emp) =>
        emp.id === employeeId ? { ...emp, status: nextStatus } : emp
      );
      renderSettings();
    } catch (e) {
      alert("Не удалось обновить статус сотрудника");
      await loadEmployees();
      renderSettings();
    } finally {
      s.disabled = false;
    }
  });
  page.querySelectorAll("[data-eq]").forEach(s => s.onchange = async () => {
    const equipmentId = s.dataset.eq;
    const nextStatus = s.value;
    s.disabled = true;
    try {
      await api(`/equipment/${equipmentId}/status`, { method: "PATCH", body: JSON.stringify({ status: nextStatus }) });
      state.equipment = state.equipment.map((eq) =>
        eq.id === equipmentId ? { ...eq, status: nextStatus } : eq
      );
      renderSettings();
    } catch (e) {
      alert("Не удалось обновить статус оборудования");
      await loadEquipment();
      renderSettings();
    } finally {
      s.disabled = false;
    }
  });
  page.querySelectorAll("[data-del-emp]").forEach((btn) => (btn.onclick = async () => {
    if (!confirm("Удалить сотрудника? Связанные операции будут удалены.")) return;
    try {
      await api(`/employees/${btn.dataset.delEmp}`, { method: "DELETE" });
      await Promise.all([loadEmployees(), loadOperations(), loadOrders()]);
      renderSettings();
    } catch {
      alert("Не удалось удалить сотрудника");
    }
  }));
  page.querySelectorAll("[data-del-eq]").forEach((btn) => (btn.onclick = async () => {
    if (!confirm("Удалить оборудование? Связанные операции будут удалены.")) return;
    try {
      await api(`/equipment/${btn.dataset.delEq}`, { method: "DELETE" });
      await Promise.all([loadEquipment(), loadOperations(), loadOrders()]);
      renderSettings();
    } catch {
      alert("Не удалось удалить оборудование");
    }
  }));
}

async function loadOrders() { state.orders = await api("/orders"); }
async function loadIngredients() { state.ingredients = await api("/ingredients"); }
async function loadEquipment() { state.equipment = await api("/equipment"); }
async function loadEmployees() { state.employees = await api("/employees"); }
async function loadProducts() { state.products = await api("/products"); }
async function loadRecipes() { state.recipes = await api("/recipes"); }
async function loadOperations() { state.operations = await api("/operations"); }

async function loadAll() {
  await Promise.all([loadOrders(), loadIngredients(), loadEquipment(), loadEmployees(), loadProducts(), loadRecipes(), loadOperations()]);
}

render();

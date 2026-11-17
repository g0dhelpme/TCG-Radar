const products = [
  { id: 1, name: "Destined Rivals Elite Trainer Box", type: "ETB", shop: "Alza.cz", price: 1_199, stock: true, checked: "před 8 min", url: "https://www.alza.cz/" },
  { id: 2, name: "Journey Together Booster Bundle", type: "Booster Bundle", shop: "Smarty.cz", price: 849, stock: true, checked: "před 12 min", url: "https://www.smarty.cz/" },
  { id: 3, name: "Prismatic Evolutions Elite Trainer Box", type: "ETB", shop: "Xzone.cz", price: 1_590, stock: false, checked: "před 18 min", url: "https://www.xzone.cz/" },
  { id: 4, name: "Surging Sparks Booster Bundle", type: "Booster Bundle", shop: "Tolarie.cz", price: 990, stock: true, checked: "před 24 min", url: "https://www.tolarie.cz/" },
  { id: 5, name: "151 Elite Trainer Box", type: "ETB", shop: "PokéObchod.cz", price: 2_490, stock: false, checked: "před 31 min", url: "https://pokeobchod.cz/" },
  { id: 6, name: "Temporal Forces Booster Bundle", type: "Booster Bundle", shop: "Alza.cz", price: 799, stock: true, checked: "před 42 min", url: "https://www.alza.cz/" },
];

const state = {
  stock: "all",
  type: "all",
  sort: "price",
  search: "",
  watched: JSON.parse(localStorage.getItem("tcg-radar-watched") || "[]"),
  targets: JSON.parse(localStorage.getItem("tcg-radar-targets") || "{}"),
};
const czk = new Intl.NumberFormat("cs-CZ", { style: "currency", currency: "CZK", maximumFractionDigits: 0 });
const $ = (selector) => document.querySelector(selector);

function save() {
  localStorage.setItem("tcg-radar-watched", JSON.stringify(state.watched));
  localStorage.setItem("tcg-radar-targets", JSON.stringify(state.targets));
}

function filteredProducts() {
  return products.filter((product) => {
    const text = `${product.name} ${product.shop}`.toLocaleLowerCase("cs");
    const matchesSearch = text.includes(state.search.toLocaleLowerCase("cs"));
    const matchesStock = state.stock === "all" || (state.stock === "in-stock" && product.stock) ||
      (state.stock === "watching" && state.watched.includes(product.id));
    return matchesSearch && matchesStock && (state.type === "all" || product.type === state.type);
  }).sort((a, b) => state.sort === "name" ? a.name.localeCompare(b.name) :
    state.sort === "recent" ? a.id - b.id : a.price - b.price);
}

function render() {
  const visible = filteredProducts();
  $("#product-count").textContent = products.length;
  $("#in-stock-count").textContent = products.filter((product) => product.stock).length;
  $("#watched-count").textContent = state.watched.length;
  $("#products").innerHTML = visible.map((product) => {
    const watching = state.watched.includes(product.id);
    const target = state.targets[product.id] || "";
    const targetHit = target && product.price <= Number(target);
    return `<article class="card">
      <div class="card-top"><span class="tag">${product.type}</span><span class="status ${product.stock ? "available" : "sold"}">${product.stock ? "● SKLADEM" : "○ VYPRODÁNO"}</span></div>
      <h2>${product.name}</h2><span class="shop">${product.shop} · kontrola ${product.checked}</span>
      <div class="price-row"><span class="price">${czk.format(product.price)} <small>vč. DPH</small></span></div>
      ${watching ? `<label class="target">HLÍDAT POD <input class="target-input" data-id="${product.id}" type="number" min="0" step="1" value="${target}" placeholder="cena Kč"></label>` : ""}
      ${targetHit ? `<div class="notice" style="margin:12px 0 0;padding:7px 10px;font-size:11px">⚡ Cena je pod limitem</div>` : ""}
      <div class="card-actions"><button class="watch ${watching ? "is-watched" : ""}" data-watch="${product.id}">${watching ? "✓ Sleduji" : "+ Sledovat"}</button><a class="buy ${product.stock ? "" : "disabled"}" href="${product.stock ? product.url : "#"}" target="_blank" rel="noopener">${product.stock ? "Do obchodu ↗" : "Není skladem"}</a></div>
    </article>`;
  }).join("");
  $("#empty").hidden = visible.length > 0;
}

document.addEventListener("click", (event) => {
  const watch = event.target.closest("[data-watch]");
  if (!watch) return;
  const id = Number(watch.dataset.watch);
  state.watched = state.watched.includes(id) ? state.watched.filter((item) => item !== id) : [...state.watched, id];
  save(); render();
});
document.addEventListener("change", (event) => {
  if (!event.target.matches(".target-input")) return;
  const id = event.target.dataset.id;
  if (event.target.value) state.targets[id] = Number(event.target.value); else delete state.targets[id];
  save(); render();
});
$("#search").addEventListener("input", (event) => { state.search = event.target.value; render(); });
$("#type-filter").addEventListener("change", (event) => { state.type = event.target.value; render(); });
$("#sort").addEventListener("change", (event) => { state.sort = event.target.value; render(); });
document.querySelectorAll("[data-stock]").forEach((button) => button.addEventListener("click", () => {
  state.stock = button.dataset.stock;
  document.querySelectorAll("[data-stock]").forEach((item) => item.classList.toggle("active", item === button));
  render();
}));
render();

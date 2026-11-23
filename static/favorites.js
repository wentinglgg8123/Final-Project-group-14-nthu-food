const prefix = "nthu-food:favorite:";
const changeEvent = "nthu-food:favorites-changed";
const mapsPrefix = "https://www.google.com/maps/search/?";

function parseFavorite(value) {
  try {
    const item = JSON.parse(value);
    if (typeof item?.id === "string" && typeof item.name === "string" &&
        typeof item.location === "string" && Number.isFinite(item.savedAt)) {
      return item;
    }
  } catch {
    // A malformed entry does not affect the other favorites.
  }
  return null;
}

function isFavorite(id) {
  try {
    return parseFavorite(localStorage.getItem(prefix + id))?.id === id;
  } catch {
    return false;
  }
}

function readFavorites() {
  const favorites = [];
  try {
    for (let index = 0; index < localStorage.length; index++) {
      const key = localStorage.key(index);
      if (!key?.startsWith(prefix)) continue;
      const item = parseFavorite(localStorage.getItem(key));
      if (item && key === prefix + item.id) favorites.push(item);
    }
  } catch {
    return favorites;
  }
  return favorites.sort((a, b) => b.savedAt - a.savedAt || a.id.localeCompare(b.id));
}

function updateFavorite(item, saved, status) {
  try {
    const key = prefix + item.id;
    if (saved) {
      localStorage.setItem(key, JSON.stringify({ ...item, savedAt: Date.now() }));
    } else {
      localStorage.removeItem(key);
    }
  } catch {
    status.textContent = "瀏覽器無法更新收藏，請確認網站資料儲存功能已開啟。";
    return;
  }
  status.textContent = "";
  window.dispatchEvent(new CustomEvent(changeEvent, { detail: item.id }));
}

function renderList(content, status) {
  const favorites = readFavorites();
  if (favorites.length === 0) {
    const prompt = document.createElement("p");
    prompt.className = "favorite-empty";
    prompt.textContent = "還沒有收藏。點餐廳的星號就能加入。";
    content.replaceChildren(prompt);
    return;
  }
  const list = document.createElement("ul");
  list.className = "favorite-list";
  for (const item of favorites) {
    const row = document.createElement("li");
    const details = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = item.name;
    if (typeof item.url === "string" && item.url.startsWith(mapsPrefix)) {
      const link = document.createElement("a");
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.append(name);
      details.append(link);
    } else {
      details.append(name);
    }
    const location = document.createElement("span");
    location.textContent = item.location;
    details.append(location);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "favorite-toggle";
    remove.setAttribute("aria-label", `取消收藏 ${item.name}`);
    remove.title = "取消收藏";
    remove.textContent = "★";
    remove.onclick = () => updateFavorite(item, false, status);
    row.append(details, remove);
    list.append(row);
  }
  content.replaceChildren(list);
}

function renderDrawFilter(content, ids, setStateValue) {
  const label = document.createElement("label");
  label.className = "favorite-draw-filter";
  const toggle = document.createElement("input");
  toggle.type = "checkbox";
  toggle.setAttribute("role", "switch");
  toggle.checked = ids !== null;
  label.append(toggle, "只抽我的最愛");
  content.append(label);
  let last = JSON.stringify(ids);
  const sync = () => {
    const next = toggle.checked ? readFavorites().map(item => item.id).sort() : null;
    const signature = JSON.stringify(next);
    if (signature === last) return;
    last = signature;
    setStateValue("ids", next);
  };
  toggle.onchange = sync;
  return sync;
}

export default function ({ parentElement, data, setStateValue }) {
  const root = parentElement.querySelector(".restaurant-favorites");
  const content = document.createElement("div");
  const status = document.createElement("p");
  status.className = "favorite-storage-status";
  status.setAttribute("role", "status");
  root.replaceChildren(content, status);

  const item = data?.restaurant;
  let refresh;
  if (item) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "favorite-toggle";
    button.setAttribute("aria-label", `收藏 ${item.name}`);
    button.onclick = () => updateFavorite(item, !isFavorite(item.id), status);
    content.append(button);
    refresh = () => {
      const saved = isFavorite(item.id);
      button.setAttribute("aria-pressed", String(saved));
      button.textContent = saved ? "★ 已收藏" : "☆ 收藏";
    };
  } else if (data?.drawFilter) {
    refresh = renderDrawFilter(content, data.ids, setStateValue);
  } else {
    refresh = () => renderList(content, status);
  }

  const onChange = (event) => {
    if (!item || event.detail === item.id) refresh();
  };
  const onStorage = (event) => {
    if (event.key === null || (item ? event.key === prefix + item.id : event.key.startsWith(prefix))) {
      refresh();
    }
  };
  refresh();
  window.addEventListener(changeEvent, onChange);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(changeEvent, onChange);
    window.removeEventListener("storage", onStorage);
  };
}

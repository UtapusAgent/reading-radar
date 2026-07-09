const APP={"name":"Reading Radar","category":"Reading tracker","description":"Track books, reading state, notes, and ratings.","features":["Book CRUD","Status filters","Quote notes","Rating summary"]};
const $ = (selector) => document.querySelector(selector);
let records = [];
let editing = null;
let query = "";

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "content-type": "application/json" }, ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || response.statusText);
  return data;
}

const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));

function payload() {
  return {
    title: $("#title").value,
    details: $("#details").value,
    status: $("#status").value,
    tag: $("#tag").value,
    due_date: $("#due_date").value,
  };
}

function fill(record) {
  editing = record.id;
  $("#title").value = record.title;
  $("#details").value = record.details;
  $("#status").value = record.status;
  $("#tag").value = record.tag;
  $("#due_date").value = record.due_date;
  $("#save").textContent = "Update";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetForm() {
  editing = null;
  $("#record-form").reset();
  $("#save").textContent = "Save";
}

async function saveRecord(event) {
  event.preventDefault();
  await api(editing ? "/api/records/" + editing : "/api/records", {
    method: editing ? "PUT" : "POST",
    body: JSON.stringify(payload()),
  });
  resetForm();
  await load();
}

async function removeRecord(id) {
  await api("/api/records/" + id, { method: "DELETE" });
  await load();
}

async function load() {
  records = await api("/api/records");
  render();
}

function filtered() {
  const term = query.toLowerCase();
  return records.filter((record) => [record.title, record.details, record.status, record.tag, record.due_date].join(" ").toLowerCase().includes(term));
}

function render() {
  const list = filtered();
  $("#count").textContent = records.length + " records";
  $("#records").innerHTML = list.map(card).join("") || '<p class="empty">No records match this view.</p>';
}

function card(record) {
  return '<article class="record"><div><span class="status">'+esc(record.status)+'</span><h3>'+esc(record.title)+'</h3><p>'+esc(record.details)+'</p><dl><div><dt>Tag</dt><dd>'+esc(record.tag || "none")+'</dd></div><div><dt>Due</dt><dd>'+esc(record.due_date || "not set")+'</dd></div></dl></div><div class="actions"><button onclick="fillById('+record.id+')">Edit</button><button class="danger" onclick="removeRecord('+record.id+')">Delete</button></div></article>';
}

function fillById(id) {
  fill(records.find((record) => record.id === id));
}

function exportJson() {
  const blob = new Blob([JSON.stringify(records, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = APP.name.toLowerCase().replaceAll(" ", "-") + "-export.json";
  link.click();
  URL.revokeObjectURL(url);
}

window.fillById = fillById;
window.removeRecord = removeRecord;
$("#app-title").textContent = APP.name;
$("#app-desc").textContent = APP.description;
$("#feature-list").innerHTML = APP.features.map((feature) => "<li>" + esc(feature) + "</li>").join("");
$("#record-form").addEventListener("submit", saveRecord);
$("#clear").addEventListener("click", resetForm);
$("#search").addEventListener("input", (event) => { query = event.target.value; render(); });
$("#export").addEventListener("click", exportJson);
load();

/**
 * Minimal notes app: storage via Anna harness; summarize via tools.invoke only.
 */
const TOOL_ID = "tool-dev-mini-notes";
const STORAGE_KEY = "mini-notes:notes_v1";

function parseDoc(raw) {
  if (raw == null || raw === "") return { notes: [], nextOrder: 1 };
  try {
    const v = typeof raw === "string" ? JSON.parse(raw) : raw;
    if (!v || typeof v !== "object") return { notes: [], nextOrder: 1 };
    const notes = Array.isArray(v.notes) ? v.notes : [];
    const nextOrder = typeof v.nextOrder === "number" && v.nextOrder > 0 ? v.nextOrder : 1;
    return { notes, nextOrder };
  } catch {
    return { notes: [], nextOrder: 1 };
  }
}

function unwrapToolResult(out) {
  if (out && typeof out === "object" && "success" in out) {
    if (!out.success) throw new Error(out.error || "tool_failed");
    return out.data && typeof out.data === "object" ? out.data : {};
  }
  return out && typeof out === "object" ? out : {};
}

async function loadDoc(anna) {
  const raw = await anna.storage.get({ key: STORAGE_KEY });
  return parseDoc(raw && raw.value != null ? raw.value : raw);
}

async function saveDoc(anna, doc) {
  const payload = JSON.stringify(doc);
  await anna.storage.set({ key: STORAGE_KEY, value: payload });
}

function formatTs(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toLocaleString();
}

async function main() {
  const input = document.getElementById("note-input");
  const listEl = document.getElementById("note-list");
  const btnSave = document.getElementById("btn-save");
  const btnSummarize = document.getElementById("btn-summarize");
  const summaryOut = document.getElementById("summary-out");
  const banner = document.getElementById("banner");

  if (!input || !listEl || !btnSave || !btnSummarize || !summaryOut) return;

  let anna;
  try {
    anna = await AnnaAppRuntime.connect();
  } catch (e) {
    banner.textContent = "独立预览：缺少 wid/t，无法使用 Anna 存储与工具。";
    return;
  }

  await anna.window.set_title({ title: "最小笔记 (mini-notes)" });
  banner.textContent = "已连接 Anna harness（mini-notes）。";

  async function render() {
    const doc = await loadDoc(anna);
    listEl.innerHTML = "";
    const sorted = [...doc.notes].sort((a, b) => (a.order || 0) - (b.order || 0));
    if (sorted.length === 0) {
      const li = document.createElement("li");
      li.className = "note";
      li.textContent = "暂无笔记。";
      listEl.appendChild(li);
      return;
    }
    for (const n of sorted) {
      const li = document.createElement("li");
      li.className = "note";
      li.dataset.id = n.id;
      li.innerHTML = `
        <div class="meta">顺序 #${escapeHtml(String(n.order))} · ${escapeHtml(formatTs(n.createdAt))}</div>
        <div class="text"></div>
        <div class="actions"><button type="button" class="danger" data-action="del">删除</button></div>
      `;
      li.querySelector(".text").textContent = n.text ?? "";
      li.querySelector('[data-action="del"]').addEventListener("click", async () => {
        const doc2 = await loadDoc(anna);
        doc2.notes = doc2.notes.filter((x) => x.id !== n.id);
        await saveDoc(anna, doc2);
        await render();
      });
      listEl.appendChild(li);
    }
  }

  btnSave.addEventListener("click", async () => {
    const text = (input.value || "").trim();
    if (!text) return;
    const doc = await loadDoc(anna);
    const id = crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(36).slice(2);
    const createdAt = new Date().toISOString();
    const order = doc.nextOrder;
    doc.notes.push({ id, text, order, createdAt });
    doc.nextOrder = order + 1;
    await saveDoc(anna, doc);
    input.value = "";
    await render();
  });

  btnSummarize.addEventListener("click", async () => {
    summaryOut.textContent = "生成中…";
    try {
      const doc = await loadDoc(anna);
      const sorted = [...doc.notes].sort((a, b) => (a.order || 0) - (b.order || 0));
      const raw = await anna.tools.invoke({
        tool_id: TOOL_ID,
        method: "summarize",
        args: { notes: sorted },
      });
      const data = unwrapToolResult(raw);
      summaryOut.textContent = data.summary != null ? String(data.summary) : JSON.stringify(raw, null, 2);
    } catch (e) {
      summaryOut.textContent = "错误: " + (e && e.message ? e.message : String(e));
    }
  });

  await render();
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

main();

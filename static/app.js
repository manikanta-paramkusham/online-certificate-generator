function looksLikeDate(s) {
  return /^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}$/.test(s);
}

document.getElementById("createForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const company = document.getElementById("company").value.trim();
  const title = document.getElementById("title").value.trim();
  const template = document.querySelector('input[name="template"]:checked').value;
  const lines = document.getElementById("students").value.trim().split("\n");

  const students = lines
    .map((line) => {
      const parts = line.split(",").map((p) => p.trim());
      if (!parts[0]) return null;
      if (parts.length === 2 && looksLikeDate(parts[1])) {
        return { name: parts[0], course: "", date: parts[1] };
      }
      return { name: parts[0], course: parts[1] || "", date: parts[2] || "" };
    })
    .filter(Boolean);

  if (!students.length) {
    alert("Add at least one student.");
    return;
  }

  const btn = document.getElementById("submitBtn");
  btn.disabled = true;
  btn.textContent = "Generating...";

  try {
    const res = await fetch("/api/batches", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_name: company, title, template, students }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to create certificates");

    showResults(data.certificates, data.count);
  } catch (err) {
    alert(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate Certificates";
  }
});

let lastResults = [];

function showResults(certs, count) {
  lastResults = certs;
  const section = document.getElementById("results");
  const tbody = document.querySelector("#linksTable tbody");
  const countEl = document.getElementById("resultCount");
  tbody.innerHTML = "";

  const base = window.location.origin;
  countEl.textContent = count || certs.length;

  certs.forEach((c) => {
    const url = base + c.link;
    const tr = document.createElement("tr");

    const nameTd = document.createElement("td");
    nameTd.textContent = c.student_name;

    const idTd = document.createElement("td");
    const code = document.createElement("code");
    code.textContent = c.unique_id;
    idTd.appendChild(code);

    const linkTd = document.createElement("td");
    const a = document.createElement("a");
    a.href = c.link;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = url;
    linkTd.appendChild(a);

    const copyTd = document.createElement("td");
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.textContent = "Copy";
    copyBtn.addEventListener("click", () => copyText(url, copyBtn));
    copyTd.appendChild(copyBtn);

    tr.append(nameTd, idTd, linkTd, copyTd);
    tbody.appendChild(tr);
  });

  section.classList.remove("hidden");
  section.scrollIntoView({ behavior: "smooth" });
}

async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    const original = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = original; }, 1500);
  } catch {
    alert("Could not copy. Please copy manually.");
  }
}

document.getElementById("copyAll").addEventListener("click", async () => {
  const base = window.location.origin;
  const text = lastResults
    .map((c) => `${c.student_name}\t${c.unique_id}\t${base + c.link}`)
    .join("\n");
  try {
    await navigator.clipboard.writeText(text);
    alert("All links copied!");
  } catch {
    alert("Could not copy. Use Download CSV instead.");
  }
});

document.getElementById("downloadCsv").addEventListener("click", () => {
  const base = window.location.origin;
  const rows = [["Student", "Unique ID", "Link"]];
  lastResults.forEach((c) => {
    rows.push([c.student_name, c.unique_id, base + c.link]);
  });
  const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "certificates.csv";
  a.click();
  URL.revokeObjectURL(a.href);
});

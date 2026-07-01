// ===========================================
// Certificate Generator
// Manual Entry + CSV Upload
// Part 1
// ===========================================

let lastResults = [];
let csvStudents = [];

const form = document.getElementById("createForm");
const manualSection = document.getElementById("manualSection");
const csvSection = document.getElementById("csvSection");

const manualRadio = document.querySelector(
    'input[name="inputMethod"][value="manual"]'
);

const csvRadio = document.querySelector(
    'input[name="inputMethod"][value="csv"]'
);

const csvFile = document.getElementById("csvFile");
const selectedFile = document.getElementById("selectedFile");
const csvPreview = document.getElementById("csvPreview");

// ===========================================
// Show / Hide Sections
// ===========================================

function updateInputMethod() {

    if (manualRadio.checked) {

        manualSection.classList.remove("hidden");
        csvSection.classList.add("hidden");

    } else {

        csvSection.classList.remove("hidden");
        manualSection.classList.add("hidden");

    }

}

manualRadio.addEventListener("change", updateInputMethod);
csvRadio.addEventListener("change", updateInputMethod);

updateInputMethod();

// ===========================================
// Helpers
// ===========================================

function looksLikeDate(value) {

    return /^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}$/.test(value);

}

// ===========================================
// Manual Parser
// ===========================================

function getManualStudents() {

    const text = document
        .getElementById("students")
        .value
        .trim();

    if (!text)
        return [];

    return text
        .split("\n")
        .map(line => {

            const parts = line
                .split(",")
                .map(p => p.trim());

            if (!parts[0])
                return null;

            if (
                parts.length === 2 &&
                looksLikeDate(parts[1])
            ) {

                return {

                    name: parts[0],
                    course: "",
                    date: parts[1]

                };

            }

            return {

                name: parts[0],
                course: parts[1] || "",
                date: parts[2] || ""

            };

        })
        .filter(Boolean);

}

// ===========================================
// CSV Reader
// ===========================================

csvFile.addEventListener("change", function () {

    csvStudents = [];

    csvPreview.innerHTML = "";

    if (!this.files.length) {

        selectedFile.textContent = "No file selected";

        return;

    }

    const file = this.files[0];

    selectedFile.textContent = file.name;

    const reader = new FileReader();

    reader.onload = function (e) {

        const text = e.target.result;

        parseCSV(text);

    };

    reader.readAsText(file);

});

// ===========================================
// Parse CSV
// ===========================================

function parseCSV(text) {

    const rows = text
        .trim()
        .split(/\r?\n/);

    if (rows.length <= 1) {

        alert("CSV file is empty.");

        return;

    }

    csvStudents = [];

    for (let i = 1; i < rows.length; i++) {

        const cols = rows[i]
            .split(",")
            .map(c => c.trim());

        if (!cols[0])
            continue;

        csvStudents.push({

            name: cols[0],
            course: cols[1] || "",
            date: cols[2] || ""

        });

    }

    showCSVPreview();

}

// ===========================================
// Preview CSV
// ===========================================

function showCSVPreview() {

    if (!csvStudents.length) {

        csvPreview.classList.add("hidden");

        return;

    }

    let html = `

        <h4>CSV Preview</h4>

        <div class="csv-count">

            ${csvStudents.length} Students Loaded

        </div>

        <table>

            <thead>

                <tr>

                    <th>Name</th>
                    <th>Course</th>
                    <th>Date</th>

                </tr>

            </thead>

            <tbody>

    `;

    csvStudents.forEach(student => {

        html += `

            <tr>

                <td>${student.name}</td>

                <td>${student.course}</td>

                <td>${student.date}</td>

            </tr>

        `;

    });

    html += `

            </tbody>

        </table>

    `;

    csvPreview.innerHTML = html;

    csvPreview.classList.remove("hidden");

}

// ===========================================
// Form Submit
// ===========================================

form.addEventListener("submit", async function (e) {

    e.preventDefault();

    const company = document
        .getElementById("company")
        .value
        .trim();

    const title = document
        .getElementById("title")
        .value
        .trim();

    const template = document.querySelector(
        'input[name="template"]:checked'
    ).value;

    let students = [];

    if (manualRadio.checked) {

        students = getManualStudents();

    } else {

        students = csvStudents;

    }

    if (!students.length) {

        alert("Please add at least one student.");

        return;

    }

    const submitBtn = document.getElementById("submitBtn");

    submitBtn.disabled = true;

    submitBtn.textContent = "Generating...";

    try {

        const response = await fetch("/api/batches", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                company_name: company,

                title: title,

                template: template,

                students: students

            })

        });

        const data = await response.json();

        if (!response.ok) {

          throw new Error(
              data.error || "Failed to generate certificates."
          );

      }

      showResults(
          data.certificates,
          data.count
      );

  }
  catch (err) {

      alert(err.message);

  }
  finally {

      submitBtn.disabled = false;

      submitBtn.textContent =
          "Generate Certificates";

  }

});

// ===========================================
// Show Results
// ===========================================

function showResults(certs, count) {

  lastResults = certs;

  const section =
      document.getElementById("results");

  const tbody =
      document.querySelector(
          "#linksTable tbody"
      );

  const countEl =
      document.getElementById(
          "resultCount"
      );

  tbody.innerHTML = "";

  countEl.textContent =
      count || certs.length;

  const base =
      window.location.origin;

  certs.forEach(cert => {

      const tr =
          document.createElement("tr");

      const url =
          base + cert.link;

      tr.innerHTML = `

          <td>

              ${cert.student_name}

          </td>

          <td>

              <code>

                  ${cert.unique_id}

              </code>

          </td>

          <td>

              <a
                  href="${cert.link}"
                  target="_blank"
              >

                  ${url}

              </a>

          </td>

          <td>

              <button
                  type="button"
                  class="copyBtn"
              >

                  Copy

              </button>

          </td>

      `;

      tr.querySelector(".copyBtn")
          .addEventListener("click", () => {

              copyText(
                  url,
                  tr.querySelector(".copyBtn")
              );

          });

      tbody.appendChild(tr);

  });

  section.classList.remove("hidden");

  section.scrollIntoView({

      behavior: "smooth"

  });

}

// ===========================================
// Copy Single Link
// ===========================================

async function copyText(text, btn) {

  try {

      await navigator.clipboard.writeText(text);

      const original =
          btn.textContent;

      btn.textContent = "Copied!";

      setTimeout(() => {

          btn.textContent =
              original;

      }, 1500);

  }
  catch {

      alert(
          "Unable to copy."
      );

  }

}

// ===========================================
// Copy All Links
// ===========================================

document
.getElementById("copyAll")
.addEventListener("click", async () => {

  if (!lastResults.length) {

      alert(
          "Nothing to copy."
      );

      return;

  }

  const base =
      window.location.origin;

  const text =
      lastResults
      .map(cert =>

          `${cert.student_name}\t${cert.unique_id}\t${base}${cert.link}`

      )
      .join("\n");

  try {

      await navigator
          .clipboard
          .writeText(text);

      alert(
          "All links copied."
      );

  }
  catch {

      alert(
          "Copy failed."
      );

  }

});

// ===========================================
// Download CSV
// ===========================================

document
.getElementById("downloadCsv")
.addEventListener("click", () => {

  if (!lastResults.length) {

      alert(
          "No certificates generated."
      );

      return;

  }

  const base =
      window.location.origin;

  const rows = [

      [

          "Student",

          "Unique ID",

          "Link"

      ]

  ];

  lastResults.forEach(cert => {

      rows.push([

          cert.student_name,

          cert.unique_id,

          base + cert.link

      ]);

  });

  const csv =
      rows
      .map(row =>

          row
          .map(value =>

              `"${String(value)
                  .replace(/"/g,'""')}"`

          )
          .join(",")

      )
      .join("\n");

  const blob =
      new Blob(

          [csv],

          {

              type:"text/csv"

          }

      );

  const a =
      document.createElement("a");

  a.href =
      URL.createObjectURL(blob);

  a.download =
      "certificates.csv";

  a.click();

  URL.revokeObjectURL(a.href);

});

// ===========================================
// End of File
// ===========================================


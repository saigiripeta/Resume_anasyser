// app/static/script.js

const form = document.getElementById("analyzeForm");
const fileInput = document.getElementById("resumeFile");
const targetDeptInput = document.getElementById("targetDepartment");
const statusDiv = document.getElementById("status");

const resultsContainer = document.getElementById("resultsContainer");
const outputText = document.getElementById("output");
const extractedTextArea = document.getElementById("extractedText");

// Summary table cells
const resName = document.getElementById("resName");
const resEmail = document.getElementById("resEmail");
const resPhone = document.getElementById("resPhone");
const resLocation = document.getElementById("resLocation");
const resOrg = document.getElementById("resOrg");

const resTeachExp = document.getElementById("resTeachExp");
const resIndExp = document.getElementById("resIndExp");
const resOtherExp = document.getElementById("resOtherExp");
const resTotalExp = document.getElementById("resTotalExp");

const resHasPhd = document.getElementById("resHasPhd");
const resPhdStartYear = document.getElementById("resPhdStartYear");
const resPhdEndYear = document.getElementById("resPhdEndYear");
const resHighestDegree = document.getElementById("resHighestDegree");
const resDepartment = document.getElementById("resDepartment");
const resScore = document.getElementById("resScore");

const resPubTotal = document.getElementById("resPubTotal");
const resArticles = document.getElementById("resArticles");
const resBooks = document.getElementById("resBooks");
const resConfs = document.getElementById("resConfs");

// Degree details
const degreesTable = document.getElementById("degreesTable").querySelector("tbody");
const resDegreesList = document.getElementById("resDegreesList");
const resFieldsList = document.getElementById("resFieldsList");

function setStatus(message, isError = false) {
  statusDiv.textContent = message;
  statusDiv.className = isError ? "status error" : "status";
}

function safe(value) {
  if (value === null || value === undefined || value === "") return "-";
  return value;
}

function formatYears(value) {
  if (value === null || value === undefined) return "-";
  return value + " years";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!fileInput.files || fileInput.files.length === 0) {
    alert("Please select a resume file.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const targetDepartment = targetDeptInput.value.trim();
  if (targetDepartment) {
    formData.append("target_department", targetDepartment);
  }

  setStatus("Analyzing resume... Please wait.");
  resultsContainer.style.display = "none";
  outputText.value = "";
  extractedTextArea.value = "";

  try {
    const response = await fetch("/analyze-resume", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const detail = data.detail || JSON.stringify(data);
      setStatus("Error: " + detail, true);
      return;
    }

    setStatus("Analysis completed.");
    resultsContainer.style.display = "block";

    // Summary: personal info
    resName.textContent = safe(data.name);
    resEmail.textContent = safe(data.email);
    resPhone.textContent = safe(data.phone);
    resLocation.textContent = safe(data.current_location);
    resOrg.textContent = safe(data.current_organization);

    // Experience
    resTeachExp.textContent = formatYears(data.teaching_experience_years);
    resIndExp.textContent = formatYears(data.industry_experience_years);
    resOtherExp.textContent = formatYears(data.other_experience_years);
    resTotalExp.textContent = formatYears(data.total_experience_years);

    // PhD / degrees
    resHasPhd.textContent = data.has_phd ? "Yes" : "No";
    resPhdStartYear.textContent = safe(data.phd_start_year);
    resPhdEndYear.textContent = safe(data.phd_end_year);
    resHighestDegree.textContent = safe(data.highest_degree);
    resDepartment.textContent = safe(data.department);
    resScore.textContent = safe(data.score);

    // Publications
    resPubTotal.textContent = safe(data.publications_total_count);
    resArticles.textContent = safe(data.research_articles_count);
    resBooks.textContent = safe(data.books_count);
    resConfs.textContent = safe(data.conference_papers_count);

    // Degree details table
    degreesTable.innerHTML = "";
    (data.degrees_info || []).forEach((deg) => {
      const tr = document.createElement("tr");

      const tdDeg = document.createElement("td");
      tdDeg.textContent = safe(deg.degree_type);
      tr.appendChild(tdDeg);

      const tdField = document.createElement("td");
      tdField.textContent = safe(deg.field_of_study);
      tr.appendChild(tdField);

      const tdInst = document.createElement("td");
      tdInst.textContent = safe(deg.institution);
      tr.appendChild(tdInst);

      const tdStart = document.createElement("td");
      tdStart.textContent = safe(deg.start_year);
      tr.appendChild(tdStart);

      const tdEnd = document.createElement("td");
      tdEnd.textContent = safe(deg.end_year);
      tr.appendChild(tdEnd);

      const tdStatus = document.createElement("td");
      tdStatus.textContent = safe(deg.status);
      tr.appendChild(tdStatus);

      degreesTable.appendChild(tr);
    });

    // Detected degree types list
    resDegreesList.innerHTML = "";
    (data.degrees_detected || []).forEach((deg) => {
      const li = document.createElement("li");
      li.textContent = deg;
      resDegreesList.appendChild(li);
    });

    // Fields of study list
    resFieldsList.innerHTML = "";
    (data.fields_of_study || []).forEach((field) => {
      const li = document.createElement("li");
      li.textContent = field;
      resFieldsList.appendChild(li);
    });

    // Raw JSON & extracted text
    outputText.value = JSON.stringify(data, null, 2);
    extractedTextArea.value = data.text_preview || "";

  } catch (err) {
    console.error(err);
    setStatus("Unexpected error: " + err, true);
  }
});
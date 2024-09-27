// Populate country dropdown
const countries = [
  "United States",
  "United Kingdom",
  "India",
  "Canada",
  "Australia",
  "China",
  "Japan",
  "Germany",
  "France",
  "Brazil",
  // Add more country names as needed
];

const countrySelect = document.getElementById("country");
countries.forEach((country) => {
  const option = document.createElement("option");
  option.value = country;
  option.textContent = country;
  countrySelect.appendChild(option);
});

function updateSymptoms() {
  const symptomsByCategory = {
    Heart: ["Pain", "Burning", "Breathing Problem", "Palpitations"],
    Legs: ["Rashes", "Itching", "Pain", "Swelling"],
    Head: ["Headache", "Dizziness", "Migraine", "Blurred Vision"],
    Back: ["Lower Back Pain", "Stiffness", "Numbness", "Sciatica"],
    Chest: ["Chest Pain", "Coughing", "Shortness of Breath", "Wheezing"],
    // Add more categories and symptoms as needed
  };

  const category = document.getElementById("disease-category").value;
  const symptomOptions = document.getElementById("symptom-options");

  // Clear previous options
  symptomOptions.innerHTML = "";

  if (category && symptomsByCategory[category]) {
    symptomsByCategory[category].forEach((symptom) => {
      const option = document.createElement("option");
      option.value = symptom;
      option.textContent = symptom;
      symptomOptions.appendChild(option);
    });
  }
}

function goBack() {
  window.history.back();
}

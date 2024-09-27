import express from "express";
import session from "express-session";
import bodyParser from "body-parser";
import PDFDocument from "pdfkit";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const app = express();
const port = 3000;
const __dirname = dirname(fileURLToPath(import.meta.url));

// Middleware Setup
app.use(express.static(join(__dirname, "public"))); // Serves static files
app.set("view engine", "ejs"); // Sets the view engine to EJS
app.set("views", join(__dirname, "views")); // Defines the views directory
app.use(bodyParser.urlencoded({ extended: true })); // Parses URL-encoded bodies

// Session Middleware
app.use(
  session({
    secret: "your-secret-key", // Replace with a strong secret key
    resave: false,
    saveUninitialized: true,
  })
);

// Route: Home Page
app.get("/", (req, res) => {
  res.render("index");
});

// Route: About Page
app.get("/about", (req, res) => {
  res.render("about");
});

// Route: Symptom Question Pages
app.get("/symptoms/:id", (req, res) => {
  const { id } = req.params;
  res.render(`symptoms${id}`);
});

app.post("/submit", (req, res) => {
  const {
    name,
    age,
    country,
    "symptom-area": symptomArea,
    symptoms,
  } = req.body;

  // Ensure symptoms is an array
  const symptomsArray = Array.isArray(symptoms) ? symptoms : [symptoms];

  // Store data in session
  req.session.formData = {
    name,
    age,
    country,
    "symptom-area": symptomArea,
    symptoms: symptomsArray,
  };

  // Redirect to the appropriate symptom page based on the symptom area
  res.redirect(`/symptoms/${symptomArea}`);
});

//head section

// Route to handle form submission for the 20 questions
app.post("/head-submit-form", (req, res) => {
  const questions = {};

  // Collect all 20 questions from the form
  for (let i = 1; i <= 20; i++) {
    questions[`question${i}`] = req.body[`question${i}`] || "no"; // Default to "no" if not provided
  }

  // Retrieve existing form data from the session
  let formData = req.session.formData || {};

  // Add the answers to the new questions to the session data
  formData = {
    ...formData,
    ...questions,
  };

  // Update the session with the new data
  req.session.formData = formData;

  // Debugging: Log form data
  console.log("Form Data Submitted:", formData);

  // Redirect to the result page
  res.redirect("/head-result");
});

// Route to display results
app.get("/head-result", (req, res) => {
  const formData = req.session.formData;

  if (!formData) {
    return res.redirect("/"); // Redirect back to the home page if no data in session
  }

  // Debugging: Log form data
  console.log("Form Data in Result:", formData);

  // Define the questions related to each condition
  const conditions = {
    Migraine: [1, 2, 3, 4, 6, 7, 13, 14, 16, 17],
    TensionHeadache: [1, 2, 4, 6, 7, 15, 16],
    ClusterHeadache: [1, 2, 4, 5, 6, 11, 13, 14, 17, 19],
    SinusHeadache: [1, 3, 5, 15, 16, 17],
    VestibularMigraine: [1, 7, 8, 10, 12, 13, 14, 15, 16, 18],
    CervicogenicHeadache: [1, 2, 4, 6, 7, 8, 14, 15],
    PostTraumaticHeadache: [1, 7, 8, 11, 14, 15, 16, 17, 18],
  };

  // Initialize result object
  let results = {};

  // Calculate the percentage of "yes" answers for each condition
  for (let condition in conditions) {
    let relevantQuestions = conditions[condition];
    let totalQuestions = relevantQuestions.length;

    // Debugging: Log the relevant questions for the condition
    console.log(`Condition: ${condition}`);
    console.log(`Relevant Questions: ${relevantQuestions}`);

    // Count the number of "yes" answers
    let yesCount = relevantQuestions.reduce((count, q) => {
      const answer = formData[`question${q}`];
      // Ensure comparison is case-insensitive
      const isYes = answer && answer.trim().toLowerCase() === "yes";
      console.log(`Question ${q} Answer: ${answer}`); // Log each question's answer
      return count + (isYes ? 1 : 0);
    }, 0);

    let percentage = (yesCount / totalQuestions) * 100;

    // Debugging output
    console.log(`Yes Count: ${yesCount}`);
    console.log(`Total Questions: ${totalQuestions}`);
    console.log(`Percentage: ${percentage.toFixed(2)}%`);

    // Determine risk level based on percentage
    if (percentage >= 70) {
      results[condition] = "High";
    } else if (percentage >= 43) {
      results[condition] = "Moderate";
    } else {
      results[condition] = "Low";
    }
  }

  // Save results in session for later use in PDF
  req.session.results = results;

  // Render the result page with form data and risk levels
  res.render("head-result", { formData, results });
});

// Route to handle PDF download
app.get("/head-download-pdf", (req, res) => {
  const formData = req.session.formData || {}; // Retrieve form data from the session
  const results = req.session.results || {}; // Retrieve results from the session

  const doc = new PDFDocument({ margin: 50 }); // Initialize the PDFDocument

  // Set headers for PDF download
  res.setHeader("Content-Disposition", "attachment; filename=head-results.pdf");
  res.setHeader("Content-Type", "application/pdf");

  doc.pipe(res);

  // Add title to the PDF
  doc.fontSize(20).text("Form Submission Result", { align: "center" });
  doc.moveDown(2);

  // Add basic user details to the PDF
  doc.fontSize(14).text(`Name: ${formData.name || "Not provided"}`);
  doc.text(`Age: ${formData.age || "Not provided"}`);
  doc.text(`Country: ${formData.country || "Not provided"}`);
  doc.text(`Symptom Area: ${formData["symptom-area"] || "Not provided"}`);
  doc.text(
    `Symptoms: ${
      Array.isArray(formData.symptoms)
        ? formData.symptoms.length
          ? formData.symptoms.join(", ")
          : "None provided"
        : formData.symptoms || "None provided"
    }`
  );
  doc.moveDown(2);

  // Define the list of questions (related to headache and dizziness)
  const questions = [
    "Do you frequently experience headaches?",
    "Are your headaches typically localized to one area of your head?",
    "Do you experience any visual disturbances (e.g., blurred vision) during your headaches?",
    "Do you have a history of migraine headaches?",
    "Are your headaches accompanied by nausea or vomiting?",
    "Do you experience light or sound sensitivity during your headaches?",
    "Have you noticed any changes in your headache pattern over time?",
    "Do you experience dizziness or vertigo along with your headaches?",
    "Do you often feel lightheaded or unsteady when standing up?",
    "Have you ever experienced a sudden onset of severe dizziness?",
    "Do you feel like the room is spinning when you are dizzy?",
    "Do you have a history of balance problems or coordination issues?",
    "Do you experience headaches that get worse with physical activity?",
    "Are your headaches triggered by certain foods or drinks?",
    "Do you experience a feeling of pressure or tightness in your head?",
    "Do you often feel dizzy when you are in a crowded or enclosed space?",
    "Have you had any recent head injuries or trauma?",
    "Do you experience headaches that wake you up from sleep?",
    "Do you have any history of high blood pressure or cardiovascular issues?",
    "Do you have a history of neurological disorders?",
  ];

  // Add questions and answers to the PDF
  questions.forEach((question, index) => {
    const answer = formData[`question${index + 1}`] || "Not answered";
    doc
      .fontSize(12)
      .font("Helvetica-Bold")
      .text(`Question ${index + 1}: ${question}`);
    doc.fontSize(12).font("Helvetica").text(`Answer: ${answer}`);
    doc.moveDown();
  });

  // Add a section for disease risk levels
  doc
    .fontSize(16)
    .font("Helvetica-Bold")
    .text("Risk Levels for Headache and Dizziness Conditions:");
  doc.moveDown();

  // Add disease and corresponding risk levels to the PDF
  for (let condition in results) {
    const riskLevel = results[condition];
    let color;

    // Color-coding based on risk level
    switch (riskLevel) {
      case "High":
        color = "red";
        break;
      case "Moderate":
        color = "orange";
        break;
      case "Low":
        color = "green";
        break;
      default:
        color = "black";
    }

    // Add disease and risk level to the PDF with appropriate color
    doc.fontSize(14).fillColor(color).text(`${condition}: ${riskLevel}`);
  }

  // End and send the PDF
  doc.end();
});

//chest section

app.post("/chest-submit-form", (req, res) => {
  const questions = {};

  // Collect all 20 questions from the form
  for (let i = 1; i <= 20; i++) {
    questions[`question${i}`] = req.body[`question${i}`] || "no"; // Default to "no" if not provided
  }

  // Retrieve existing form data from the session
  let formData = req.session.formData || {};

  // Add the answers to the new questions to the session data
  formData = {
    ...formData,
    ...questions,
  };

  // Update the session with the new data
  req.session.formData = formData;

  // Debugging: Log form data
  console.log("Form Data Submitted:", formData);

  // Redirect to the result page
  res.redirect("/chest-result");
});

// Route to display results
app.get("/chest-result", (req, res) => {
  const formData = req.session.formData;

  if (!formData) {
    return res.redirect("/"); // Redirect back to the home page if no data in session
  }

  // Debugging: Log form data
  console.log("Form Data in Result:", formData);

  const conditions = {
    Angina: [1, 4, 5, 7, 17],
    Pleuritis: [3, 10, 12, 13, 18],
    PulmonaryEmbolism: [3, 8, 11, 16, 19],
    Pneumonia: [3, 9, 14, 15, 18],
    ChronicObstructivePulmonaryDisease: [2, 6, 9, 10, 14],
    GastroesophagealRefluxDisease: [5, 7, 13, 16, 20],
    LungCancer: [3, 4, 6, 9, 15],
  };

  // Initialize result object
  let results = {};

  // Calculate the percentage of "yes" answers for each condition
  for (let condition in conditions) {
    let relevantQuestions = conditions[condition];
    let totalQuestions = relevantQuestions.length;

    // Debugging: Log the relevant questions for the condition
    console.log(`Condition: ${condition}`);
    console.log(`Relevant Questions: ${relevantQuestions}`);

    // Count the number of "yes" answers
    let yesCount = relevantQuestions.reduce((count, q) => {
      const answer = formData[`question${q}`];
      // Ensure comparison is case-insensitive
      const isYes = answer && answer.trim().toLowerCase() === "yes";
      console.log(`Question ${q} Answer: ${answer}`); // Log each question's answer
      return count + (isYes ? 1 : 0);
    }, 0);

    let percentage = (yesCount / totalQuestions) * 100;

    // Debugging output
    console.log(`Yes Count: ${yesCount}`);
    console.log(`Total Questions: ${totalQuestions}`);
    console.log(`Percentage: ${percentage.toFixed(2)}%`);

    // Determine risk level based on percentage
    if (percentage >= 70) {
      results[condition] = "High";
    } else if (percentage >= 45) {
      results[condition] = "Moderate";
    } else {
      results[condition] = "Low";
    }
  }

  // Save results in session for later use in PDF
  req.session.results = results;

  // Render the result page with form data and risk levels
  res.render("chest-result", { formData, results });
});

// Route to handle PDF download
app.get("/chest-download-pdf", (req, res) => {
  const formData = req.session.formData || {}; // Retrieve form data from the session
  const results = req.session.results || {}; // Retrieve results from the session

  const doc = new PDFDocument({ margin: 50 }); // Initialize the PDFDocument

  // Set headers for PDF download
  res.setHeader(
    "Content-Disposition",
    "attachment; filename=chest-results.pdf"
  );
  res.setHeader("Content-Type", "application/pdf");

  doc.pipe(res);

  // Add title to the PDF
  doc.fontSize(20).text("Form Submission Result", { align: "center" });
  doc.moveDown(2);

  // Add basic user details to the PDF
  doc.fontSize(14).text(`Name: ${formData.name || "Not provided"}`);
  doc.text(`Age: ${formData.age || "Not provided"}`);
  doc.text(`Country: ${formData.country || "Not provided"}`);
  doc.text(`Symptom Area: ${formData["symptom-area"] || "Not provided"}`);
  doc.text(
    `Symptoms: ${
      Array.isArray(formData.symptoms)
        ? formData.symptoms.length
          ? formData.symptoms.join(", ")
          : "None provided"
        : formData.symptoms || "None provided"
    }`
  );
  doc.moveDown(2);

  const questions = [
    "Do you experience chest pain or discomfort during physical activity?",
    "Is the chest pain sharp or stabbing?",
    "Do you feel pressure or tightness in your chest, as if something heavy is sitting on it?",
    "Does the pain radiate to your arms, neck, jaw, or back?",
    "Do you experience shortness of breath even with mild exertion?",
    "Do you often feel like you can't catch your breath while at rest?",
    "Do you experience palpitations (irregular heartbeats) or a racing heart?",
    "Have you ever fainted or felt lightheaded along with chest discomfort?",
    "Does your chest pain get worse when you take a deep breath or cough?",
    "Do you have a history of heart disease or cardiovascular issues in your family?",
    "Do you experience wheezing, coughing, or difficulty breathing at night?",
    "Have you noticed any swelling in your legs, ankles, or feet?",
    "Do you feel short of breath when lying down or have to prop yourself up with pillows to sleep?",
    "Have you ever been diagnosed with high blood pressure?",
    "Do you experience heartburn or indigestion-like symptoms along with chest pain?",
    "Do you have a history of smoking or are you currently a smoker?",
    "Have you been diagnosed with asthma or another respiratory condition?",
    "Do you experience sweating, nausea, or cold sweats along with chest discomfort?",
    "Does your chest pain improve with rest or after taking medication?",
    "Have you had any recent injuries or trauma to your chest?",
  ];

  // Add questions and answers to the PDF
  questions.forEach((question, index) => {
    const answer = formData[`question${index + 1}`] || "Not answered";
    doc
      .fontSize(12)
      .font("Helvetica-Bold")
      .text(`Question ${index + 1}: ${question}`);
    doc.fontSize(12).font("Helvetica").text(`Answer: ${answer}`);
    doc.moveDown();
  });

  // Add a section for disease risk levels
  doc
    .fontSize(16)
    .font("Helvetica-Bold")
    .text("Risk Levels for Chest Conditions:");
  doc.moveDown();

  // Add disease and corresponding risk levels to the PDF
  for (let condition in results) {
    const riskLevel = results[condition];
    let color;

    // Color-coding based on risk level
    switch (riskLevel) {
      case "High":
        color = "red";
        break;
      case "Moderate":
        color = "orange";
        break;
      case "Low":
        color = "green";
        break;
      default:
        color = "black";
    }

    // Add disease and risk level to the PDF with appropriate color
    doc.fontSize(14).fillColor(color).text(`${condition}: ${riskLevel}`);
  }

  // End and send the PDF
  doc.end();
});

//abdomen section

// Route to handle form submission for the 20 questions
app.post("/abdomen-submit-form", (req, res) => {
  const questions = {};

  // Collect all 20 questions from the form
  for (let i = 1; i <= 20; i++) {
    questions[`question${i}`] = req.body[`question${i}`] || "no"; // Default to "no" if not provided
  }

  // Retrieve existing form data from the session
  let formData = req.session.formData || {};

  // Add the answers to the new questions to the session data
  formData = {
    ...formData,
    ...questions,
  };

  // Update the session with the new data
  req.session.formData = formData;

  // Debugging: Log form data
  console.log("Form Data Submitted:", formData);

  // Redirect to the result page
  res.redirect("/abdomen-result");
});

// Route to display results
app.get("/abdomen-result", (req, res) => {
  const formData = req.session.formData;

  if (!formData) {
    return res.redirect("/"); // Redirect back to the home page if no data in session
  }

  // Debugging: Log form data
  console.log("Form Data in Result:", formData);

  // Define the questions related to each condition
  const conditions = {
    Gastroenteritis: [1, 4, 6, 8, 10], // Questions related to nausea, vomiting, diarrhea, and abdominal pain
    IrritableBowelSyndrome: [1, 2, 4, 6, 7], // Questions related to abdominal pain, bloating, gas, and bowel irregularities
    PepticUlcers: [1, 3, 5, 7, 8], // Questions related to abdominal pain, nausea, and vomiting
    Gallstones: [1, 3, 5, 6, 9], // Questions related to severe abdominal pain, nausea, and vomiting
    Appendicitis: [1, 2, 4, 5, 9], // Questions related to severe pain in the lower right abdomen, nausea, and vomiting

    CrohnsDisease: [1, 2, 4, 5, 7], // Questions related to diarrhea, abdominal pain, and weight loss
    FoodPoisoning: [1, 4, 6, 8, 9], // Questions related to nausea, vomiting, diarrhea, and abdominal cramping
  };

  // Initialize result object
  let results = {};

  // Calculate the percentage of "yes" answers for each condition
  for (let condition in conditions) {
    let relevantQuestions = conditions[condition];
    let totalQuestions = relevantQuestions.length;

    // Debugging: Log the relevant questions for the condition
    console.log(`Condition: ${condition}`);
    console.log(`Relevant Questions: ${relevantQuestions}`);

    // Count the number of "yes" answers
    let yesCount = relevantQuestions.reduce((count, q) => {
      const answer = formData[`question${q}`];
      // Ensure comparison is case-insensitive
      const isYes = answer && answer.trim().toLowerCase() === "yes";
      console.log(`Question ${q} Answer: ${answer}`); // Log each question's answer
      return count + (isYes ? 1 : 0);
    }, 0);

    let percentage = (yesCount / totalQuestions) * 100;

    // Debugging output
    console.log(`Yes Count: ${yesCount}`);
    console.log(`Total Questions: ${totalQuestions}`);
    console.log(`Percentage: ${percentage.toFixed(2)}%`);

    // Determine risk level based on percentage
    if (percentage >= 70) {
      results[condition] = "High";
    } else if (percentage >= 45) {
      results[condition] = "Moderate";
    } else {
      results[condition] = "Low";
    }
  }

  // Save results in session for later use in PDF
  req.session.results = results;

  // Render the result page with form data and risk levels
  res.render("abdomen-result", { formData, results });
});

// Route to handle PDF download
app.get("/abdomen-download-pdf", (req, res) => {
  const formData = req.session.formData || {}; // Retrieve form data from the session
  const results = req.session.results || {}; // Retrieve results from the session

  const doc = new PDFDocument({ margin: 50 }); // Initialize the PDFDocument

  // Set headers for PDF download
  res.setHeader(
    "Content-Disposition",
    "attachment; filename=abdomen-results.pdf"
  );
  res.setHeader("Content-Type", "application/pdf");

  doc.pipe(res);

  // Add title to the PDF
  doc.fontSize(20).text("Form Submission Result", { align: "center" });
  doc.moveDown(2);

  // Add basic user details to the PDF
  doc.fontSize(14).text(`Name: ${formData.name || "Not provided"}`);
  doc.text(`Age: ${formData.age || "Not provided"}`);
  doc.text(`Country: ${formData.country || "Not provided"}`);
  doc.text(`Symptom Area: ${formData["symptom-area"] || "Not provided"}`);
  doc.text(
    `Symptoms: ${
      Array.isArray(formData.symptoms)
        ? formData.symptoms.length
          ? formData.symptoms.join(", ")
          : "None provided"
        : formData.symptoms || "None provided"
    }`
  );
  doc.moveDown(2);

  // Define the list of questions (related to heart disease)
  const questions = [
    "Do you experience persistent or recurring abdominal pain?",
    "Is the abdominal pain localized to a specific area, such as the upper or lower abdomen?",
    "Do you often feel nauseous without any apparent cause?",
    "Have you had episodes of vomiting along with your abdominal discomfort?",
    "Do you experience diarrhea, either regularly or sporadically?",
    "Have you noticed blood in your stool or dark, tarry stools?",
    "Do you experience bloating or a feeling of fullness even after eating small meals?",
    "Have you experienced any unexplained weight loss recently?",
    "Does eating certain foods, such as dairy or gluten, trigger your symptoms?",
    "Do you have frequent episodes of heartburn or acid reflux?",
    "Does your abdominal pain worsen after eating or drinking?",
    "Do you have a history of stomach ulcers or gastritis?",
    "Have you experienced any changes in your bowel habits, such as constipation or diarrhea?",
    "Have you noticed a loss of appetite or disinterest in food?",
    "Do you feel abdominal pain when pressing on your stomach?",
    "Do you have a family history of gastrointestinal disorders such as Crohn’s disease or celiac disease?",
    "Have you traveled recently and experienced stomach problems upon returning?",
    "Do you experience abdominal pain or discomfort along with frequent urination or pain while urinating?",
    "Have you noticed any yellowing of your skin or eyes (jaundice) along with abdominal symptoms?",
    "Have you recently taken any medications or antibiotics that could have triggered your symptoms?",
  ];

  // Add questions and answers to the PDF
  questions.forEach((question, index) => {
    const answer = formData[`question${index + 1}`] || "Not answered";
    doc
      .fontSize(12)
      .font("Helvetica-Bold")
      .text(`Question ${index + 1}: ${question}`);
    doc.fontSize(12).font("Helvetica").text(`Answer: ${answer}`);
    doc.moveDown();
  });

  // Add a section for disease risk levels
  doc
    .fontSize(16)
    .font("Helvetica-Bold")
    .text("Risk Levels for Abdomen Conditions:");
  doc.moveDown();

  // Add disease and corresponding risk levels to the PDF
  for (let condition in results) {
    const riskLevel = results[condition];
    let color;

    // Color-coding based on risk level
    switch (riskLevel) {
      case "High":
        color = "red";
        break;
      case "Moderate":
        color = "orange";
        break;
      case "Low":
        color = "green";
        break;
      default:
        color = "black";
    }

    // Add disease and risk level to the PDF with appropriate color
    doc.fontSize(14).fillColor(color).text(`${condition}: ${riskLevel}`);
  }

  // End and send the PDF
  doc.end();
});

// arms section

// Route to handle form submission for the 20 questions
app.post("/arms-submit-form", (req, res) => {
  const questions = {};

  // Collect all 20 questions from the form
  for (let i = 1; i <= 20; i++) {
    questions[`question${i}`] = req.body[`question${i}`] || "no"; // Default to "no" if not provided
  }

  // Retrieve existing form data from the session
  let formData = req.session.formData || {};

  // Add the answers to the new questions to the session data
  formData = {
    ...formData,
    ...questions,
  };

  // Update the session with the new data
  req.session.formData = formData;

  // Debugging: Log form data
  console.log("Form Data Submitted:", formData);

  // Redirect to the result page
  res.redirect("/arms-result");
});

// Route to display results
app.get("/arms-result", (req, res) => {
  const formData = req.session.formData;

  if (!formData) {
    return res.redirect("/"); // Redirect back to the home page if no data in session
  }

  // Debugging: Log form data
  console.log("Form Data in Result:", formData);

  // Define the questions related to each condition
  const conditions = {
    PeripheralNeuropathy: [1, 2, 5, 8, 13], // Numbness, tingling, and pain in arms
    CarpalTunnelSyndrome: [2, 3, 4, 7, 11], // Pain, tingling, and swelling in arms/hands
    Tendonitis: [3, 5, 6, 10, 15], // Inflammation and pain in arms or shoulders
    ThoracicOutletSyndrome: [4, 6, 7, 12, 14], // Compression causing numbness and pain
    BrachialPlexusInjury: [1, 6, 9, 10, 17], // Nerve damage affecting the arms and shoulders
    Lymphedema: [12, 14, 18, 19, 20], // Swelling in arms due to lymphatic issues
    FrozenShoulder: [8, 10, 11, 16, 18], // Stiffness and pain in the shoulder joint
  };

  // Initialize result object
  let results = {};

  // Calculate the percentage of "yes" answers for each condition
  for (let condition in conditions) {
    let relevantQuestions = conditions[condition];
    let totalQuestions = relevantQuestions.length;

    // Debugging: Log the relevant questions for the condition
    console.log(`Condition: ${condition}`);
    console.log(`Relevant Questions: ${relevantQuestions}`);

    // Count the number of "yes" answers
    let yesCount = relevantQuestions.reduce((count, q) => {
      const answer = formData[`question${q}`];
      // Ensure comparison is case-insensitive
      const isYes = answer && answer.trim().toLowerCase() === "yes";
      console.log(`Question ${q} Answer: ${answer}`); // Log each question's answer
      return count + (isYes ? 1 : 0);
    }, 0);

    let percentage = (yesCount / totalQuestions) * 100;

    // Debugging output
    console.log(`Yes Count: ${yesCount}`);
    console.log(`Total Questions: ${totalQuestions}`);
    console.log(`Percentage: ${percentage.toFixed(2)}%`);

    // Determine risk level based on percentage
    if (percentage >= 70) {
      results[condition] = "High";
    } else if (percentage >= 45) {
      results[condition] = "Moderate";
    } else {
      results[condition] = "Low";
    }
  }

  // Save results in session for later use in PDF
  req.session.results = results;

  // Render the result page with form data and risk levels
  res.render("arms-result", { formData, results });
});

// Route to handle PDF download
app.get("/arms-download-pdf", (req, res) => {
  const formData = req.session.formData || {}; // Retrieve form data from the session
  const results = req.session.results || {}; // Retrieve results from the session

  const doc = new PDFDocument({ margin: 50 }); // Initialize the PDFDocument

  // Set headers for PDF download
  res.setHeader("Content-Disposition", "attachment; filename=arms-results.pdf");
  res.setHeader("Content-Type", "application/pdf");

  doc.pipe(res);

  // Add title to the PDF
  doc.fontSize(20).text("Form Submission Result", { align: "center" });
  doc.moveDown(2);

  // Add basic user details to the PDF
  doc.fontSize(14).text(`Name: ${formData.name || "Not provided"}`);
  doc.text(`Age: ${formData.age || "Not provided"}`);
  doc.text(`Country: ${formData.country || "Not provided"}`);
  doc.text(`Symptom Area: ${formData["symptom-area"] || "Not provided"}`);
  doc.text(
    `Symptoms: ${
      Array.isArray(formData.symptoms)
        ? formData.symptoms.length
          ? formData.symptoms.join(", ")
          : "None provided"
        : formData.symptoms || "None provided"
    }`
  );
  doc.moveDown(2);

  // Define the list of questions (related to heart disease)
  const questions = [
    "Do you experience pain in one or both of your arms?",
    "Is the arm pain sharp, dull, or throbbing?",
    "Do you feel tingling or numbness in your arms or hands?",
    "Is the numbness in your arms constant or does it come and go?",
    "Do you have difficulty moving or lifting your arms?",
    "Does your arm pain radiate from your neck or shoulders?",
    "Have you noticed any swelling in your arms, hands, or fingers?",
    "Do you experience arm weakness or a feeling of heaviness?",
    "Is the arm pain worse at night or while resting?",
    "Have you noticed any discoloration or bruising on your arms?",
    "Do you experience burning sensations in your arms or hands?",
    "Does repetitive motion, such as typing or lifting, aggravate your arm pain?",
    "Have you experienced any recent injuries or trauma to your arms?",
    "Do you experience arm pain after physical activity or exercise?",
    "Have you noticed a loss of grip strength in your hands?",
    "Does your arm pain get worse with cold or damp weather?",
    "Do you experience swelling in your arm after prolonged standing or sitting?",
    "Is your arm pain relieved by resting or applying ice?",
    "Do you feel tightness or stiffness in your arms or shoulders?",
    "Have you experienced any muscle spasms or cramping in your arms?",
  ];

  // Add questions and answers to the PDF
  questions.forEach((question, index) => {
    const answer = formData[`question${index + 1}`] || "Not answered";
    doc
      .fontSize(12)
      .font("Helvetica-Bold")
      .text(`Question ${index + 1}: ${question}`);
    doc.fontSize(12).font("Helvetica").text(`Answer: ${answer}`);
    doc.moveDown();
  });

  // Add a section for disease risk levels
  doc
    .fontSize(16)
    .font("Helvetica-Bold")
    .text("Risk Levels for Heart Conditions:");
  doc.moveDown();

  // Add disease and corresponding risk levels to the PDF
  for (let condition in results) {
    const riskLevel = results[condition];
    let color;

    // Color-coding based on risk level
    switch (riskLevel) {
      case "High":
        color = "red";
        break;
      case "Moderate":
        color = "orange";
        break;
      case "Low":
        color = "green";
        break;
      default:
        color = "black";
    }

    // Add disease and risk level to the PDF with appropriate color
    doc.fontSize(14).fillColor(color).text(`${condition}: ${riskLevel}`);
  }

  // End and send the PDF
  doc.end();
});

//heart section

// Route to handle form submission for the 20 questions
app.post("/heart-submit-form", (req, res) => {
  const questions = {};

  // Collect all 20 questions from the form
  for (let i = 1; i <= 20; i++) {
    questions[`question${i}`] = req.body[`question${i}`] || "no"; // Default to "no" if not provided
  }

  // Retrieve existing form data from the session
  let formData = req.session.formData || {};

  // Add the answers to the new questions to the session data
  formData = {
    ...formData,
    ...questions,
  };

  // Update the session with the new data
  req.session.formData = formData;

  // Debugging: Log form data
  console.log("Form Data Submitted:", formData);

  // Redirect to the result page
  res.redirect("/heart-result");
});

// Route to display results
app.get("/heart-result", (req, res) => {
  const formData = req.session.formData;

  if (!formData) {
    return res.redirect("/"); // Redirect back to the home page if no data in session
  }

  // Debugging: Log form data
  console.log("Form Data in Result:", formData);

  // Define the questions related to each condition
  const conditions = {
    CoronaryArteryDisease: [1, 3, 4, 5, 7],
    Hypertension: [2, 7, 12, 13, 15],
    HeartFailure: [1, 8, 14, 16, 18],
    Arrhythmias: [8, 16, 9, 11, 19],
    CholesterolIssues: [4, 13, 5, 7, 11],
    DiabetesAndCardiovascular: [9, 2, 4, 15, 19],
  };

  // Initialize result object
  let results = {};

  // Calculate the percentage of "yes" answers for each condition
  for (let condition in conditions) {
    let relevantQuestions = conditions[condition];
    let totalQuestions = relevantQuestions.length;

    // Debugging: Log the relevant questions for the condition
    console.log(`Condition: ${condition}`);
    console.log(`Relevant Questions: ${relevantQuestions}`);

    // Count the number of "yes" answers
    let yesCount = relevantQuestions.reduce((count, q) => {
      const answer = formData[`question${q}`];
      // Ensure comparison is case-insensitive
      const isYes = answer && answer.trim().toLowerCase() === "yes";
      console.log(`Question ${q} Answer: ${answer}`); // Log each question's answer
      return count + (isYes ? 1 : 0);
    }, 0);

    let percentage = (yesCount / totalQuestions) * 100;

    // Debugging output
    console.log(`Yes Count: ${yesCount}`);
    console.log(`Total Questions: ${totalQuestions}`);
    console.log(`Percentage: ${percentage.toFixed(2)}%`);

    // Determine risk level based on percentage
    if (percentage >= 70) {
      results[condition] = "High";
    } else if (percentage >= 45) {
      results[condition] = "Moderate";
    } else {
      results[condition] = "Low";
    }
  }

  // Save results in session for later use in PDF
  req.session.results = results;

  // Render the result page with form data and risk levels
  res.render("heart-result", { formData, results });
});

// Route to handle PDF download
app.get("/heart-download-pdf", (req, res) => {
  const formData = req.session.formData || {}; // Retrieve form data from the session
  const results = req.session.results || {}; // Retrieve results from the session

  const doc = new PDFDocument({ margin: 50 }); // Initialize the PDFDocument

  // Set headers for PDF download
  res.setHeader(
    "Content-Disposition",
    "attachment; filename=hearts-results.pdf"
  );
  res.setHeader("Content-Type", "application/pdf");

  doc.pipe(res);

  // Add title to the PDF
  doc.fontSize(20).text("Form Submission Result", { align: "center" });
  doc.moveDown(2);

  // Add basic user details to the PDF
  doc.fontSize(14).text(`Name: ${formData.name || "Not provided"}`);
  doc.text(`Age: ${formData.age || "Not provided"}`);
  doc.text(`Country: ${formData.country || "Not provided"}`);
  doc.text(`Symptom Area: ${formData["symptom-area"] || "Not provided"}`);
  doc.text(
    `Symptoms: ${
      Array.isArray(formData.symptoms)
        ? formData.symptoms.length
          ? formData.symptoms.join(", ")
          : "None provided"
        : formData.symptoms || "None provided"
    }`
  );
  doc.moveDown(2);

  // Define the list of questions (related to heart disease)
  const questions = [
    "Do you experience chest pain or discomfort during physical activity?",
    "Have you ever been diagnosed with high blood pressure?",
    "Do you often feel shortness of breath, even with mild exertion?",
    "Have you ever been told you have high cholesterol levels?",
    "Do you have a family history of heart disease or heart attacks?",
    "Do you smoke or have you smoked in the past?",
    "Do you feel fatigued or weak more often than usual?",
    "Do you experience irregular heartbeats or palpitations?",
    "Have you been diagnosed with diabetes or high blood sugar?",
    "Do you follow a sedentary lifestyle with little physical activity?",
    "Do you often feel dizzy or lightheaded?",
    "Are you overweight or obese based on your BMI?",
    "Do you consume a diet high in saturated fats and processed foods?",
    "Have you ever experienced swelling in your legs, ankles, or feet?",
    "Do you have trouble sleeping, or do you suffer from sleep apnea?",
    "Have you experienced a rapid or abnormal heartbeat recently?",
    "Do you experience nausea or cold sweats without apparent reason?",
    "Do you feel pressure or squeezing in your chest at times?",
    "Are you under constant stress or anxiety?",
    "Have you noticed any unexplained weight gain or fluid retention?",
  ];

  // Add questions and answers to the PDF
  questions.forEach((question, index) => {
    const answer = formData[`question${index + 1}`] || "Not answered";
    doc
      .fontSize(12)
      .font("Helvetica-Bold")
      .text(`Question ${index + 1}: ${question}`);
    doc.fontSize(12).font("Helvetica").text(`Answer: ${answer}`);
    doc.moveDown();
  });

  // Add a section for disease risk levels
  doc
    .fontSize(16)
    .font("Helvetica-Bold")
    .text("Risk Levels for Heart Conditions:");
  doc.moveDown();

  // Add disease and corresponding risk levels to the PDF
  for (let condition in results) {
    const riskLevel = results[condition];
    let color;

    // Color-coding based on risk level
    switch (riskLevel) {
      case "High":
        color = "red";
        break;
      case "Moderate":
        color = "orange";
        break;
      case "Low":
        color = "green";
        break;
      default:
        color = "black";
    }

    // Add disease and risk level to the PDF with appropriate color
    doc.fontSize(14).fillColor(color).text(`${condition}: ${riskLevel}`);
  }

  // End and send the PDF
  doc.end();
});

//legs section

// Route to handle form submission for the 20 questions
app.post("/legs-submit-form", (req, res) => {
  const questions = {};

  // Collect all 20 questions from the form
  for (let i = 1; i <= 20; i++) {
    questions[`question${i}`] = req.body[`question${i}`] || "no"; // Default to "no" if not provided
  }

  // Retrieve existing form data from the session
  let formData = req.session.formData || {};

  // Add the answers to the new questions to the session data
  formData = {
    ...formData,
    ...questions,
  };

  // Update the session with the new data
  req.session.formData = formData;

  // Debugging: Log form data
  console.log("Form Data Submitted:", formData);

  // Redirect to the result page
  res.redirect("/legs-result");
});

// Route to display results
app.get("/legs-result", (req, res) => {
  const formData = req.session.formData;

  if (!formData) {
    return res.redirect("/"); // Redirect back to the home page if no data in session
  }

  // Debugging: Log form data
  console.log("Form Data in Result:", formData);

  // Define the questions related to each condition
  const conditions = {
    AthleteFoot: [1, 2, 3, 4, 12, 15, 18],
    Onychomycosis: [5, 6, 7, 13, 14, 16],
    MoccasinTypeAthleteFoot: [2, 12, 13, 15, 18],
    InterdigitalTineaPedis: [1, 2, 3, 13, 14, 16],
    VesicularTineaPedis: [4, 1, 3, 13, 19],
    Candidiasis: [10, 11, 3, 13, 19],
    FungalHeelCracks: [8, 2, 13, 15],
  };

  // Initialize result object
  let results = {};

  // Calculate the percentage of "yes" answers for each condition
  for (let condition in conditions) {
    let relevantQuestions = conditions[condition];
    let totalQuestions = relevantQuestions.length;

    // Debugging: Log the relevant questions for the condition
    console.log(`Condition: ${condition}`);
    console.log(`Relevant Questions: ${relevantQuestions}`);

    // Count the number of "yes" answers
    let yesCount = relevantQuestions.reduce((count, q) => {
      const answer = formData[`question${q}`];
      // Ensure comparison is case-insensitive
      const isYes = answer && answer.trim().toLowerCase() === "yes";
      console.log(`Question ${q} Answer: ${answer}`); // Log each question's answer
      return count + (isYes ? 1 : 0);
    }, 0);

    let percentage = (yesCount / totalQuestions) * 100;

    // Debugging output
    console.log(`Yes Count: ${yesCount}`);
    console.log(`Total Questions: ${totalQuestions}`);
    console.log(`Percentage: ${percentage.toFixed(2)}%`);

    // Determine risk level based on percentage
    if (percentage >= 60) {
      results[condition] = "High";
    } else if (percentage >= 45) {
      results[condition] = "Moderate";
    } else {
      results[condition] = "Low";
    }
  }

  // Save results in session for later use in PDF
  req.session.results = results;

  // Render the result page with form data and risk levels
  res.render("legs-result", { formData, results });
});

// Route to handle PDF download
app.get("/legs-download-pdf", (req, res) => {
  const formData = req.session.formData || {}; // Retrieve form data from the session
  const results = req.session.results || {}; // Retrieve results from the session

  const doc = new PDFDocument({ margin: 50 }); // Initialize the PDFDocument

  // Set headers for PDF download
  res.setHeader("Content-Disposition", "attachment; filename=legs-results.pdf");
  res.setHeader("Content-Type", "application/pdf");

  doc.pipe(res);

  // Add title to the PDF
  doc.fontSize(20).text("Form Submission Result", { align: "center" });
  doc.moveDown(2);

  // Add basic user details to the PDF
  doc.fontSize(14).text(`Name: ${formData.name || "Not provided"}`);
  doc.text(`Age: ${formData.age || "Not provided"}`);
  doc.text(`Country: ${formData.country || "Not provided"}`);
  doc.text(`Symptom Area: ${formData["symptom-area"] || "Not provided"}`);
  doc.text(
    `Symptoms: ${
      Array.isArray(formData.symptoms)
        ? formData.symptoms.length
          ? formData.symptoms.join(", ")
          : "None provided"
        : formData.symptoms || "None provided"
    }`
  );
  doc.moveDown(2);

  // Define the list of questions (related to foot fungal diseases)
  const questions = [
    "Do you experience itching between your toes?",
    "Is the skin on your feet peeling or flaking?",
    "Do you have any redness or inflammation on the soles of your feet?",
    "Have you noticed any blisters or fluid-filled bumps on your feet?",
    "Are your toenails discolored (yellow, white, or brown)?",
    "Do your toenails appear thickened or brittle?",
    "Are your toenails separating from the nail bed?",
    "Do you have any cracked or painful skin on your heels?",
    "Is there a strong odor coming from your feet, even with regular washing?",
    "Do you often have moist, sweaty feet?",
    "Have you noticed any swelling or soreness in the areas between your toes?",
    "Do you have any scaly, dry patches on the soles of your feet?",
    "Is there any discomfort or pain when walking or wearing shoes?",
    "Do you have any white, macerated skin between your toes?",
    "Have you tried over-the-counter antifungal treatments? If so, did they help?",
    "Are the symptoms confined to one foot, or are both feet affected?",
    "Have you been in public places like locker rooms, pools, or communal showers recently?",
    "Do you frequently wear tight or non-breathable shoes?",
    "Do you have any underlying conditions like diabetes or a weakened immune system?",
    "Have you noticed any improvement or worsening of symptoms over time?",
  ];

  // Add questions and answers to the PDF
  questions.forEach((question, index) => {
    const answer = formData[`question${index + 1}`] || "Not answered";
    doc
      .fontSize(12)
      .font("Helvetica-Bold")
      .text(`Question ${index + 1}: ${question}`);
    doc.fontSize(12).font("Helvetica").text(`Answer: ${answer}`);
    doc.moveDown();
  });

  // Add a section for disease risk levels
  doc
    .fontSize(16)
    .font("Helvetica-Bold")
    .text("Risk Levels for Fungal Conditions:");
  doc.moveDown();

  // Add disease and corresponding risk levels to the PDF
  for (let condition in results) {
    const riskLevel = results[condition];
    let color;

    // Color-coding based on risk level
    switch (riskLevel) {
      case "High":
        color = "red";
        break;
      case "Moderate":
        color = "orange";
        break;
      case "Low":
        color = "green";
        break;
      default:
        color = "black";
    }

    // Add disease and risk level to the PDF with appropriate color
    doc.fontSize(14).fillColor(color).text(`${condition}: ${riskLevel}`);
  }

  // End and send the PDF
  doc.end();
});

// Start the Server
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

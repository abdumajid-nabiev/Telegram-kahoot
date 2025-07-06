document.addEventListener("DOMContentLoaded", () => {
  const newQuizNameInput = document.getElementById("new-quiz-name");
  const createQuizBtn = document.getElementById("create-quiz-btn");
  const quizzesUl = document.getElementById("quizzes-ul");
  const editorSection = document.getElementById("editor");
  const questionsContainer = document.getElementById("questions-container");
  const saveQuizBtn = document.getElementById("save-quiz-btn");
  const cancelEditBtn = document.getElementById("cancel-edit-btn");
  const addQuestionBtn = document.getElementById("add-question-btn");
  const editingFilenameSpan = document.getElementById("editing-filename");

  let currentQuiz = null; // quiz data array
  let currentFilename = null;

  // Helpers to create DOM elements for questions & options
  function createOptionElement(optionText = "", isCorrect = false, optionIndex = 0) {
    const optionRow = document.createElement("div");
    optionRow.classList.add("option-row");

    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = `correct-option-${optionIndex}`;
    radio.classList.add("correct-radio");

    const input = document.createElement("input");
    input.type = "text";
    input.classList.add("option-input");
    input.value = optionText;
    input.placeholder = "Option text";

    radio.checked = isCorrect;

    radio.onclick = () => {
      // Uncheck all radios in this question, then check this one
      const parent = optionRow.parentElement;
      const radios = parent.querySelectorAll('input[type="radio"]');
      radios.forEach(r => (r.checked = false));
      radio.checked = true;
    };

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "Remove Option";
    removeBtn.classList.add("remove-option-btn");
    removeBtn.onclick = () => {
      optionRow.remove();
    };

    optionRow.appendChild(radio);
    optionRow.appendChild(input);
    optionRow.appendChild(removeBtn);

    return optionRow;
  }

  function createQuestionElement(questionObj = null, index = 0) {
    const questionBlock = document.createElement("div");
    questionBlock.classList.add("question-block");

    // Question text input
    const questionInput = document.createElement("input");
    questionInput.type = "text";
    questionInput.classList.add("question-text-input");
    questionInput.placeholder = `Question ${index + 1} text`;
    questionInput.value = questionObj ? questionObj.text : "";

    // Time limit input
    const timeLimitInput = document.createElement("input");
    timeLimitInput.type = "number";
    timeLimitInput.min = 1;
    timeLimitInput.max = 60;
    timeLimitInput.value = questionObj ? questionObj.time_limit : 7;
    timeLimitInput.title = "Time limit in seconds";

    const timeLimitLabel = document.createElement("label");
    timeLimitLabel.textContent = "Time limit (seconds): ";
    timeLimitLabel.appendChild(timeLimitInput);

    // Options container
    const optionsContainer = document.createElement("div");

    // Add option buttons (max 6 options)
    const addOptionBtn = document.createElement("button");
    addOptionBtn.textContent = "+ Add Option";
    addOptionBtn.onclick = () => {
      if (optionsContainer.childElementCount >= 6) {
        alert("Max 6 options allowed.");
        return;
      }
      optionsContainer.appendChild(createOptionElement());
    };

    // Remove question button
    const removeQuestionBtn = document.createElement("button");
    removeQuestionBtn.textContent = "Remove Question";
    removeQuestionBtn.classList.add("remove-question-btn");
    removeQuestionBtn.onclick = () => {
      if (confirm("Remove this question?")) {
        questionBlock.remove();
      }
    };

    // Fill options if exist
    if (questionObj && questionObj.options && questionObj.options.length > 0) {
      questionObj.options.forEach((optText) => {
        optionsContainer.appendChild(createOptionElement(optText));
      });

      // Set correct answer radio button checked
      const correctIndex = questionObj.options.indexOf(questionObj.answer);
      if (correctIndex !== -1) {
        const radios = optionsContainer.querySelectorAll("input[type=radio]");
        radios[correctIndex].checked = true;
      }
    } else {
      // Default: 4 empty options with first correct
      for (let i = 0; i < 4; i++) {
        optionsContainer.appendChild(createOptionElement(i === 0));
      }
    }

    questionBlock.appendChild(questionInput);
    questionBlock.appendChild(timeLimitLabel);
    questionBlock.appendChild(optionsContainer);
    questionBlock.appendChild(addOptionBtn);
    questionBlock.appendChild(removeQuestionBtn);

    return questionBlock;
  }

  function renderQuizEditor(quizData) {
    questionsContainer.innerHTML = "";
    quizData.forEach((q, i) => {
      questionsContainer.appendChild(createQuestionElement(q, i));
    });
  }

  function gatherQuizDataFromEditor() {
    const questionBlocks = questionsContainer.querySelectorAll(".question-block");
    const quiz = [];

    for (const block of questionBlocks) {
      const textInput = block.querySelector(".question-text-input");
      const timeLimitInput = block.querySelector("input[type=number]");
      const optionInputs = block.querySelectorAll(".option-input");
      const correctRadios = block.querySelectorAll("input[type=radio]");

      // Validate question text
      if (!textInput.value.trim()) {
        alert("Please fill all question texts.");
        return null;
      }

      // Gather options and find which is correct
      const options = [];
      let correctAnswer = null;
      for (let i = 0; i < optionInputs.length; i++) {
        const optText = optionInputs[i].value.trim();
        if (!optText) {
          alert("Please fill all option texts.");
          return null;
        }
        options.push(optText);
        if (correctRadios[i].checked) correctAnswer = optText;
      }

      if (!correctAnswer) {
        alert("Please select the correct answer for all questions.");
        return null;
      }

      quiz.push({
        text: textInput.value.trim(),
        options: options,
        answer: correctAnswer,
        time_limit: Number(timeLimitInput.value) || 7,
      });
    }

    return quiz;
  }

  // Load quiz JSON and render editor
  async function loadQuiz(filename) {
    try {
      const res = await fetch("/load_quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });
      const data = await res.json();
      if (data.error) {
        alert("Error loading quiz: " + data.error);
        return;
      }
      currentQuiz = data;
      currentFilename = filename;
      editingFilenameSpan.textContent = currentFilename;
      renderQuizEditor(currentQuiz);
      editorSection.style.display = "block";
      document.getElementById("quiz-list").style.display = "none";
      document.getElementById("new-quiz-section").style.display = "none";
    } catch (err) {
      alert("Failed to load quiz.");
      console.error(err);
    }
  }

  // Save quiz JSON from editor
  async function saveQuiz() {
    const quiz = gatherQuizDataFromEditor();
    if (!quiz) return; // validation failed

    try {
      const res = await fetch("/save_quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: currentFilename, quiz }),
      });
      const data = await res.json();
      if (data.success) {
        alert("Quiz saved successfully!");
        location.reload();
      } else {
        alert("Failed to save quiz.");
      }
    } catch (err) {
      alert("Error saving quiz.");
      console.error(err);
    }
  }

  // Delete quiz
  async function deleteQuiz(filename) {
    if (!confirm(`Delete quiz "${filename}"? This cannot be undone.`)) return;
    try {
      const res = await fetch("/delete_quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });
      const data = await res.json();
      if (data.success) {
        alert("Quiz deleted.");
        location.reload();
      } else {
        alert("Failed to delete quiz.");
      }
    } catch (err) {
      alert("Error deleting quiz.");
      console.error(err);
    }
  }

  // Create new empty quiz file with default 1 question
  async function createNewQuiz(filename) {
    if (!filename.endsWith(".json")) {
      alert("Filename must end with .json");
      return;
    }
    const defaultQuiz = [
      {
        text: "New question?",
        options: ["Option 1", "Option 2", "Option 3", "Option 4"],
        answer: "Option 1",
        time_limit: 7,
      },
    ];

    try {
      const res = await fetch("/save_quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, quiz: defaultQuiz }),
      });
      const data = await res.json();
      if (data.success) {
        alert("New quiz created!");
        loadQuiz(filename);
      } else {
        alert("Failed to create quiz.");
      }
    } catch (err) {
      alert("Error creating quiz.");
      console.error(err);
    }
  }

  // Event listeners
  createQuizBtn.addEventListener("click", () => {
    const fname = newQuizNameInput.value.trim();
    if (!fname) {
      alert("Enter a quiz filename.");
      return;
    }
    createNewQuiz(fname);
  });

  quizzesUl.addEventListener("click", (e) => {
    if (e.target.classList.contains("load-quiz-btn")) {
      const filename = e.target.dataset.filename;
      loadQuiz(filename);
    }
    if (e.target.classList.contains("delete-quiz-btn")) {
      const filename = e.target.dataset.filename;
      deleteQuiz(filename);
    }
  });

  saveQuizBtn.addEventListener("click", () => saveQuiz());

  cancelEditBtn.addEventListener("click", () => {
    editorSection.style.display = "none";
    document.getElementById("quiz-list").style.display = "block";
    document.getElementById("new-quiz-section").style.display = "block";
  });

  addQuestionBtn.addEventListener("click", () => {
    const questionCount = questionsContainer.children.length;
    questionsContainer.appendChild(createQuestionElement(null, questionCount));
  });
});

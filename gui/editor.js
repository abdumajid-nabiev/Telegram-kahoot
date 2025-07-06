let curFile = "", curQuiz = [];
fetch("/api/quizzes").then(r=>r.json()).then(files=>{
  const sel = document.getElementById("quiz-select");
  files.forEach(f=>sel.add(new Option(f,f)));
});
function loadQuiz(){
  curFile = document.getElementById("quiz-select").value;
  fetch(`/api/quiz/${curFile}`).then(r=>r.json()).then(q=>{
    curQuiz = q;
    document.getElementById("editor").innerHTML =
      q.map((item,i)=>`
        <fieldset>
          <legend>Q${i+1}</legend>
          Text: <input value="${item.text||''}" onchange="curQuiz[${i}].text=this.value"><br>
          Options: <input value="${item.options.join(',')}" onchange="curQuiz[${i}].options=this.value.split(',')"><br>
          Answer: <input value="${item.answer}" onchange="curQuiz[${i}].answer=this.value"><br>
          Time: <input type="number" value="${item.time_limit||30}" onchange="curQuiz[${i}].time_limit=+this.value"><br>
        </fieldset>
      `).join("");
  });
}
function saveQuiz(){
  fetch(`/api/quiz/${curFile}`,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(curQuiz)
  }).then(()=>alert("Saved!"));
}
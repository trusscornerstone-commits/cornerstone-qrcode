// login.js

const form = document.querySelector("form");

// Usuário e senha "pré-definidos"
const USER = "admin@cornerstone.com";
const PASS = "Corner!stone123";

form.addEventListener("submit", function(e) {
  e.preventDefault(); // impede o envio padrão

  const email = form.email.value;
  const password = form.password.value;

  if(email === USER && password === PASS){
    // se estiver correto, redireciona
    window.location.href = "home.html";
  } else {
    alert("Email ou senha incorretos!");
  }
});

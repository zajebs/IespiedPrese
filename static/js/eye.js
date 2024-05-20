document.addEventListener("DOMContentLoaded", function() {
	const togglePassword = document.querySelector(".password-toggle");
	const passwordField = document.querySelector("#password");

	togglePassword.addEventListener("click", function() {
		const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
		passwordField.setAttribute("type", type);

		this.classList.toggle("fa-eye");
		this.classList.toggle("fa-eye-slash");
	});
});

// ===== Auth Logic =====
async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('loginBtn');
  const errDiv = document.getElementById('loginError');
  btn.innerHTML = '<span class="loader"></span> Logging in...'; btn.disabled = true;
  errDiv.classList.add('hidden');

  const data = await apiCall('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: document.getElementById('email').value, password: document.getElementById('password').value })
  });

  btn.innerHTML = 'Login'; btn.disabled = false;
  if (data?.success) {
    setAuth(data.token, data.user);
    window.location.href = data.user.is_admin ? 'admin.html' : 'dashboard.html';
  } else {
    errDiv.textContent = data?.message || 'Login failed'; errDiv.classList.remove('hidden');
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const btn = document.getElementById('registerBtn');
  const errDiv = document.getElementById('registerError');
  const successDiv = document.getElementById('registerSuccess');
  errDiv.classList.add('hidden'); successDiv.classList.add('hidden');

  const password = document.getElementById('password').value;
  if (password !== document.getElementById('confirmPassword').value) {
    errDiv.textContent = 'Passwords do not match'; errDiv.classList.remove('hidden'); return;
  }

  btn.innerHTML = '<span class="loader"></span> Creating...'; btn.disabled = true;
  const data = await apiCall('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name: document.getElementById('name').value, email: document.getElementById('email').value, password })
  });

  btn.innerHTML = 'Create Account'; btn.disabled = false;
  if (data?.success) {
    setAuth(data.token, data.user);
    successDiv.textContent = 'Account created! Redirecting...'; successDiv.classList.remove('hidden');
    setTimeout(() => window.location.href = 'dashboard.html', 1000);
  } else {
    errDiv.textContent = data?.message || 'Registration failed'; errDiv.classList.remove('hidden');
  }
}

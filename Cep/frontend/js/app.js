// ===== Core App Logic =====
const API_BASE = 'http://127.0.0.1:5000/api';

// Auth helpers
function getToken() { return localStorage.getItem('medadvisor_token'); }
function getUser() { try { return JSON.parse(localStorage.getItem('medadvisor_user')); } catch { return null; } }
function setAuth(token, user) { localStorage.setItem('medadvisor_token', token); localStorage.setItem('medadvisor_user', JSON.stringify(user)); }
function clearAuth() { localStorage.removeItem('medadvisor_token'); localStorage.removeItem('medadvisor_user'); localStorage.removeItem('medadvisor_cart'); }
function isLoggedIn() { return !!getToken(); }

// API helper
async function apiCall(endpoint, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    const data = await res.json();
    if (res.status === 401) { clearAuth(); window.location.href = 'login.html'; return null; }
    return data;
  } catch (err) { console.error('API Error:', err); showToast('Connection error. Is the server running?', 'error'); return null; }
}

// Cart helpers
function getCart() { try { return JSON.parse(localStorage.getItem('medadvisor_cart')) || []; } catch { return []; } }
function saveCart(cart) { localStorage.setItem('medadvisor_cart', JSON.stringify(cart)); updateCartBadge(); }
function addToCart(medicine) {
  const cart = getCart();
  const existing = cart.find(i => i.id === medicine.id);
  if (existing) { existing.quantity += 1; } else { cart.push({ ...medicine, quantity: 1 }); }
  saveCart(cart);
  showToast(`${medicine.name} added to cart!`, 'success');
}
function removeFromCart(id) { saveCart(getCart().filter(i => i.id !== id)); }
function updateCartQuantity(id, delta) {
  const cart = getCart();
  const item = cart.find(i => i.id === id);
  if (item) { item.quantity += delta; if (item.quantity <= 0) removeFromCart(id); else saveCart(cart); }
}
function getCartTotal() { return getCart().reduce((sum, i) => sum + (i.price * i.quantity), 0); }
function getCartCount() { return getCart().reduce((sum, i) => sum + i.quantity, 0); }
function updateCartBadge() {
  document.querySelectorAll('#cartBadge,.cart-badge').forEach(el => { if(el) el.textContent = getCartCount(); });
}

// Toast notifications
function showToast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span> ${msg}`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100px)'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// Navbar auth state
function updateNavbar() {
  const user = getUser();
  const navAuth = document.getElementById('navAuth');
  const navUser = document.getElementById('navUser');
  const navAvatar = document.getElementById('navAvatar');
  if (navAuth && navUser) {
    if (user) { navAuth.classList.add('hidden'); navUser.classList.remove('hidden'); if (navAvatar) navAvatar.textContent = user.name?.charAt(0)?.toUpperCase() || 'U'; }
    else { navAuth.classList.remove('hidden'); navUser.classList.add('hidden'); }
  }
  updateCartBadge();
}

function logout() { clearAuth(); window.location.href = 'index.html'; }
function toggleMenu() { document.getElementById('navLinks')?.classList.toggle('open'); }
function toggleSidebar() { document.getElementById('sidebar')?.classList.toggle('open'); }

// Init
document.addEventListener('DOMContentLoaded', () => { updateNavbar(); updateCartBadge(); });

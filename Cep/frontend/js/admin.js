// ===== Admin Logic =====
document.addEventListener('DOMContentLoaded', () => {
  if (!isLoggedIn()) { window.location.href = 'login.html'; return; }
  const user = getUser();
  if (!user?.is_admin) { window.location.href = 'dashboard.html'; return; }
  loadDashboard();
});

function showAdminSection(section) {
  ['overviewSection','usersSection','adminOrdersSection','medicinesSection'].forEach(s => document.getElementById(s).classList.add('hidden'));
  document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));
  event.target.closest('a').classList.add('active');
  const map = { overview:'overviewSection', users:'usersSection', orders:'adminOrdersSection', medicines:'medicinesSection' };
  document.getElementById(map[section]).classList.remove('hidden');
  if (section === 'overview') loadDashboard();
  else if (section === 'users') loadUsers();
  else if (section === 'orders') loadAdminOrders();
  else if (section === 'medicines') loadAdminMedicines();
}

async function loadDashboard() {
  const data = await apiCall('/admin/dashboard');
  if (!data?.stats) return;
  const s = data.stats;
  document.getElementById('statsGrid').innerHTML = `
    <div class="stat-card"><div class="stat-icon blue">👥</div><div class="stat-info"><h3>${s.total_users}</h3><p>Total Users</p></div></div>
    <div class="stat-card"><div class="stat-icon green">📦</div><div class="stat-info"><h3>${s.total_orders}</h3><p>Total Orders</p></div></div>
    <div class="stat-card"><div class="stat-icon yellow">💊</div><div class="stat-info"><h3>${s.total_medicines}</h3><p>Medicines</p></div></div>
    <div class="stat-card"><div class="stat-icon red">💰</div><div class="stat-info"><h3>$${s.total_revenue.toFixed(2)}</h3><p>Revenue</p></div></div>
  `;
  const tbody = document.querySelector('#recentOrdersTable tbody');
  tbody.innerHTML = s.recent_orders.map(o => `<tr>
    <td>#${o.id}</td><td>${o.user_name}</td><td>${o.items.length} items</td>
    <td>$${o.total_price.toFixed(2)}</td>
    <td><span class="status-badge ${o.status.toLowerCase().replace(/ /g,'-')}">${o.status}</span></td>
    <td>${new Date(o.created_at).toLocaleDateString()}</td>
  </tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--text-light)">No orders yet</td></tr>';
}

async function loadUsers() {
  const data = await apiCall('/admin/users');
  document.querySelector('#usersTable tbody').innerHTML = (data?.users || []).map(u => `<tr>
    <td>${u.id}</td><td>${u.name}</td><td>${u.email}</td><td>${new Date(u.created_at).toLocaleDateString()}</td>
  </tr>`).join('') || '<tr><td colspan="4" style="text-align:center">No users</td></tr>';
}

async function loadAdminOrders() {
  const status = document.getElementById('orderStatusFilter')?.value || '';
  const data = await apiCall(`/admin/orders${status ? '?status=' + status : ''}`);
  document.querySelector('#adminOrdersTable tbody').innerHTML = (data?.orders || []).map(o => `<tr>
    <td>#${o.id}</td><td>${o.user_name}</td><td style="font-size:0.8rem">${o.tracking_id}</td>
    <td>$${o.total_price.toFixed(2)}</td>
    <td><span class="status-badge ${o.status.toLowerCase().replace(/ /g,'-')}">${o.status}</span></td>
    <td><button class="btn btn-sm btn-secondary" onclick="advanceOrder(${o.id})" ${o.status==='Delivered'?'disabled':''}>Advance ➤</button></td>
  </tr>`).join('') || '<tr><td colspan="6" style="text-align:center">No orders</td></tr>';
}

async function advanceOrder(id) {
  const data = await apiCall(`/admin/orders/${id}/advance`, { method: 'PUT' });
  if (data?.success) { showToast('Order status updated!', 'success'); loadAdminOrders(); loadDashboard(); }
  else showToast(data?.message || 'Failed', 'error');
}

async function loadAdminMedicines() {
  const data = await apiCall('/medicines/');
  document.querySelector('#medicinesTable tbody').innerHTML = (data?.medicines || []).map(m => `<tr>
    <td>${m.id}</td><td>${m.name}</td><td>${m.category}</td><td>$${m.price.toFixed(2)}</td>
    <td><span class="med-stock ${m.stock<10?'low':''}">${m.stock}</span></td>
    <td><button class="btn btn-sm btn-danger" onclick="deleteMedicine(${m.id})">Delete</button></td>
  </tr>`).join('');
}

function showAddMedicineModal() { document.getElementById('addMedicineModal').classList.remove('hidden'); }
function closeModal() { document.getElementById('addMedicineModal').classList.add('hidden'); }

async function addMedicine(e) {
  e.preventDefault();
  const data = await apiCall('/admin/medicines', {
    method: 'POST',
    body: JSON.stringify({
      name: document.getElementById('medName').value,
      generic_name: document.getElementById('medGeneric').value,
      category: document.getElementById('medCategory').value,
      description: document.getElementById('medDesc').value,
      dosage: document.getElementById('medDosage').value,
      price: parseFloat(document.getElementById('medPrice').value),
      stock: parseInt(document.getElementById('medStock').value)
    })
  });
  if (data?.success) { showToast('Medicine added!', 'success'); closeModal(); loadAdminMedicines(); }
  else showToast('Failed to add', 'error');
}

async function deleteMedicine(id) {
  if (!confirm('Delete this medicine?')) return;
  const data = await apiCall(`/admin/medicines/${id}`, { method: 'DELETE' });
  if (data?.success) { showToast('Medicine deleted', 'success'); loadAdminMedicines(); }
  else showToast('Failed', 'error');
}

// ===== Shop Logic =====
let allMedicines = [];
let currentCategory = 'all';

document.addEventListener('DOMContentLoaded', () => { loadMedicines(); });

async function loadMedicines() {
  const data = await apiCall('/medicines/');
  if (data?.medicines) { allMedicines = data.medicines; renderMedicines(allMedicines); }
}

function renderMedicines(medicines) {
  const grid = document.getElementById('medicinesGrid');
  if (!medicines.length) { grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><span class="empty-icon">💊</span><h3>No medicines found</h3><p>Try a different search or category</p></div>`; return; }
  grid.innerHTML = medicines.map(m => {
    const stockClass = m.stock <= 0 ? 'out' : m.stock < 10 ? 'low' : '';
    const stockText = m.stock <= 0 ? 'Out of Stock' : m.stock < 10 ? `Only ${m.stock} left` : `In Stock (${m.stock})`;
    return `
    <div class="medicine-card">
      <span class="med-emoji">${m.image_url || '💊'}</span>
      <span class="med-category">${m.category || 'General'}</span>
      <h3>${m.name}</h3>
      <p class="med-generic">${m.generic_name}</p>
      <p class="med-desc">${m.description || ''}</p>
      <div class="flex justify-between items-center">
        <span class="med-price">$${m.price.toFixed(2)}</span>
        <span class="med-stock ${stockClass}">${stockText}</span>
      </div>
      <div class="card-actions">
        <button class="btn btn-primary btn-sm w-full" onclick='addToCart(${JSON.stringify({id:m.id,name:m.name,price:m.price,image_url:m.image_url})})' ${m.stock<=0?'disabled style="opacity:0.5"':''}>
          ${m.stock<=0?'Out of Stock':'🛒 Add to Cart'}
        </button>
      </div>
    </div>`;
  }).join('');
}

function filterMedicines() {
  const search = document.getElementById('searchInput').value.toLowerCase();
  let filtered = allMedicines;
  if (currentCategory !== 'all') filtered = filtered.filter(m => m.category === currentCategory);
  if (search) filtered = filtered.filter(m => m.name.toLowerCase().includes(search) || m.generic_name.toLowerCase().includes(search) || (m.description||'').toLowerCase().includes(search));
  renderMedicines(filtered);
}

function filterCategory(btn, cat) {
  currentCategory = cat;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterMedicines();
}

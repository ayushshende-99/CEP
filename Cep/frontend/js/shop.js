// ===== Shop Logic =====
let allMedicines = [];
let currentCategory = 'all';

document.addEventListener('DOMContentLoaded', () => { loadMedicines(); });

function normalizeText(value) {
  return (value || '').toLowerCase().replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim();
}

function tokenize(value) {
  return normalizeText(value).split(' ').filter(Boolean);
}

function editDistanceLimited(a, b, maxDistance = 2) {
  if (a === b) return 0;
  if (Math.abs(a.length - b.length) > maxDistance) return maxDistance + 1;

  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const curr = [i];
    let minRow = i;
    for (let j = 1; j <= b.length; j++) {
      const ins = curr[j - 1] + 1;
      const del = prev[j] + 1;
      const rep = prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1);
      const cost = Math.min(ins, del, rep);
      curr.push(cost);
      if (cost < minRow) minRow = cost;
    }
    if (minRow > maxDistance) return maxDistance + 1;
    prev = curr;
  }
  return prev[prev.length - 1];
}

function semanticMedicineScore(medicine, query) {
  const normalizedQuery = normalizeText(query);
  const queryTokens = tokenize(query);
  if (!normalizedQuery || !queryTokens.length) return 0;

  const name = normalizeText(medicine.name);
  const generic = normalizeText(medicine.generic_name);
  const description = normalizeText(medicine.description || '');
  const category = normalizeText(medicine.category || '');
  const combinedTokens = new Set(tokenize(`${medicine.name} ${medicine.generic_name || ''} ${medicine.description || ''} ${medicine.category || ''}`));

  let score = 0;
  if (name.includes(normalizedQuery)) score += 10;
  if (generic.includes(normalizedQuery)) score += 8;
  if (description.includes(normalizedQuery)) score += 4;
  if (category.includes(normalizedQuery)) score += 4;

  for (const token of queryTokens) {
    if (combinedTokens.has(token)) {
      score += 2.5;
      continue;
    }

    for (const medToken of combinedTokens) {
      if (token.length <= 4 && editDistanceLimited(token, medToken, 1) <= 1) {
        score += 1.2;
        break;
      }
      if (token.length > 4 && editDistanceLimited(token, medToken, 2) <= 2) {
        score += 0.9;
        break;
      }
    }
  }

  return score;
}

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
  const search = document.getElementById('searchInput').value;
  let filtered = allMedicines;
  if (currentCategory !== 'all') filtered = filtered.filter(m => m.category === currentCategory);
  if (search && normalizeText(search)) {
    const ranked = filtered
      .map(medicine => ({ medicine, score: semanticMedicineScore(medicine, search) }))
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(item => item.medicine);
    filtered = ranked;
  }
  renderMedicines(filtered);
}

function filterCategory(btn, cat) {
  currentCategory = cat;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterMedicines();
}

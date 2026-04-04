// ===== Tracking Logic =====
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const id = params.get('id');
  if (id) { document.getElementById('trackingInput').value = id; trackOrder(); }
});

async function trackOrder() {
  const trackingId = document.getElementById('trackingInput').value.trim();
  if (!trackingId) { showToast('Please enter a tracking ID', 'error'); return; }

  const resultDiv = document.getElementById('trackingResult');
  const errorDiv = document.getElementById('trackingError');
  resultDiv.classList.add('hidden'); errorDiv.classList.add('hidden');

  const data = await apiCall(`/orders/track/${trackingId}`);

  if (data?.success) {
    resultDiv.classList.remove('hidden');
    document.getElementById('trackOrderId').textContent = data.order.id;
    document.getElementById('trackTrackingId').textContent = data.order.tracking_id;

    const statusEl = document.getElementById('trackStatus');
    statusEl.textContent = data.order.status;
    statusEl.className = `status-badge ${data.order.status.toLowerCase().replace(/ /g, '-')}`;

    document.getElementById('trackDate').textContent = new Date(data.order.created_at).toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' });
    document.getElementById('trackProgress').style.width = data.progress_percentage + '%';

    const icons = ['📋', '✅', '📦', '🚚', '🛵', '🏠'];
    document.getElementById('timeline').innerHTML = data.timeline.map((t, i) => `
      <div class="timeline-item ${t.completed ? 'completed' : ''} ${t.current ? 'current' : ''}">
        <div class="timeline-dot">${t.completed ? '✓' : icons[i]}</div>
        <div class="timeline-content">
          <h4>${t.status}</h4>
          <p>${t.description}</p>
        </div>
      </div>
    `).join('');

    document.getElementById('trackItemsList').innerHTML = data.order.items.map(i => `
      <div class="flex justify-between items-center" style="padding:8px 0;border-bottom:1px solid var(--border)">
        <span>${i.name} × ${i.quantity}</span>
        <strong>$${i.subtotal.toFixed(2)}</strong>
      </div>
    `).join('') + `<div class="flex justify-between items-center" style="padding:12px 0;font-weight:800;font-size:1.1rem"><span>Total</span><span>$${data.order.total_price.toFixed(2)}</span></div>`;
  } else {
    errorDiv.classList.remove('hidden');
  }
}

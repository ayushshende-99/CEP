// ===== Cart Logic =====
document.addEventListener('DOMContentLoaded', () => {
  if (!isLoggedIn()) { window.location.href = 'login.html'; return; }
  renderCart();
});

function renderCart() {
  const cart = getCart();
  const cartContent = document.getElementById('cartContent');
  const emptyCart = document.getElementById('emptyCart');
  const countEl = document.getElementById('cartCount');

  if (!cart.length) { cartContent.classList.add('hidden'); emptyCart.classList.remove('hidden'); return; }
  cartContent.classList.remove('hidden'); emptyCart.classList.add('hidden');
  if (countEl) countEl.textContent = `${getCartCount()} items in cart`;

  document.getElementById('cartItems').innerHTML = cart.map(item => `
    <div class="cart-item">
      <span class="item-emoji">${item.image_url || '💊'}</span>
      <div class="item-info">
        <h4>${item.name}</h4>
        <span class="item-price">₹${item.price.toFixed(2)} each</span>
      </div>
      <div class="qty-control">
        <button onclick="updateCartQuantity(${item.id},-1);renderCart()">−</button>
        <span>${item.quantity}</span>
        <button onclick="updateCartQuantity(${item.id},1);renderCart()">+</button>
      </div>
      <span class="item-subtotal">₹${(item.price * item.quantity).toFixed(2)}</span>
      <button class="remove-btn" onclick="removeFromCart(${item.id});renderCart()">🗑️</button>
    </div>
  `).join('');

  const total = getCartTotal();
  document.getElementById('subtotal').textContent = `₹${total.toFixed(2)}`;
  document.getElementById('totalPrice').textContent = `₹${total.toFixed(2)}`;
}

async function placeOrder() {
  const cart = getCart();
  if (!cart.length) { showToast('Cart is empty', 'error'); return; }

  const address = document.getElementById('shippingAddress').value;
  if (!address) { showToast('Please enter shipping address', 'error'); return; }

  const btn = document.getElementById('checkoutBtn');
  btn.innerHTML = '<span class="loader"></span> Processing...'; btn.disabled = true;

  const data = await apiCall('/orders/place', {
    method: 'POST',
    body: JSON.stringify({
      items: cart.map(i => ({ id: i.id, quantity: i.quantity })),
      address,
      payment_method: 'Cash on Delivery'
    })
  });

  btn.innerHTML = '🛒 Place Order'; btn.disabled = false;

  if (data?.success) {
    saveCart([]);
    document.getElementById('modalTrackingId').textContent = data.order.tracking_id;
    document.getElementById('orderModal').classList.remove('hidden');
    showToast('Order placed successfully!', 'success');
  } else {
    showToast(data?.errors?.join(', ') || data?.message || 'Failed to place order', 'error');
  }
}

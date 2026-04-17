// ===== Chat Logic (Friendly Edition + Order via Chat) =====

// Quick-reply suggestion chips
const QUICK_REPLIES = [
  "I have a headache",
  "I'm feeling feverish",
  "I have a cough and cold",
  "My stomach hurts",
  "I have a sore throat",
  "I can't sleep at night",
  "I have allergies",
  "I have body pain",
  "I feel anxious",
  "What can you do?"
];

const ORDER_QUICK_REPLIES = [
  "I want to order Paracetamol 500mg",
  "Buy Cetirizine 200mg",
  "I need Omeprazole 200mg"
];

// ===== Voice Input (Speech-to-Text) =====
let voiceRecognition = null;
let isRecording = false;

function initVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    let finalTranscript = '';
    let interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }
    const input = document.getElementById('chatInput');
    if (finalTranscript) {
      input.value = finalTranscript;
    } else {
      input.value = interimTranscript;
      input.placeholder = '🎙️ Listening...';
    }
  };

  recognition.onend = () => {
    isRecording = false;
    updateMicButton();
    const input = document.getElementById('chatInput');
    input.placeholder = 'Describe your symptoms or order medicine...';
    // Auto-send if there's text
    if (input.value.trim()) {
      sendMessage();
    }
  };

  recognition.onerror = (event) => {
    isRecording = false;
    updateMicButton();
    const input = document.getElementById('chatInput');
    input.placeholder = 'Describe your symptoms or order medicine...';
    if (event.error === 'no-speech') {
      showToast('No speech detected. Please try again.', 'info');
    } else if (event.error === 'not-allowed') {
      showToast('Microphone access denied. Please allow microphone in browser settings.', 'error');
    } else {
      showToast('Voice input error. Please try again.', 'error');
    }
  };

  return recognition;
}

function toggleVoiceInput() {
  if (!voiceRecognition) {
    voiceRecognition = initVoiceRecognition();
  }

  if (!voiceRecognition) {
    showToast('Voice input is not supported in this browser. Try Chrome or Edge.', 'error');
    return;
  }

  if (isRecording) {
    voiceRecognition.stop();
    isRecording = false;
  } else {
    document.getElementById('chatInput').value = '';
    document.getElementById('chatInput').placeholder = '🎙️ Listening...';
    voiceRecognition.start();
    isRecording = true;
  }
  updateMicButton();
}

function updateMicButton() {
  const btn = document.getElementById('micBtn');
  if (!btn) return;
  if (isRecording) {
    btn.classList.add('recording');
    btn.title = 'Stop listening';
  } else {
    btn.classList.remove('recording');
    btn.title = 'Speak your symptoms';
  }
}

// ===== Voice Output (Text-to-Speech) =====
let currentUtterance = null;

function speakText(buttonEl) {
  // If already speaking, stop
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    document.querySelectorAll('.voice-speak-btn.speaking').forEach(b => {
      b.classList.remove('speaking');
      b.textContent = '🔊';
      b.title = 'Read aloud';
    });
    // If clicking the same button that was speaking, just stop
    if (buttonEl.classList.contains('speaking')) {
      buttonEl.classList.remove('speaking');
      buttonEl.textContent = '🔊';
      buttonEl.title = 'Read aloud';
      return;
    }
  }

  // Get the text content from the parent message
  const messageContainer = buttonEl.closest('.message-bot') || buttonEl.closest('.message');
  if (!messageContainer) return;

  // Collect text from message bubbles and medical results, strip HTML
  const elements = messageContainer.querySelectorAll('.message-bubble, .medical-result');
  let text = '';
  elements.forEach(el => {
    text += el.innerText + '. ';
  });
  text = text.replace(/\s+/g, ' ').trim();
  if (!text) return;

  // Limit length for TTS performance
  if (text.length > 2000) {
    text = text.substring(0, 2000) + '... That is all I will read for now.';
  }

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 1;
  utterance.volume = 1;
  utterance.lang = 'en-US';

  // Try to pick a good voice
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.name.includes('Google') && v.lang.startsWith('en'))
    || voices.find(v => v.lang.startsWith('en') && v.localService)
    || voices.find(v => v.lang.startsWith('en'));
  if (preferred) utterance.voice = preferred;

  buttonEl.classList.add('speaking');
  buttonEl.textContent = '⏹️';
  buttonEl.title = 'Stop reading';

  utterance.onend = () => {
    buttonEl.classList.remove('speaking');
    buttonEl.textContent = '🔊';
    buttonEl.title = 'Read aloud';
  };
  utterance.onerror = () => {
    buttonEl.classList.remove('speaking');
    buttonEl.textContent = '🔊';
    buttonEl.title = 'Read aloud';
  };

  currentUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

// Preload voices
if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}

// Helper: create speaker button HTML
function speakerBtnHtml() {
  return `<button class="voice-speak-btn" onclick="speakText(this)" title="Read aloud">🔊</button>`;
}

// Helper: render a formatted bot message (markdown-like)
function renderBotMessage(message) {
  return message
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}


document.addEventListener('DOMContentLoaded', () => {
  if (!isLoggedIn()) { window.location.href = 'login.html'; return; }
  const user = getUser();
  const sa = document.getElementById('sidebarAvatar');
  const sn = document.getElementById('sidebarName');
  const se = document.getElementById('sidebarEmail');
  if (sa) sa.textContent = user?.name?.charAt(0)?.toUpperCase() || 'U';
  if (sn) sn.textContent = user?.name || 'User';
  if (se) se.textContent = user?.email || '';

  // Show personalized welcome
  const chatMessages = document.getElementById('chatMessages');
  const firstName = user?.name?.split(' ')[0] || 'there';
  const hour = new Date().getHours();
  let greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  chatMessages.innerHTML = `
    <div class="message message-bot">
      <div class="message-avatar">🤖</div>
      <div>
        <div class="message-bubble">
          ${greeting}, <strong>${firstName}</strong>! 👋😊<br><br>
          I'm your friendly <strong>MedAdvisor AI</strong> — here to help you feel better!<br><br>
          Tell me what's bothering you in your own words, and I'll run your symptoms through the trained disease model, then suggest medicines from the loaded catalog.<br><br>
          🛒 <strong>You can also order medicines directly!</strong> Just say something like "I want to order Paracetamol".<br><br>
          💡 <em>Try tapping a suggestion below, typing, or click 🎤 to speak!</em>
        </div>
        ${speakerBtnHtml()}
        <div class="quick-replies" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px">
          ${QUICK_REPLIES.map(q => `<button class="quick-reply-chip" onclick="sendQuickReply('${q}')">${q}</button>`).join('')}
        </div>
        <div style="margin-top:8px">
          <p style="font-size:0.8rem;color:var(--text-light);margin-bottom:6px">🛒 <strong>Order medicines:</strong></p>
          <div style="display:flex;flex-wrap:wrap;gap:6px">
            ${ORDER_QUICK_REPLIES.map(q => `<button class="quick-reply-chip" style="border-color:var(--secondary);color:var(--secondary)" onclick="sendQuickReply('${q}')">${q}</button>`).join('')}
          </div>
        </div>
        <div class="disclaimer-box mt-1">
          <span>💙</span>
          <span>I provide general health guidance only — always check with a real doctor before taking any medicine!</span>
        </div>
      </div>
    </div>
  `;
});

function showSection(section) {
  document.getElementById('chatSection').classList.toggle('hidden', section !== 'chat');
  document.getElementById('ordersSection').classList.toggle('hidden', section !== 'orders');
  document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));
  event.target.closest('a').classList.add('active');
  if (section === 'orders') loadOrders();
}

function sendQuickReply(text) {
  document.getElementById('chatInput').value = text;
  sendMessage();
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  const chatMessages = document.getElementById('chatMessages');

  // Hide quick replies after first message
  document.querySelectorAll('.quick-replies').forEach(el => el.style.display = 'none');

  // User message
  const userName = getUser()?.name?.split(' ')[0] || 'You';
  chatMessages.innerHTML += `<div class="message message-user"><div class="message-avatar">😊</div><div class="message-bubble">${escapeHtml(msg)}</div></div>`;

  // Friendly typing indicator
  const typingId = 'typing-' + Date.now();
  chatMessages.innerHTML += `<div class="message message-bot" id="${typingId}"><div class="message-avatar">🤖</div><div class="message-bubble"><span class="typing-dots"><span>.</span><span>.</span><span>.</span></span> Thinking...</div></div>`;
  chatMessages.scrollTop = chatMessages.scrollHeight;

  const data = await apiCall('/medical/analyze', { method: 'POST', body: JSON.stringify({ symptoms: msg }) });
  document.getElementById(typingId)?.remove();

  if (data?.is_order && data?.success && data?.medicine) {
    // ===== ORDER FLOW: Medicine found =====
    const med = data.medicine;
    const rxRequired = data.requires_prescription;
    const qty = data.quantity || 1;
    const totalPrice = (med.price * qty).toFixed(2);

    let html = `<div class="message message-bot"><div class="message-avatar">🤖</div><div>`;
    html += `<div class="message-bubble">${renderBotMessage(data.message)}</div>`;

    // Medicine order card
    html += `<div class="order-card-chat">`;
    html += `<div class="order-card-header">`;
    html += `<span class="order-card-emoji">${med.image_url || '💊'}</span>`;
    html += `<div>`;
    html += `<h4>${med.name}</h4>`;
    html += `<p class="order-card-category">${med.category || 'General'}</p>`;
    html += `</div>`;
    html += `</div>`;
    html += `<div class="order-card-details">`;
    html += `<div class="order-card-price">₹${med.price.toFixed(2)} × ${qty} = ₹${totalPrice}</div>`;
    html += `<div class="order-card-stock ${med.stock > 0 ? '' : 'out'}">📦 ${med.stock > 0 ? med.stock + ' in stock' : 'Out of stock'}</div>`;
    html += `</div>`;

    if (rxRequired) {
      // Prescription required — show upload area
      html += `<div class="prescription-required-badge">⚠️ Prescription Required</div>`;
      html += `<p style="font-size:0.82rem;color:var(--text-light);margin:8px 0">Upload your prescription to proceed. Name the file with the medicine name and today's date.</p>`;
      html += `<div class="prescription-upload-area" id="rxUpload_${med.id}">`;
      html += `<div class="rx-upload-icon">📋</div>`;
      html += `<p>Upload Prescription Image</p>`;
      html += `<p class="rx-hint">File should contain medicine name & today's date<br>e.g. <code>${med.name.split(' ')[0].split(',')[0].toLowerCase()}_${new Date().toISOString().split('T')[0]}.jpg</code></p>`;
      html += `<input type="file" id="rxFile_${med.id}" accept="image/*,.pdf" onchange="handleRxFileSelect(${med.id}, this)" style="display:none">`;
      html += `<button class="btn btn-outline btn-sm" onclick="document.getElementById('rxFile_${med.id}').click()">📤 Choose File</button>`;
      html += `<div id="rxFileName_${med.id}" class="rx-file-name" style="display:none"></div>`;
      html += `<button class="btn btn-primary btn-sm mt-1" id="rxSubmitBtn_${med.id}" onclick="uploadPrescription(${med.id}, ${qty})" style="display:none">✅ Upload & Verify Prescription</button>`;
      html += `</div>`;
    } else {
      // No prescription needed — show confirm button
      html += `<div class="no-prescription-badge">✅ No Prescription Needed</div>`;
      html += `<button class="btn btn-primary btn-sm w-full mt-1" onclick="confirmChatOrder(${med.id}, '${escapeHtml(med.name)}', ${qty})">🛒 Confirm Order (${qty})</button>`;
    }

    html += `</div>`; // close order-card-chat
    html += `${speakerBtnHtml()}</div></div>`;
    chatMessages.innerHTML += html;

  } else if (data?.is_order && !data?.success) {
    // ===== ORDER FLOW: Medicine not found =====
    let formattedMsg = renderBotMessage(data.message);
    chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
      <div class="message-bubble">${formattedMsg}</div>
      ${speakerBtnHtml()}
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
        ${ORDER_QUICK_REPLIES.map(q => `<button class="quick-reply-chip" style="border-color:var(--secondary);color:var(--secondary)" onclick="sendQuickReply('${q}')">${q}</button>`).join('')}
        <a href="shop.html" class="btn btn-outline btn-sm">🏪 Browse Shop</a>
      </div>
    </div></div>`;

  } else if (data?.success) {
    // ===== ML-BASED SYMPTOM ANALYSIS =====
    let html = `<div class="message message-bot"><div class="message-avatar">🤖</div><div>`;

    const empathy = data.empathy_message || "Here's what I found for you:";
    html += `<div class="message-bubble">${empathy}<br><br>I matched these symptoms: <strong>${data.symptoms_detected.join(', ')}</strong></div>`;

    if (data.urgent_warning) {
      html += `<p style="font-size:0.82rem;margin-top:10px;color:var(--danger);background:#FEF2F2;padding:10px 12px;border-radius:10px"><strong>🏥 Seek medical care:</strong> ${data.urgent_warning}</p>`;
    }

    data.results.forEach(r => {
      html += `<div class="medical-result">`;
      html += `<h4>🧠 ${r.disease}</h4>`;
      html += `<p style="font-size:0.85rem;margin-bottom:6px"><strong>Model match score:</strong> ${r.match_score}%</p>`;
      html += `<div style="height:8px;background:#E5E7EB;border-radius:999px;overflow:hidden;margin-bottom:10px"><div style="height:100%;width:${Math.min(r.match_score, 100)}%;background:linear-gradient(90deg, #14B8A6, #0F766E)"></div></div>`;
      html += `<p style="font-size:0.8rem;color:var(--text-light);margin-bottom:8px">Estimated global probability: ${r.probability}%</p>`;
      html += `<p style="font-size:0.85rem;margin:10px 0 6px"><strong>Symptoms supporting this match:</strong></p>`;
      html += r.supporting_symptoms.map(s => `<span class="condition-tag">${s}</span>`).join('');
      html += `</div>`;
    });

    if (data.medicine_suggestions?.length) {
      html += `<div class="medical-result">`;
      html += `<h4>💊 Suggested Medicines</h4>`;
      html += `<p style="font-size:0.84rem;color:var(--text-light);margin-bottom:8px">These suggestions are based on your symptoms and predicted diseases.</p>`;

      data.medicine_suggestions.forEach(m => {
        html += `<div class="medicine-card-sm">`;
        html += `<h5>${escapeHtml(m.name)}</h5>`;
        if (m.generic_name) {
          html += `<p style="font-size:0.8rem;color:var(--text-light)">Generic: ${escapeHtml(m.generic_name)}</p>`;
        }
        html += `<p class="dosage">Dosage: ${escapeHtml(m.dosage || 'Use as directed')}</p>`;
        html += `<p class="side-fx">Category: ${escapeHtml(m.category || 'General')}</p>`;
        if (m.reason) {
          html += `<p style="font-size:0.78rem;color:var(--text-light);margin-top:4px">Why suggested: ${escapeHtml(m.reason)}</p>`;
        }

        if (m.in_shop && m.medicine_id) {
          const priceText = typeof m.price === 'number' ? ` | Price: ₹${m.price.toFixed(2)}` : '';
          html += `<p style="font-size:0.8rem;color:var(--primary);margin-top:4px">Available in shop${priceText}</p>`;
          html += `<button class="btn btn-primary btn-sm mt-1" onclick="confirmChatOrder(${m.medicine_id}, '', 1)">Order This Medicine</button>`;
        } else {
          html += `<p style="font-size:0.8rem;color:var(--warning);margin-top:6px">Not currently available in our shop catalog.</p>`;
        }
        html += `</div>`;
      });
      html += `</div>`;
    }

    if (data.care_advice?.length) {
      html += `<div class="medical-result">`;
      html += `<h4>🩺 Care Advice</h4>`;
      data.care_advice.forEach(advice => {
        html += `<p style="font-size:0.84rem;color:var(--text-light);margin-top:6px">• ${escapeHtml(advice)}</p>`;
      });
      html += `</div>`;
    }

    if (data.follow_up) {
      html += `<div class="message-bubble" style="margin-top:8px">${data.follow_up}</div>`;
    }

    if (data.model) {
      html += `<div class="message-bubble" style="margin-top:8px;background:#F0FDF4;border-radius:12px">
        <strong>Model:</strong> ${data.model.name}<br>
        <strong>Training data:</strong> ${data.model.rows.toLocaleString()} rows, ${data.model.diseases} diseases, ${data.model.symptom_features} symptom features.<br><br>
        Use this as a guide only. If symptoms are severe, unusual, or getting worse, please speak with a doctor.
      </div>`;
    } else {
      html += `<div class="message-bubble" style="margin-top:8px;background:#F0FDF4;border-radius:12px">
        Use this as a guide only. If symptoms are severe, unusual, or getting worse, please speak with a doctor.
      </div>`;
    }

    html += `<div class="message-bubble" style="margin-top:8px;background:#ECFDF5;border-radius:12px">
      You can still <a href="shop.html" style="color:var(--primary);font-weight:600">browse the pharmacy</a> if you need symptom-relief products.
    </div>`;
    html += `<div class="disclaimer-box mt-1"><span>💙</span><span>${data.disclaimer}</span></div>`;
    html += `${speakerBtnHtml()}`;
    html += `<div class="mt-1 flex gap-1" style="flex-wrap:wrap">
      <a href="shop.html" class="btn btn-primary btn-sm">🛒 Order Medicines</a>
      <button class="btn btn-outline btn-sm" onclick="sendQuickReply('thank you')">👍 Thanks!</button>
    </div>`;
    html += `</div></div>`;
    chatMessages.innerHTML += html;

  } else if (data?.is_chat) {
    // ===== CASUAL CONVERSATION =====
    let formattedMsg = renderBotMessage(data.message);
    chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div><div class="message-bubble">${formattedMsg}</div>${speakerBtnHtml()}</div></div>`;

  } else {
    // ===== UNRECOGNIZED — Friendly fallback =====
    let formattedMsg = renderBotMessage(data?.message || "I'm not sure about that, but I'd love to help! Could you describe your symptoms differently?");
    chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
      <div class="message-bubble">${formattedMsg}</div>
      ${speakerBtnHtml()}
      <div class="quick-replies" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
        ${QUICK_REPLIES.slice(0, 6).map(q => `<button class="quick-reply-chip" onclick="sendQuickReply('${q}')">${q}</button>`).join('')}
      </div>
      <div class="disclaimer-box mt-1"><span>💙</span><span>${data?.disclaimer || 'Always consult a doctor.'}</span></div>
    </div></div>`;
  }
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===== Chat-Based Order Functions =====

async function confirmChatOrder(medicineId, medicineName, quantity) {
  quantity = quantity || 1;
  const chatMessages = document.getElementById('chatMessages');

  // Show processing indicator
  const procId = 'proc-' + Date.now();
  chatMessages.innerHTML += `<div class="message message-bot" id="${procId}"><div class="message-avatar">🤖</div><div class="message-bubble"><span class="typing-dots"><span>.</span><span>.</span><span>.</span></span> Placing your order for ${quantity} unit(s)...</div></div>`;
  chatMessages.scrollTop = chatMessages.scrollHeight;

  const data = await apiCall('/medical/chat-order', {
    method: 'POST',
    body: JSON.stringify({ medicine_id: medicineId, quantity: quantity })
  });

  document.getElementById(procId)?.remove();

  if (data?.success) {
    // Order placed successfully
    const formattedMsg = renderBotMessage(data.message);
    chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
      <div class="order-success-card">
        <div class="order-success-icon">🎉</div>
        ${formattedMsg}
      </div>
      ${speakerBtnHtml()}
      <div class="mt-1 flex gap-1" style="flex-wrap:wrap">
        <a href="tracking.html?id=${data.order?.tracking_id || ''}" class="btn btn-primary btn-sm">📦 Track Order</a>
        <button class="btn btn-outline btn-sm" onclick="sendQuickReply('thank you')">👍 Thanks!</button>
      </div>
    </div></div>`;
    showToast('Order placed successfully! 🎉', 'success');

  } else if (data?.requires_prescription) {
    // Needs prescription — show upload UI
    const formattedMsg = renderBotMessage(data.message);
    const medId = data.medicine_id;
    const medName = data.medicine_name;
    chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
      <div class="message-bubble">${formattedMsg}</div>
      <div class="prescription-upload-area" id="rxUpload_${medId}">
        <div class="rx-upload-icon">📋</div>
        <p>Upload Prescription Image</p>
        <p class="rx-hint">File should contain medicine name & today's date<br>e.g. <code>${medName.split(' ')[0].split(',')[0].toLowerCase()}_${new Date().toISOString().split('T')[0]}.jpg</code></p>
        <input type="file" id="rxFile_${medId}" accept="image/*,.pdf" onchange="handleRxFileSelect(${medId}, this)" style="display:none">
        <button class="btn btn-outline btn-sm" onclick="document.getElementById('rxFile_${medId}').click()">📤 Choose File</button>
        <div id="rxFileName_${medId}" class="rx-file-name" style="display:none"></div>
        <button class="btn btn-primary btn-sm mt-1" id="rxSubmitBtn_${medId}" onclick="uploadPrescription(${medId})" style="display:none">✅ Upload & Verify Prescription</button>
      </div>
      ${speakerBtnHtml()}
    </div></div>`;

  } else {
    // Error
    const formattedMsg = renderBotMessage(data?.message || 'Something went wrong. Please try again.');
    chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
      <div class="order-reject-card">${formattedMsg}</div>
      ${speakerBtnHtml()}
    </div></div>`;
  }
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function handleRxFileSelect(medicineId, inputEl) {
  const file = inputEl.files[0];
  if (!file) return;

  const fileNameDiv = document.getElementById(`rxFileName_${medicineId}`);
  const submitBtn = document.getElementById(`rxSubmitBtn_${medicineId}`);

  if (fileNameDiv) {
    fileNameDiv.textContent = `📎 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    fileNameDiv.style.display = 'block';
  }
  if (submitBtn) {
    submitBtn.style.display = 'inline-flex';
  }
}

async function uploadPrescription(medicineId, quantity) {
  quantity = quantity || 1;
  const fileInput = document.getElementById(`rxFile_${medicineId}`);
  if (!fileInput || !fileInput.files[0]) {
    showToast('Please select a prescription file first.', 'error');
    return;
  }

  const chatMessages = document.getElementById('chatMessages');
  const submitBtn = document.getElementById(`rxSubmitBtn_${medicineId}`);
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Verifying...';
  }

  // User message showing upload
  chatMessages.innerHTML += `<div class="message message-user"><div class="message-avatar">😊</div><div class="message-bubble">📎 Uploading prescription: ${escapeHtml(fileInput.files[0].name)}</div></div>`;

  // Build form data
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('medicine_id', medicineId);
  formData.append('quantity', String(quantity));

  // Make the upload call (can't use apiCall because it sets Content-Type to JSON)
  const token = getToken();
  try {
    const res = await fetch(`${API_BASE}/medical/upload-prescription`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    const data = await res.json();

    if (data?.success) {
      // Prescription verified & order placed
      const formattedMsg = renderBotMessage(data.message);
      chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
        <div class="order-success-card">
          <div class="order-success-icon">🎉✔️</div>
          ${formattedMsg}
        </div>
        ${speakerBtnHtml()}
        <div class="mt-1 flex gap-1" style="flex-wrap:wrap">
          <a href="tracking.html?id=${data.order?.tracking_id || ''}" class="btn btn-primary btn-sm">📦 Track Order</a>
          <button class="btn btn-outline btn-sm" onclick="sendQuickReply('thank you')">👍 Thanks!</button>
        </div>
      </div></div>`;
      showToast('Prescription verified! Order placed! 🎉', 'success');
    } else {
      // Prescription rejected
      const formattedMsg = renderBotMessage(data.message || 'Prescription validation failed.');
      chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
        <div class="order-reject-card">${formattedMsg}</div>
        ${speakerBtnHtml()}
        <div class="mt-1">
          <button class="btn btn-outline btn-sm" onclick="document.getElementById('rxFile_${medicineId}').click()">📤 Try Another File</button>
        </div>
      </div></div>`;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = '✅ Upload & Verify Prescription';
      }
    }
  } catch (err) {
    console.error('Upload error:', err);
    chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
      <div class="order-reject-card">❌ Upload failed. Please check your connection and try again.</div>
    </div></div>`;
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = '✅ Upload & Verify Prescription';
    }
  }
  chatMessages.scrollTop = chatMessages.scrollHeight;
}


async function loadOrders() {
  const data = await apiCall('/orders/my-orders');
  const container = document.getElementById('ordersList');
  if (!data?.orders?.length) {
    container.innerHTML = `<div class="empty-state"><span class="empty-icon">📦</span><h3>No orders yet</h3><p>Visit our shop to order medicines</p><a href="shop.html" class="btn btn-primary mt-2">Browse Shop</a></div>`;
    return;
  }
  container.innerHTML = data.orders.map(o => `
    <div class="card mb-2">
      <div class="flex justify-between items-center" style="flex-wrap:wrap;gap:8px">
        <div><h3 style="font-weight:700">Order #${o.id}</h3><p style="font-size:0.8rem;color:var(--text-light)">Tracking: ${o.tracking_id}</p></div>
        <div style="text-align:right"><span class="status-badge ${o.status.toLowerCase().replace(/ /g,'-')}">${o.status}</span><p style="font-size:0.8rem;color:var(--text-light);margin-top:4px">₹${o.total_price.toFixed(2)}</p></div>
      </div>
      <div class="mt-1" style="font-size:0.85rem;color:var(--text-light)">${o.items.map(i => `${i.name} x${i.quantity}`).join(', ')}</div>
      <div class="mt-1"><a href="tracking.html?id=${o.tracking_id}" class="btn btn-outline btn-sm">Track Order</a></div>
    </div>
  `).join('');
}

function escapeHtml(text) {
  const d = document.createElement('div'); d.textContent = text; return d.innerHTML;
}

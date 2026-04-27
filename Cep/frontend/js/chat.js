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

  if (!data?.success) {
    // ===== ERROR CASE =====
    let formattedMsg = renderBotMessage(data?.message || "I'm not sure about that. Could you describe your symptoms differently?");
    chatMessages.innerHTML += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>
      <div class="message-bubble">${formattedMsg}</div>
      ${speakerBtnHtml()}
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
        ${QUICK_REPLIES.slice(0, 3).map(q => `<button class="quick-reply-chip" onclick="sendQuickReply('${q}')">${q}</button>`).join('')}
      </div>
    </div></div>`;

  } else if (data?.severity === "serious") {
    // ===== SERIOUS CONDITION - CONSULT DOCTOR =====
    let html = `<div class="message message-bot"><div class="message-avatar">🤖</div><div>`;
    html += `<div class="message-bubble" style="background:#FEF2F2;border-left:4px solid var(--danger)">`;
    html += `<strong>🏥 ${data.disease}</strong><br>`;
    html += `This condition requires professional medical attention.<br><br>`;
    html += `<strong>⚠️ Please consult a doctor immediately.</strong>`;
    html += `</div>`;
    if (data.advice) {
      html += `<p style="font-size:0.85rem;margin-top:10px;color:var(--text-light)"><strong>In the meantime:</strong> ${escapeHtml(data.advice)}</p>`;
    }
    html += `${speakerBtnHtml()}`;
    html += `<div class="mt-1"><a href="shop.html" class="btn btn-outline btn-sm">Browse Medicines</a></div>`;
    html += `</div></div>`;
    chatMessages.innerHTML += html;

  } else if (data?.severity === "unknown") {
    // ===== UNKNOWN SEVERITY - PHARMACIST REVIEW =====
    let html = `<div class="message message-bot"><div class="message-avatar">🤖</div><div>`;
    html += `<div class="message-bubble">`;
    html += `<strong>🔍 ${data.disease || 'Uncertain Condition'}</strong><br>`;
    html += `${escapeHtml(data.message)}<br><br>`;
    html += `A pharmacist will review your case and get back to you soon.`;
    html += `</div>`;
    if (data.advice) {
      html += `<p style="font-size:0.85rem;margin-top:10px;color:var(--text-light)"><strong>Advice:</strong> ${escapeHtml(data.advice)}</p>`;
    }
    if (data.pharmacist_request) {
      html += `<p style="font-size:0.78rem;margin-top:8px;color:var(--primary)"><strong>Request ID:</strong> ${data.pharmacist_request.id}</p>`;
    }
    html += `${speakerBtnHtml()}`;
    html += `<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
      ${QUICK_REPLIES.slice(0, 3).map(q => `<button class="quick-reply-chip" onclick="sendQuickReply('${q}')">${q}</button>`).join('')}
    </div>`;
    html += `</div></div>`;
    chatMessages.innerHTML += html;

  } else if (data?.success) {
    // ===== MILD CONDITION - SHOW MEDICINES =====
    let html = `<div class="message message-bot"><div class="message-avatar">🤖</div><div>`;
    
    // Main message
    html += `<div class="message-bubble">`;
    html += `<strong>✅ ${data.disease}</strong><br>`;
    html += `${escapeHtml(data.message)}<br><br>`;
    html += `Severity: <strong>${data.severity}</strong>`;
    html += `</div>`;

    // Advice
    if (data.advice) {
      html += `<p style="font-size:0.85rem;margin-top:10px;color:var(--text-light);background:#F0FDF4;padding:10px 12px;border-radius:10px">💡 ${escapeHtml(data.advice)}</p>`;
    }

    // Show OTC medicines if available
    if (data.otc_medicines && data.otc_medicines.length > 0) {
      html += `<div class="medical-result" style="margin-top:12px">`;
      html += `<h4>✅ Over-the-Counter Medicines</h4>`;
      html += `<p style="font-size:0.84rem;color:var(--text-light);margin-bottom:8px">No prescription needed</p>`;
      
      data.otc_medicines.forEach(m => {
        const catalog = m.catalog || {};
        html += `<div class="medicine-card-sm" style="margin-top:8px">`;
        html += `<h5>${escapeHtml(m.name)}</h5>`;
        if (catalog.generic_name) {
          html += `<p style="font-size:0.8rem;color:var(--text-light)">Generic: ${escapeHtml(catalog.generic_name)}</p>`;
        }
        html += `<p class="dosage">Dosage: ${escapeHtml(catalog.dosage || 'Use as directed')}</p>`;
        if (catalog.price) {
          html += `<p style="color:var(--primary);font-weight:600">₹${parseFloat(catalog.price).toFixed(2)}</p>`;
        }
        if (m.medicine_id) {
          html += `<button class="btn btn-primary btn-sm mt-1" onclick="confirmChatOrder(${m.medicine_id}, '${escapeHtml(m.name)}', 1)">🛒 Order</button>`;
        }
        html += `</div>`;
      });
      html += `</div>`;
    }

    // Show prescription medicines if available
    if (data.prescription_medicines && data.prescription_medicines.length > 0) {
      html += `<div class="medical-result" style="margin-top:12px">`;
      html += `<h4>⚠️ Prescription Medicines</h4>`;
      html += `<p style="font-size:0.84rem;color:var(--text-light);margin-bottom:8px">Requires valid prescription</p>`;
      
      data.prescription_medicines.forEach(m => {
        const catalog = m.catalog || {};
        html += `<div class="medicine-card-sm" style="margin-top:8px">`;
        html += `<h5>${escapeHtml(m.name)}</h5>`;
        if (catalog.generic_name) {
          html += `<p style="font-size:0.8rem;color:var(--text-light)">Generic: ${escapeHtml(catalog.generic_name)}</p>`;
        }
        html += `<p class="dosage">Dosage: ${escapeHtml(catalog.dosage || 'Use as directed')}</p>`;
        if (catalog.price) {
          html += `<p style="color:var(--primary);font-weight:600">₹${parseFloat(catalog.price).toFixed(2)}</p>`;
        }
        html += `<div class="prescription-required-badge">⚠️ Prescription Required</div>`;
        if (m.medicine_id) {
          html += `<button class="btn btn-primary btn-sm mt-1" onclick="uploadPrescriptionPrompt(${m.medicine_id}, '${escapeHtml(m.name)}')">📋 Upload Prescription</button>`;
        }
        html += `</div>`;
      });
      html += `</div>`;
    }

    if (!data.otc_medicines || data.otc_medicines.length === 0) {
      if (!data.prescription_medicines || data.prescription_medicines.length === 0) {
        html += `<p style="font-size:0.85rem;margin-top:10px;color:var(--text-light)">No medicines found for this condition in our database.</p>`;
      }
    }

    html += `${speakerBtnHtml()}`;
    html += `</div></div>`;
    chatMessages.innerHTML += html;

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

function uploadPrescriptionPrompt(medicineId, medicineName) {
  const chatMessages = document.getElementById('chatMessages');
  const fileInputId = `rxFile_prompt_${medicineId}_${Date.now()}`;
  
  let html = `<div class="message message-user"><div class="message-avatar">😊</div><div class="message-bubble">I want to upload a prescription for ${escapeHtml(medicineName)}</div></div>`;
  html += `<div class="message message-bot"><div class="message-avatar">🤖</div><div>`;
  html += `<div class="message-bubble">Sure! Let me help you upload your prescription for <strong>${escapeHtml(medicineName)}</strong>.</div>`;
  html += `<div class="prescription-upload-area" style="margin-top:12px" id="rxUpload_${medicineId}">`;
  html += `<div class="rx-upload-icon">📋</div>`;
  html += `<p>Upload Prescription Image</p>`;
  html += `<p class="rx-hint">File should contain medicine name & today's date</p>`;
  html += `<input type="file" id="${fileInputId}" accept="image/*,.pdf" onchange="handlePrescriptionFileSelect(${medicineId}, this, '${escapeHtml(medicineName)}')" style="display:none">`;
  html += `<button class="btn btn-outline btn-sm" onclick="document.getElementById('${fileInputId}').click()">📤 Choose File</button>`;
  html += `<div id="rxFileName_${medicineId}" class="rx-file-name" style="display:none"></div>`;
  html += `<button class="btn btn-primary btn-sm mt-1" id="rxSubmitBtn_${medicineId}" onclick="uploadPrescriptionFromChat(${medicineId}, '${escapeHtml(medicineName)}')" style="display:none">✅ Upload & Verify</button>`;
  html += `</div>`;
  html += `${speakerBtnHtml()}`;
  html += `</div></div>`;
  
  chatMessages.innerHTML += html;
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function handlePrescriptionFileSelect(medicineId, input, medicineName) {
  if (!input.files[0]) return;
  
  const fileNameDiv = document.getElementById(`rxFileName_${medicineId}`);
  const submitBtn = document.getElementById(`rxSubmitBtn_${medicineId}`);
  
  if (fileNameDiv) {
    fileNameDiv.textContent = `📎 ${input.files[0].name} (${(input.files[0].size / 1024).toFixed(1)} KB)`;
    fileNameDiv.style.display = 'block';
  }
  if (submitBtn) {
    submitBtn.style.display = 'inline-flex';
  }
}

async function uploadPrescriptionFromChat(medicineId, medicineName) {
  const fileInputId = document.querySelector(`button[onclick*="uploadPrescriptionFromChat(${medicineId}"]`).previousElementSibling.previousElementSibling.id;
  const fileInput = document.getElementById(fileInputId);
  
  if (!fileInput || !fileInput.files[0]) {
    showToast('Please select a prescription file first.', 'error');
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);
  formData.append('medicine_id', medicineId);

  const submitBtn = document.getElementById(`rxSubmitBtn_${medicineId}`);
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="loader"></span> Uploading...';

  try {
    const token = getToken();
    const res = await fetch(`http://127.0.0.1:5000/api/medical/upload-prescription`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData
    });

    const data = await res.json();
    const chatMessages = document.getElementById('chatMessages');

    if (data?.success) {
      let html = `<div class="message message-bot"><div class="message-avatar">🤖</div><div>`;
      html += `<div class="message-bubble" style="background:#F0FDF4;border-left:4px solid var(--primary)">`;
      html += `✅ <strong>Prescription Verified!</strong><br>`;
      html += `Your prescription for ${escapeHtml(medicineName)} has been verified successfully.`;
      html += `</div>`;
      
      if (data.prescription_submission_id) {
        html += `<p style="font-size:0.78rem;margin-top:8px;color:var(--primary)"><strong>Submission ID:</strong> ${data.prescription_submission_id}</p>`;
      }
      
      html += `<button class="btn btn-primary btn-sm mt-1" onclick="confirmChatOrder(${medicineId}, '${escapeHtml(medicineName)}', 1)">🛒 Add to Cart & Order</button>`;
      html += `${speakerBtnHtml()}`;
      html += `</div></div>`;
      chatMessages.innerHTML += html;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
      let html = `<div class="message message-bot"><div class="message-avatar">🤖</div><div>`;
      html += `<div class="message-bubble" style="background:#FEF2F2;border-left:4px solid var(--danger)">`;
      html += `❌ <strong>Prescription Not Readable</strong><br>`;
      html += `${escapeHtml(data.message || 'The prescription file could not be read clearly. Please try again with a clearer image.')}<br><br>`;
      html += `A pharmacist will review your submission shortly.`;
      html += `</div>`;
      html += `${speakerBtnHtml()}`;
      html += `</div></div>`;
      chatMessages.innerHTML += html;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  } catch (err) {
    console.error('Upload error:', err);
    showToast('Error uploading prescription. Please try again.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '✅ Upload & Verify';
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

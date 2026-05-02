/**
 * Messenger-style chat engine for intake
 * Drives the conversational UI - renders Avery messages, handles user input
 */
(function () {
  'use strict';

  // ── Config ─────────────────────────────────────────────────────────
  let API_URL = '';
  let SUBMIT_URL = '';
  let currentTurnId = null;

  // ── DOM refs ───────────────────────────────────────────────────────
  const $ = id => document.getElementById(id);
  let msgArea, quickReplies, msgInput, msgSend, progressChip, progressBar;

  // ── Bootstrap ──────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', async () => {
    msgArea      = $('chat-messages');
    quickReplies = $('quick-replies');
    msgInput     = $('msg-input');
    msgSend      = $('msg-send');
    progressChip = $('progress-chip');
    progressBar  = $('progress-bar');

    const meta = JSON.parse($('api-meta').textContent);
    API_URL = meta.apiUrl;
    SUBMIT_URL = meta.submitUrl;

    // Load initial state
    try {
      const state = await apiFetch('GET', null);

      // Replay history (no animation)
      state.history.forEach(entry => appendBubble(entry.role, entry.text, false));

      // Show current turn
      if (state.current) {
        await renderTurn(state.current, state.progress, false);
      }
    } catch (err) {
      console.error('Failed to load messenger state:', err);
      appendBubble('avery', 'Something went wrong loading the chat. Please refresh the page.', true);
    }

    // Wire input events
    msgSend.addEventListener('click', sendUserInput);
    msgInput.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendUserInput();
      }
    });
  });

  // ── Rendering ──────────────────────────────────────────────────────

  function appendBubble(role, text, animate) {
    const row = document.createElement('div');
    row.className = `bubble-row ${role === 'user' ? 'user-row' : ''}`;

    const b = document.createElement('div');
    b.className = `bubble ${role === 'user' ? 'user brand' : 'coach'}${animate ? ' fade-up' : ''}`;
    b.textContent = text;
    row.appendChild(b);

    if (role === 'user' && animate && currentTurnId) {
      const edit = document.createElement('span');
      edit.className = 'bubble-edit';
      edit.textContent = 'edit';
      edit.dataset.turnId = currentTurnId;
      // TODO: implement edit functionality
      row.appendChild(edit);
    }

    msgArea.appendChild(row);
    scrollBottom();
  }

  function showTyping() {
    const b = document.createElement('div');
    b.className = 'bubble coach';
    b.id = 'typing-indicator';
    b.innerHTML = '<span class="typing-dots"><span></span><span></span><span></span></span>';
    msgArea.appendChild(b);
    scrollBottom();
    return b;
  }

  function hideTyping() {
    const t = $('typing-indicator');
    if (t) t.remove();
  }

  async function renderTurn(turn, progress, animate) {
    if (!turn || !turn.id) return;

    currentTurnId = turn.id;

    // Animate Avery messages one by one
    for (const text of (turn.avery_messages || [])) {
      if (animate) {
        const typingEl = showTyping();
        await sleep(600 + Math.min(text.length * 12, 800));
        hideTyping();
      }
      appendBubble('avery', text, animate);
      if (animate) await sleep(150);
    }

    // Update progress
    if (progress) updateProgress(progress);

    // Render input area
    if (turn.input) {
      setInputMode(turn.input);
    }

    // Auto-advance turns with no input
    if (turn.input && turn.input.type === 'none') {
      await sleep(800);
      await sendAnswer('__auto__', '');
    }

    scrollBottom();
  }

  function setInputMode(inputConfig) {
    const { type, chips = [], placeholder = 'Type a message…', card_html, card_type } = inputConfig;

    // Show/hide quick-reply chips
    quickReplies.innerHTML = '';
    let displayChips = chips;

    // Add "Skip" chip for skip_chips type
    if (type === 'skip_chips' && chips.length > 0) {
      displayChips = [...chips, { label: 'Skip', value: '__skip__' }];
    }

    if (displayChips.length > 0) {
      displayChips.forEach(chip => {
        const btn = document.createElement('button');
        btn.className = 'quick-reply';
        btn.type = 'button';

        const label = typeof chip === 'string' ? chip : chip.label;
        const value = typeof chip === 'string' ? chip : chip.value;

        btn.textContent = label;
        btn.addEventListener('click', () => sendAnswer(value, label));
        quickReplies.appendChild(btn);
      });
      quickReplies.hidden = false;
    } else {
      quickReplies.hidden = true;
    }

    // Show/hide text input
    const hasTextInput = ['text', 'date', 'number', 'skip_chips', 'email', 'phone', 'currency'].includes(type);
    msgInput.style.display = hasTextInput ? '' : 'none';
    msgSend.style.display = hasTextInput ? '' : 'none';
    msgInput.placeholder = placeholder;
    if (type === 'email') {
      msgInput.type = 'email';
      msgInput.inputMode = 'email';
    } else if (type === 'phone') {
      msgInput.type = 'tel';
      msgInput.inputMode = 'tel';
    } else if (type === 'date') {
      msgInput.type = 'text';
      msgInput.inputMode = 'numeric';
    } else if (type === 'currency' || type === 'number') {
      msgInput.type = 'text';
      msgInput.inputMode = 'numeric';
    } else {
      msgInput.type = 'text';
      msgInput.inputMode = 'text';
    }
    msgInput.value = '';
    if (hasTextInput) msgInput.focus();

    // Render inline cards (consent, prescription)
    renderInlineCard(inputConfig);
  }

  function renderInlineCard(inputConfig) {
    // Remove any existing inline card
    const existing = msgArea.querySelector('.chat-card');
    if (existing) existing.remove();

    if (!inputConfig.card_html) return;

    const card = document.createElement('div');
    card.className = 'chat-card';
    card.innerHTML = inputConfig.card_html;
    msgArea.appendChild(card);

    // Wire up prescription card
    if (inputConfig.card_type === 'prescription') {
      console.log('Rendering prescription card', { card, cardId: card.id });
      wirePrescriptionCard(card);
      const drugRoot = card.querySelector('.drug-search-root');
      console.log('Found drug root:', drugRoot, 'initDrugSearch available:', typeof window.initDrugSearch);
      if (drugRoot && typeof window.initDrugSearch === 'function') {
        console.log('Calling window.initDrugSearch');
        window.initDrugSearch(drugRoot);
      } else {
        console.warn('Failed to call initDrugSearch', { drugRoot: !!drugRoot, initDrugSearchType: typeof window.initDrugSearch });
      }
    }

    // Wire up consent form
    if (inputConfig.card_type === 'consent') {
      const form = card.querySelector('.consent-form');
      if (form) {
        form.addEventListener('submit', e => {
          e.preventDefault();
          handleConsentSubmit(form);
        });
        // Also add a submit button since the form isn't in a traditional flow
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.className = 'btn brand lg full';
        submitBtn.style.marginTop = '12px';
        submitBtn.textContent = 'Submit';
        form.parentElement.appendChild(submitBtn);
        submitBtn.addEventListener('click', e => {
          e.preventDefault();
          handleConsentSubmit(form);
        });
      }
    }

    // Wire up household member form
    if (inputConfig.card_type === 'household_members') {
      wireHouseholdForm(card);
    }

    scrollBottom();
  }

  // ── Sending ────────────────────────────────────────────────────────

  function sendUserInput() {
    const val = msgInput.value.trim();
    if (!val) return;
    sendAnswer(val, val);
  }

  async function sendAnswer(value, displayText) {
    // Optimistically update UI
    msgInput.value = '';
    quickReplies.hidden = true;
    msgInput.style.display = 'none';
    msgSend.style.display = 'none';

    // Show typing indicator
    showTyping();
    const t0 = Date.now();

    try {
      const result = await apiFetch('POST', { turn_id: currentTurnId, answer: value });

      // Enforce minimum 500ms typing indicator
      const elapsed = Date.now() - t0;
      if (elapsed < 500) await sleep(500 - elapsed);
      hideTyping();

      if (!result.ok) {
        // Validation error
        if (result.error) {
          appendBubble('avery', result.error, true);
        }
        // Re-show input for retry
        if (result.next) {
          await renderTurn(result.next, null, true);
        } else {
          setInputMode({ type: 'text', chips: [] });
        }
        return;
      }

      const userText = result.user_display || displayText || '';
      if (userText && userText !== '__auto__' && userText !== '__skip__') {
        appendBubble('user', userText, true);
      }

      if (result.done) {
        // All done - redirect
        window.location.href = result.redirect_url;
        return;
      }

      // Normal flow: show next turn
      if (result.next) {
        await renderTurn(result.next, result.progress, true);
      }

    } catch (err) {
      hideTyping();
      console.error('Failed to submit answer:', err);
      appendBubble('avery', 'Something went wrong. Please try again.', true);
      // Re-show input for retry
      setInputMode({ type: 'text', chips: [] });
    }
  }

  async function handleConsentSubmit(form) {
    // Show user bubble
    appendBubble('user', 'Consent submitted', true);

    // Clear footer
    const msgBar = $('msg-bar');
    msgBar.style.display = 'none';

    // Show typing
    const typing = showTyping();
    const t0 = Date.now();

    try {
      // The form already has csrfmiddlewaretoken in it, but let's make sure
      const formData = new FormData(form);
      formData.set('_chat', '1');

      const res = await fetch(SUBMIT_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() },
        body: formData,
      });
      const json = await res.json();

      const elapsed = Date.now() - t0;
      if (elapsed < 500) await sleep(500 - elapsed);
      hideTyping();

      if (json.ok && json.done) {
        window.location.href = json.redirect_url;
      } else {
        appendBubble('avery', 'There was an issue submitting. Please try again.', true);
        msgBar.style.display = '';
      }
    } catch (err) {
      hideTyping();
      console.error('Failed to submit consent:', err);
      appendBubble('avery', 'Something went wrong. Please try again.', true);
      msgBar.style.display = '';
    }
  }

  function wireHouseholdForm(card) {
    // Wire up add forms
    const addForms = card.querySelectorAll('.household-add-form');
    addForms.forEach(form => {
      form.addEventListener('submit', e => {
        e.preventDefault();
        handleHouseholdMemberAdd(form);
      });
    });

    // Wire up remove buttons
    const removeButtons = card.querySelectorAll('.household-remove-btn');
    removeButtons.forEach(btn => {
      btn.addEventListener('click', e => {
        e.preventDefault();
        handleHouseholdMemberRemove(btn);
      });
    });

    // Wire up done button
    const doneBtn = card.querySelector('.household-done-btn');
    if (doneBtn) {
      doneBtn.addEventListener('click', e => {
        e.preventDefault();
        sendAnswer('__household_done__', 'Done adding members');
      });
    }
  }

  async function handleHouseholdMemberAdd(form) {
    const role = form.dataset.role;
    const firstName = form.querySelector('[name="first_name"]').value.trim();
    const lastName = form.querySelector('[name="last_name"]').value.trim();
    const dob = form.querySelector('[name="date_of_birth"]').value.trim();

    if (!firstName || !dob) {
      appendBubble('avery', 'Please fill in the name and date of birth.', true);
      return;
    }

    try {
      const result = await apiFetch('POST', {
        turn_id: currentTurnId,
        action: 'household_add',
        role,
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dob,
      });

      if (result.ok && result.card_html) {
        // Refresh the card
        const card = msgArea.querySelector('#household-form-card');
        if (card && card.parentElement) {
          const newCard = document.createElement('div');
          newCard.className = 'chat-card';
          newCard.innerHTML = result.card_html;
          card.parentElement.replaceChild(newCard, card);
          wireHouseholdForm(newCard);
          scrollBottom();
        }
      } else if (result.error) {
        appendBubble('avery', result.error, true);
      }
    } catch (err) {
      console.error('Failed to add household member:', err);
      appendBubble('avery', 'Something went wrong. Please try again.', true);
    }
  }

  async function handleHouseholdMemberRemove(btn) {
    const role = btn.dataset.role;
    const tempId = btn.dataset.tempId;

    try {
      const result = await apiFetch('POST', {
        turn_id: currentTurnId,
        action: 'household_remove',
        role,
        temp_id: tempId,
      });

      if (result.ok && result.card_html) {
        // Refresh the card
        const card = msgArea.querySelector('#household-form-card');
        if (card && card.parentElement) {
          const newCard = document.createElement('div');
          newCard.className = 'chat-card';
          newCard.innerHTML = result.card_html;
          card.parentElement.replaceChild(newCard, card);
          wireHouseholdForm(newCard);
          scrollBottom();
        }
      } else if (result.error) {
        appendBubble('avery', result.error, true);
      }
    } catch (err) {
      console.error('Failed to remove household member:', err);
      appendBubble('avery', 'Something went wrong. Please try again.', true);
    }
  }

  function wirePrescriptionCard(card) {
    const innerCard = card.querySelector('[id^="prescription-card-"]');
    const tempId = innerCard ? innerCard.id.replace('prescription-card-', '') : '';

    // Wire remove buttons
    const removeButtons = card.querySelectorAll('.prescription-remove-btn');
    removeButtons.forEach(btn => {
      btn.addEventListener('click', e => {
        e.preventDefault();
        handlePrescriptionRemove(tempId, parseInt(btn.dataset.drugIndex));
      });
    });

    // Wire add medication button
    const addBtn = card.querySelector('.prescription-add-medication-btn');
    if (addBtn) {
      addBtn.addEventListener('click', e => {
        e.preventDefault();
        handlePrescriptionAdd(card, tempId);
      });
    }

    // Wire done button
    const doneBtn = card.querySelector('.prescription-done-btn');
    if (doneBtn) {
      doneBtn.addEventListener('click', e => {
        e.preventDefault();
        sendAnswer('__prescription_done__', '');
      });
    }
  }

  async function handlePrescriptionAdd(card, tempId) {
    console.log('handlePrescriptionAdd called', { card, tempId });
    const drugName = card.querySelector('input[name="selected_drug_name"]')?.value.trim() || '';
    const drugId = card.querySelector('input[name="selected_drug_id"]')?.value || '';
    const normalizedName = card.querySelector('input[name="normalized_drug_name"]')?.value || '';
    const source = card.querySelector('input[name="source"]')?.value || '';

    console.log('Drug fields:', { drugName, drugId, normalizedName, source });

    if (!drugName) {
      appendBubble('avery', 'Please search for and select a medication first.', true);
      return;
    }

    try {
      console.log('Sending prescription_add request');
      const result = await apiFetch('POST', {
        turn_id: currentTurnId,
        action: 'prescription_add',
        temp_id: tempId,
        drug_name: drugName,
        drug_id: drugId,
        normalized_name: normalizedName,
        source: source,
      });

      console.log('prescription_add response:', result);

      if (result.ok && result.card_html) {
        // Refresh the card
        const oldCard = msgArea.querySelector(`#prescription-card-${tempId}`);
        if (oldCard && oldCard.parentElement) {
          const newCard = document.createElement('div');
          newCard.className = 'chat-card';
          newCard.innerHTML = result.card_html;
          oldCard.parentElement.replaceChild(newCard, oldCard);
          wirePrescriptionCard(newCard);
          const drugRoot = newCard.querySelector('.drug-search-root');
          if (drugRoot && typeof window.initDrugSearch === 'function') {
            window.initDrugSearch(drugRoot);
          }
          scrollBottom();
        }
      } else if (result.error) {
        appendBubble('avery', result.error, true);
      }
    } catch (err) {
      console.error('Failed to add medication:', err);
      appendBubble('avery', 'Something went wrong. Please try again.', true);
    }
  }

  async function handlePrescriptionRemove(tempId, drugIndex) {
    try {
      const result = await apiFetch('POST', {
        turn_id: currentTurnId,
        action: 'prescription_remove',
        temp_id: tempId,
        drug_index: drugIndex,
      });

      if (result.ok && result.card_html) {
        // Refresh the card
        const oldCard = msgArea.querySelector(`#prescription-card-${tempId}`);
        if (oldCard && oldCard.parentElement) {
          const newCard = document.createElement('div');
          newCard.className = 'chat-card';
          newCard.innerHTML = result.card_html;
          oldCard.parentElement.replaceChild(newCard, oldCard);
          wirePrescriptionCard(newCard);
          const drugRoot = newCard.querySelector('.drug-search-root');
          if (drugRoot && typeof window.initDrugSearch === 'function') {
            window.initDrugSearch(drugRoot);
          }
          scrollBottom();
        }
      } else if (result.error) {
        appendBubble('avery', result.error, true);
      }
    } catch (err) {
      console.error('Failed to remove medication:', err);
      appendBubble('avery', 'Something went wrong. Please try again.', true);
    }
  }

  // ── Utilities ──────────────────────────────────────────────────────

  async function apiFetch(method, body) {
    const opts = {
      method,
      headers: {
        'X-CSRFToken': getCsrf(),
      },
    };
    if (body) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(API_URL, opts);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  }

  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function updateProgress(progress) {
    if (progressChip) {
      progressChip.textContent = `${progress.index} of ${progress.total}`;
    }
    if (progressBar) {
      const pct = Math.round((progress.index / (progress.total || 1)) * 100);
      progressBar.style.width = `${pct}%`;
    }
  }

  function scrollBottom() {
    msgArea.scrollTop = msgArea.scrollHeight;
  }

  function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

})();

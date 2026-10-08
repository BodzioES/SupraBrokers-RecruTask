// Master-detail: click a row to load details via the DRF API.
// Single modal handles both add (empty) and edit (prefilled), normal POST.
(function () {
  const detail = document.getElementById('contact-detail');
  const modalEl = document.getElementById('contact-modal');
  const form = document.getElementById('contact-form');
  const modalTitle =
    document.getElementById('contact-modal-title-text') ||
    document.getElementById('contact-modal-title');
  const deleteModalEl = document.getElementById('delete-modal');
  const deleteForm = document.getElementById('delete-form');
  const deleteName = document.getElementById('delete-name');
  if (!detail || !modalEl || !form) return;

  let modalInstance = null;
  let deleteModalInstance = null;
  let activeRow = null;
  const cache = new Map();

  function getModal() {
    if (!modalInstance) modalInstance = new bootstrap.Modal(modalEl);
    return modalInstance;
  }

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Same initials + color algorithm as Contact.initials/avatar_color.
  function initialsAvatar(firstName, lastName, large) {
    const first = (firstName || '').trim().charAt(0).toUpperCase();
    const last = (lastName || '').trim().charAt(0).toUpperCase();
    const combined = `${firstName || ''}${lastName || ''}`.toLowerCase();
    let total = 0;
    for (const char of combined) total += char.codePointAt(0);
    const color = total % 8;
    return `<span class="avatar ${large ? 'avatar-lg' : ''} avatar-c${color}" aria-hidden="true">${esc(first + last)}</span>`;
  }

  function statusClass(name) {
    const slug = String(name || '')
      .toLowerCase()
      .replace(/[\s_]+/g, '_')
      .replace(/[^a-z0-9_-]/g, '');
    return ['new', 'in_progress', 'lost', 'outdated'].includes(slug)
      ? `status-${slug}`
      : 'status-unknown';
  }

  // Mirror of ContactStatus.display_name: 'in_progress' becomes 'In progress'.
  function displayName(name) {
    const text = String(name || '').replace(/_/g, ' ');
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  function renderDetail(data) {
    const added = (data.created_at || '').slice(0, 16).replace('T', ' ');
    detail.innerHTML = `
      <div class="d-flex align-items-center gap-3 mb-2">
        ${initialsAvatar(data.first_name, data.last_name, true)}
        <div>
          <h2 class="h5 mb-1 fw-semibold">${esc(data.first_name)} ${esc(data.last_name)}</h2>
          <span class="status-badge ${statusClass(data.status_name)}">${esc(displayName(data.status_name))}</span>
        </div>
      </div>
      <div class="mb-3">
        <div class="detail-row"><i data-lucide="phone"></i>
          <a href="tel:${esc(data.phone)}">${esc(data.phone)}</a></div>
        <div class="detail-row"><i data-lucide="mail"></i>
          <a href="mailto:${esc(data.email)}">${esc(data.email)}</a></div>
        <div class="detail-row"><i data-lucide="map-pin"></i> ${esc(data.city)}</div>
        <div class="detail-row">
          <span class="weather-slot" data-city="${esc(data.city)}">…</span></div>
        <div class="detail-row text-muted small"><i data-lucide="calendar"></i> Added: ${esc(added)}</div>
        <div class="detail-row text-muted small"><i data-lucide="share-2"></i> Shared: ${data.is_shared ? 'Yes' : 'No'}</div>
      </div>
      <div class="d-flex flex-wrap gap-2">
        <button class="btn btn-primary btn-sm" data-action="edit" data-id="${data.id}">
          <i data-lucide="pencil"></i>Edit
        </button>
        <button class="btn btn-delete-solid btn-sm" data-action="delete" data-id="${data.id}" title="Delete" aria-label="Delete">
          <i data-lucide="trash-2"></i>
        </button>
      </div>`;
    if (window.lucide) window.lucide.createIcons();
    if (window.refreshWeather) window.refreshWeather(detail);
  }

  const detailColumn = document.getElementById('detail-column');
  const detailBackdrop = document.getElementById('detail-backdrop');
  const detailClose = document.querySelector('.detail-close');
  const isMobile = () => window.matchMedia('(max-width: 991px)').matches;

  function closeDrawer() {
    if (detailColumn) detailColumn.classList.remove('open');
    if (detailBackdrop) detailBackdrop.classList.remove('visible');
    document.body.classList.remove('drawer-open');
  }

  if (detailBackdrop) {
    detailBackdrop.addEventListener('click', closeDrawer);
  }
  if (detailClose) {
    detailClose.addEventListener('click', closeDrawer);
  }
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeDrawer();
  });

  async function showDetail(id, row) {
    if (activeRow) activeRow.classList.remove('active');
    activeRow = row || null;
    if (activeRow) activeRow.classList.add('active');
    // On mobile the detail panel slides in as a drawer.
    if (isMobile() && detailColumn) {
      detailColumn.classList.add('open');
      if (detailBackdrop) detailBackdrop.classList.add('visible');
      document.body.classList.add('drawer-open');
    }
    // Details already fetched once are reused, no second API call.
    if (cache.has(id)) {
      renderDetail(cache.get(id));
      return;
    }
    detail.innerHTML = `<div class="text-center text-muted py-5">
      <div class="spinner-border spinner-border-sm"></div> Loading…</div>`;
    try {
      const response = await fetch(`/api/contacts/${id}/`);
      if (!response.ok) throw new Error('not found');
      const data = await response.json();
      cache.set(id, data);
      renderDetail(data);
    } catch (e) {
      detail.innerHTML = `<div class="alert alert-warning mb-0">
        Could not load details.</div>`;
    }
  }

  function setField(name, value) {
    const input = form.querySelector(`[name="${name}"]`);
    if (input) input.value = value == null ? '' : value;
  }

  function openModal(mode, data) {
    if (mode === 'edit' && data) {
      modalTitle.textContent = 'Edit contact';
      form.action = `/${data.id}/edit/`;
      setField('first_name', data.first_name);
      setField('last_name', data.last_name);
      setField('phone', data.phone);
      setField('email', data.email);
      setField('city', data.city);
      setField('status', data.status);
      const shared = form.querySelector('[name="is_shared"]');
      if (shared) shared.checked = false;
    } else {
      modalTitle.textContent = 'Add contact';
      form.action = '/add/';
      form.reset();
    }
    form.querySelectorAll('.is-valid, .is-invalid').forEach((el) => {
      el.classList.remove('is-valid', 'is-invalid');
    });
    // Programmatic fill fires no input events, so refresh the preview manually.
    form.dispatchEvent(new Event('avatar-refresh'));
    getModal().show();
  }

  document.querySelectorAll('.contact-row[data-id]').forEach((row) => {
    row.addEventListener('click', (event) => {
      if (event.target.closest('a, button')) return;
      showDetail(row.dataset.id, row);
    });
  });

  const addButton = document.getElementById('add-contact-btn');
  if (addButton) {
    addButton.addEventListener('click', () => openModal('add'));
  }
  document.querySelectorAll('[data-add-empty]').forEach((button) => {
    button.addEventListener('click', () => openModal('add'));
  });

  // Autofocus the first field every time the modal opens.
  modalEl.addEventListener('shown.bs.modal', () => {
    const first = form.querySelector('[name="first_name"]');
    if (first) first.focus();
  });

  function openDeleteModal(data) {
    if (!deleteModalEl || !deleteForm || !deleteName) return;
    if (!deleteModalInstance) deleteModalInstance = new bootstrap.Modal(deleteModalEl);
    deleteForm.action = `/${data.id}/delete/`;
    deleteName.textContent = `${data.first_name} ${data.last_name} (${data.city})`;
    deleteModalInstance.show();
  }

  // One listener for buttons rendered later inside the detail panel.
  detail.addEventListener('click', (event) => {
    const button = event.target.closest('[data-action]');
    if (!button) return;
    const data = cache.get(button.dataset.id);
    if (!data) return;
    if (button.dataset.action === 'edit') openModal('edit', data);
    if (button.dataset.action === 'delete') openDeleteModal(data);
  });
})();

// Master-detail: click a row to load details via the DRF API.
// Single modal handles both add (empty) and edit (prefilled), normal POST.
(function () {
  const detail = document.getElementById('contact-detail');
  const modalEl = document.getElementById('contact-modal');
  const form = document.getElementById('contact-form');
  const modalTitle = document.getElementById('contact-modal-title');
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

  function avatarLg() {
    return `<span class="avatar avatar-lg" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="40" height="40" fill="currentColor">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
      </svg></span>`;
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
        ${avatarLg()}
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
        <div class="detail-row"><i data-lucide="cloud-sun"></i>
          <span class="weather-slot text-muted small" data-city="${esc(data.city)}">…</span></div>
        <div class="detail-row text-muted small"><i data-lucide="calendar"></i> Added: ${esc(added)}</div>
      </div>
      <div class="d-flex flex-wrap gap-2">
        <a class="btn btn-primary btn-sm" href="tel:${esc(data.phone)}">
          <i data-lucide="phone"></i>Call
        </a>
        <a class="btn btn-outline-secondary btn-sm" href="mailto:${esc(data.email)}">
          <i data-lucide="mail"></i>Email
        </a>
        <button class="btn btn-outline-secondary btn-sm" data-action="edit" data-id="${data.id}">
          <i data-lucide="pencil"></i>Edit
        </button>
        <button class="btn btn-outline-danger btn-sm btn-icon" data-action="delete" data-id="${data.id}" title="Delete">
          <i data-lucide="trash-2"></i>
        </button>
      </div>`;
    if (window.lucide) window.lucide.createIcons();
    if (window.refreshWeather) window.refreshWeather(detail);
  }

  async function showDetail(id, row) {
    if (activeRow) activeRow.classList.remove('active');
    activeRow = row || null;
    if (activeRow) activeRow.classList.add('active');
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

  function openDeleteModal(data) {
    if (!deleteModalEl || !deleteForm || !deleteName) return;
    if (!deleteModalInstance) deleteModalInstance = new bootstrap.Modal(deleteModalEl);
    deleteForm.action = `/${data.id}/delete/`;
    deleteName.textContent = `${data.first_name} ${data.last_name} (${data.city})`;
    deleteModalInstance.show();
  }

  detail.addEventListener('click', (event) => {
    const button = event.target.closest('[data-action]');
    if (!button) return;
    const data = cache.get(button.dataset.id);
    if (!data) return;
    if (button.dataset.action === 'edit') openModal('edit', data);
    if (button.dataset.action === 'delete') openDeleteModal(data);
  });
})();

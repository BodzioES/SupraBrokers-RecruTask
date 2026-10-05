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

  function renderDetail(data) {
    const added = (data.created_at || '').slice(0, 16).replace('T', ' ');
    detail.innerHTML = `
      <div class="d-flex align-items-center gap-3 mb-3">
        ${avatarLg()}
        <div>
          <h2 class="h5 mb-0">${esc(data.first_name)} ${esc(data.last_name)}</h2>
          <span class="badge text-bg-secondary">${esc(data.status_name || '')}</span>
        </div>
      </div>
      <ul class="list-group list-group-flush mb-3">
        <li class="list-group-item"><i class="bi bi-telephone"></i>
          <a href="tel:${esc(data.phone)}">${esc(data.phone)}</a></li>
        <li class="list-group-item"><i class="bi bi-envelope"></i>
          <a href="mailto:${esc(data.email)}">${esc(data.email)}</a></li>
        <li class="list-group-item"><i class="bi bi-geo-alt"></i> ${esc(data.city)}</li>
        <li class="list-group-item"><i class="bi bi-cloud-sun"></i>
          <span class="weather-slot text-muted small" data-city="${esc(data.city)}">…</span></li>
        <li class="list-group-item text-muted small">Added: ${esc(added)}</li>
      </ul>
      <div class="d-flex gap-2">
        <button class="btn btn-primary btn-sm" data-action="edit" data-id="${data.id}">
          <i class="bi bi-pencil"></i> Edit
        </button>
        <button class="btn btn-outline-danger btn-sm" data-action="delete" data-id="${data.id}">
          <i class="bi bi-trash"></i> Delete
        </button>
      </div>`;
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

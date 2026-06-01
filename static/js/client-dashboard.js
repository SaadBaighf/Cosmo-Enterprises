// Smooth animations on page load
document.addEventListener('DOMContentLoaded', function () {
  // DELETE LOGIC
  const deleteButtons = document.querySelectorAll('.delete-btn');
  const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
  const deleteClientName = document.getElementById('delete-client-name');
  const deleteClientId = document.getElementById('delete-client-id');

  deleteButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      const name = this.getAttribute('data-client-name');
      const id = this.getAttribute('data-client-id');
      deleteClientName.textContent = name;
      deleteClientId.value = id;
      deleteModal.show();
    });
  });

  // EDIT/ADD LOGIC
  const editButtons = document.querySelectorAll('.edit-client-btn');
  const modalTitle = document.getElementById('modal-title');
  const modalSubmitBtn = document.getElementById('modal-submit-btn');
  const formClientId = document.getElementById('form-client-id');
  const avatarPreview = document.getElementById('avatar-preview');

  // Reset form when modal closes
  document.getElementById('addClientModal').addEventListener('hidden.bs.modal', function () {
    document.getElementById('clientForm').reset();
    formClientId.value = '';
    avatarPreview.classList.remove('show-preview');
    setTimeout(() => {
      avatarPreview.style.display = 'none';
    }, 300);
    modalTitle.textContent = 'Add New Client';
    modalSubmitBtn.textContent = 'Save Client';
    modalSubmitBtn.disabled = false; // Re-enable button
    modalSubmitBtn.classList.remove('btn-secondary');
    modalSubmitBtn.classList.add('btn-primary');
  });

  // Handle Edit Button Click
  editButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      const id = this.getAttribute('data-id');
      const name = this.getAttribute('data-name');
      const email = this.getAttribute('data-email');
      const phone = this.getAttribute('data-phone');
      const company = this.getAttribute('data-company');
      const isActive = this.getAttribute('data-is_active') === 'true';
      const avatarUrl = this.getAttribute('data-avatar-url');

      // Fill form
      formClientId.value = id;
      document.getElementById('id_name').value = name;
      document.getElementById('id_email').value = email;
      document.getElementById('id_phone').value = phone;
      document.getElementById('id_company').value = company;
      document.getElementById('id_is_active').checked = isActive;

      // Handle avatar preview
      if (avatarUrl) {
        avatarImg.src = avatarUrl;
        avatarPreview.style.display = 'block';
        setTimeout(() => {
          avatarPreview.classList.add('show-preview');
        }, 10);
      } else {
        avatarPreview.classList.remove('show-preview');
        setTimeout(() => {
          avatarPreview.style.display = 'none';
        }, 300);
      }

      // Update modal title & button
      modalTitle.textContent = 'Edit Client';
      modalSubmitBtn.textContent = 'Update Client';
      
      // Enable button for existing clients (assume valid data)
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.classList.remove('btn-secondary');
      modalSubmitBtn.classList.add('btn-primary');
    });
  });
  
  // SEARCH - REMOVED AUTO-SUBMIT TO PREVENT RELOAD
  const searchInput = document.querySelector('input[name="search"]');
  if (searchInput) {
    searchInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        this.form.submit();
      }
    });
  }

  // ✅ REAL-TIME VALIDATION WITH DISABLED BUTTON
  const clientForm = document.getElementById('clientForm');
  if (clientForm) {
    const nameField = document.getElementById('id_name');
    const emailField = document.getElementById('id_email');
    const phoneField = document.getElementById('id_phone');
    const submitBtn = document.getElementById('modal-submit-btn');

    // Function to check if all fields are valid
    function validateForm() {
      let isValid = true;
      
      // Validate Name (required, min 2 chars, letters only)
      const nameValue = nameField.value.trim();
      if (!nameValue || nameValue.length < 2 || !/^[a-zA-Z\s]+$/.test(nameValue)) {
        isValid = false;
        nameField.classList.add('is-invalid');
      } else {
        nameField.classList.remove('is-invalid');
      }
      
      // Validate Email (if provided)
      const emailValue = emailField.value.trim();
      if (emailValue && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue)) {
        isValid = false;
        emailField.classList.add('is-invalid');
      } else {
        emailField.classList.remove('is-invalid');
      }
      
      // Validate Phone (if provided)
      const phoneValue = phoneField.value.trim();
      if (phoneValue && !/^\+?[\d\s\-\(\)]{10,15}$/.test(phoneValue)) {
        isValid = false;
        phoneField.classList.add('is-invalid');
      } else {
        phoneField.classList.remove('is-invalid');
      }
      
      // Enable/disable button based on validation
      if (isValid) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('btn-secondary');
        submitBtn.classList.add('btn-primary');
      } else {
        submitBtn.disabled = true;
        submitBtn.classList.remove('btn-primary');
        submitBtn.classList.add('btn-secondary');
      }
    }

    // Run validation on every input change
    nameField.addEventListener('input', validateForm);
    emailField.addEventListener('input', validateForm);
    phoneField.addEventListener('input', validateForm);
    
    // Initialize validation on page load
    validateForm();
  }
});
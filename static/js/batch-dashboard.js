document.addEventListener('DOMContentLoaded', function () {
  // 1. Handle "Complete / Update Status" Modal
  const updateButtons = document.querySelectorAll('.update-status-btn');
  const updateBatchIdInput = document.getElementById('update-batch-id');
  const updateBatchNumText = document.getElementById('update-batch-num');

  updateButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      const batchId = this.getAttribute('data-batch-id');
      const batchNum = this.getAttribute('data-batch-num');
      
      updateBatchIdInput.value = batchId;
      updateBatchNumText.textContent = batchNum;
    });
  });

  // 2. Handle "Delete" Modal
  const deleteButtons = document.querySelectorAll('.delete-btn');
  const deleteBatchIdInput = document.getElementById('delete-batch-id');
  const deleteBatchNumText = document.getElementById('delete-batch-num');

  deleteButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      const batchId = this.getAttribute('data-batch-id');
      const batchNum = this.getAttribute('data-batch-num');
      
      deleteBatchIdInput.value = batchId;
      deleteBatchNumText.textContent = batchNum;
    });
  });
});
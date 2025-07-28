
function toggleEdit(btn) {
  const parent = btn.closest('.record');
  const inputs = parent.querySelectorAll('[data-editable], input[name="filename"]');
  if (btn.innerText.includes('Edit')) {
    inputs.forEach(input => input.removeAttribute('readonly'));
    btn.innerText = '💾 Save';
  } else {
    const data = {};
    inputs.forEach(input => {
      input.setAttribute('readonly', true);
      data[input.name] = input.value;
    });
    fetch('/update_metadata', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    btn.innerText = '✏️ Edit';
  }
}

function downloadMeta(filename) {
  window.location.href = `/download_zip/${filename}`;
}

function deleteRecord(filename, btn) {
  if (!confirm("Delete this record?")) return;
  fetch('/delete_metadata', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ filename })
  }).then(() => btn.closest('.record').remove());
}

function toggleAll(master) {
  document.querySelectorAll('.select-box').forEach(cb => cb.checked = master.checked);
}

function downloadSelected() {
  const selected = [...document.querySelectorAll('.select-box:checked')].map(cb => cb.value);
  if (!selected.length) {
    alert("No files selected.");
    return;
  }

  fetch('/download_batch_zip', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filenames: selected })
  })
  .then(res => res.blob())
  .then(blob => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'proof_batch.zip';
    link.click();
  });
}

/* ─────────────────────────────────────────
   TreatImages – Frontend interactions
───────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {

  // ── Range slider live label ─────────────────
  const rangeInput = document.getElementById("compress-quality");
  const rangeDisplay = document.getElementById("quality-display");

  if (rangeInput && rangeDisplay) {
    const updateRange = () => {
      const pct = rangeInput.value;
      rangeDisplay.textContent = pct + "%";
      // Update the CSS custom property used by the gradient track
      rangeInput.style.setProperty("--pct", pct + "%");
    };
    rangeInput.addEventListener("input", updateRange);
    updateRange(); // initialise on load
  }

  // ── Dropzone click & drag-and-drop ──────────
  document.querySelectorAll(".dropzone").forEach((zone) => {
    const inputId = zone.dataset.input;
    const fileInput = document.getElementById(inputId);
    const countEl = zone.querySelector(".dz-count");

    if (!fileInput) return;

    // Click to open file dialog
    zone.addEventListener("click", () => fileInput.click());

    // Update count label when files are chosen
    fileInput.addEventListener("change", () => {
      updateCount(fileInput, countEl);
    });

    // Drag-and-drop highlight
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("active");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("active"));
    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      zone.classList.remove("active");

      const dt = e.dataTransfer;
      if (dt && dt.files.length > 0) {
        // Assign files to the hidden input via DataTransfer
        const transfer = new DataTransfer();
        for (const file of dt.files) transfer.items.add(file);
        fileInput.files = transfer.files;
        updateCount(fileInput, countEl);
      }
    });
  });

  function updateCount(input, countEl) {
    if (!countEl) return;
    const n = input.files.length;
    countEl.textContent = n > 0 ? `${n} arquivo${n > 1 ? "s" : ""} selecionado${n > 1 ? "s" : ""}` : "";
  }

  // ── Form submit via fetch + Polling for Async Tasks ────
  const overlay = document.getElementById("loading-overlay");
  const progressContainer = document.getElementById("progress-container");
  const progressBar = document.getElementById("progress-bar");
  const progressStatus = document.getElementById("progress-status");

  document.querySelectorAll(".tool-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault(); // sempre interceptamos

      const fileInput = form.querySelector('input[type="file"]');
      if (!fileInput || fileInput.files.length === 0) {
        showToast("Por favor, selecione ao menos uma imagem.", "error");
        return;
      }

      // Mostra overlay com texto dinâmico (suporte a data-loading-text no botão)
      const btn = form.querySelector(".btn");
      const loadingText = document.getElementById("loading-text");
      if (loadingText && btn && btn.dataset.loadingText) {
        loadingText.textContent = btn.dataset.loadingText;
      } else if (loadingText) {
        loadingText.textContent = "Processando imagens…";
      }

      if (progressBar) progressBar.style.width = "0%";
      if (progressStatus) progressStatus.textContent = "0%";
      if (progressContainer) progressContainer.style.display = "none";
      if (overlay) overlay.classList.add("active");
      if (btn) btn.classList.add("loading");

      try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
          method: "POST",
          body: formData,
        });

        if (response.status === 202) {
          const { task_id } = await response.json();
          if (progressContainer) progressContainer.style.display = "block";
          
          // Inicia o Polling
          const pollInterval = setInterval(async () => {
            try {
              const res = await fetch(`/task-status/${task_id}`);
              if (!res.ok) {
                clearInterval(pollInterval);
                showToast("Erro ao monitorar o progresso do lote.", "error");
                cleanupOverlay(btn);
                return;
              }
              
              const task = await res.json();
              if (task.status === "completed") {
                clearInterval(pollInterval);
                
                // Dispara o download
                const downloadLink = document.createElement("a");
                downloadLink.href = `/task-download/${task_id}`;
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);

                showToast("Processamento concluído com sucesso! ✅", "success");
                if (task.errors && task.errors.length > 0) {
                  showToast(`Falha em algumas imagens: ${task.errors.join(", ")}`, "error");
                }
                
                cleanupOverlay(btn);
              } else if (task.status === "failed") {
                clearInterval(pollInterval);
                showToast(task.error || "O processamento falhou.", "error");
                cleanupOverlay(btn);
              } else {
                // Atualiza progresso
                const progress = task.progress || 0;
                const total = task.total || 1;
                const pct = Math.round((progress / total) * 100);
                if (progressBar) progressBar.style.width = `${pct}%`;
                if (progressStatus) progressStatus.textContent = `${progress} / ${total} (${pct}%)`;
              }
            } catch (pollErr) {
              console.error(pollErr);
              clearInterval(pollInterval);
              showToast("Erro na comunicação de progresso com o servidor.", "error");
              cleanupOverlay(btn);
            }
          }, 1000);
          
        } else {
          // ❌ Backend retornou erro direto (ex: 400 ou 500)
          const data = await response.json();
          const msg = data.error || "Erro ao processar as imagens.";
          showToast(msg, "error");
          cleanupOverlay(btn);
        }
      } catch (err) {
        console.error(err);
        showToast("Erro de conexão com o servidor.", "error");
        cleanupOverlay(btn);
      }
    });
  });

  function cleanupOverlay(btn) {
    if (overlay) overlay.classList.remove("active");
    if (btn) btn.classList.remove("loading");
    if (progressContainer) progressContainer.style.display = "none";
  }

  // ── Flash auto-dismiss ───────────────────────
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      el.style.opacity = "0";
      el.style.transform = "translateY(-8px)";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // ── Crop Logic (Cropper.js) ──────────────────
  let cropperInstance = null;
  const cropModal = document.getElementById("crop-modal");
  const cropImageEl = document.getElementById("crop-image-element");
  const cropInput = document.getElementById("crop-images");
  const btnCropStart = document.getElementById("btn-crop-start");
  const btnCropConfirm = document.getElementById("btn-crop-confirm");
  const btnCropClose = document.getElementById("btn-crop-close");

  // Open modal when clicking the button
  if (btnCropStart) {
    btnCropStart.addEventListener("click", () => {
      if (!cropInput || cropInput.files.length === 0) {
        showToast("Selecione uma imagem primeiro.", "error");
        return;
      }
      
      const file = cropInput.files[0];
      const reader = new FileReader();
      
      reader.onload = (e) => {
        cropImageEl.src = e.target.result;
        cropModal.classList.add("active");
        
        // Initialise Cropper
        if (cropperInstance) cropperInstance.destroy();
        cropperInstance = new Cropper(cropImageEl, {
          viewMode: 1,
          dragMode: 'move',
          autoCropArea: 0.8,
          restore: false,
          guides: true,
          center: true,
          highlight: false,
          cropBoxMovable: true,
          cropBoxResizable: true,
          toggleDragModeOnDblclick: false,
        });
      };
      reader.readAsDataURL(file);
    });
  }

  // Handle Aspect Ratio buttons
  document.querySelectorAll(".ratio-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      if (!cropperInstance) return;
      
      document.querySelectorAll(".ratio-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      
      const ratio = parseFloat(btn.dataset.ratio);
      cropperInstance.setAspectRatio(isNaN(ratio) ? NaN : ratio);
    });
  });

  // Close modal
  if (btnCropClose) {
    btnCropClose.addEventListener("click", () => {
      cropModal.classList.remove("active");
      if (cropperInstance) {
        cropperInstance.destroy();
        cropperInstance = null;
      }
    });
  }

  // Confirm Crop & Send to Download
  if (btnCropConfirm) {
    btnCropConfirm.addEventListener("click", () => {
      if (!cropperInstance) return;

      const canvas = cropperInstance.getCroppedCanvas({
        maxWidth: 4096,
        maxHeight: 4096,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high',
      });

      canvas.toBlob((blob) => {
        const formData = new FormData();
        formData.append("images", blob, cropInput.files[0].name);

        if (overlay) {
          document.getElementById("loading-text").textContent = "Finalizando recorte…";
          overlay.classList.add("active");
        }
        btnCropConfirm.classList.add("loading");

        fetch("/crop", {
          method: "POST",
          body: formData
        })
        .then(res => res.blob())
        .then(downloadBlob => {
          const url = URL.createObjectURL(downloadBlob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `recorte_${cropInput.files[0].name}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          
          cropModal.classList.remove("active");
          showToast("Imagem recortada com sucesso! ✅", "success");
        })
        .catch(err => {
          console.error(err);
          showToast("Erro ao processar o recorte.", "error");
        })
        .finally(() => {
          if (overlay) overlay.classList.remove("active");
          btnCropConfirm.classList.remove("loading");
          if (cropperInstance) {
            cropperInstance.destroy();
            cropperInstance = null;
          }
        });
      }, cropInput.files[0].type);
    });
  }

  // ── Simple toast helper (client-side only) ───
  function showToast(message, type = "error") {
    const container = document.querySelector(".flash-container") || (() => {
      const div = document.createElement("div");
      div.className = "flash-container";
      document.body.insertBefore(div, document.querySelector("main"));
      return div;
    })();

    const toast = document.createElement("div");
    toast.className = `flash flash-${type}`;
    toast.innerHTML = `<span class="flash-icon">${type === "error" ? "⚠️" : "✅"}</span> ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = "opacity 0.4s ease";
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 400);
    }, 5000);
  }
});

// VERSION_MARKER: TESTE_20250922_1613
// VERSION_MARKER: 2025-09-22_REVIEW_v2
(function () {
  const qrBtn = document.getElementById('qrBtn');
  const videoPreview = document.getElementById('videoPreview');
  const FEEDBACK_ID = 'cameraFeedback';

  let stream = null;
  let videoEl = null;
  let scanning = false;
  let lastDecode = null;
  let stopping = false;

  function ensureFeedbackContainer() {
    let fb = document.getElementById(FEEDBACK_ID);
    if (!fb) {
      fb = document.createElement('div');
      fb.id = FEEDBACK_ID;
      fb.style.marginTop = '8px';
      fb.style.fontSize = '0.9rem';
      fb.style.fontFamily = 'system-ui, sans-serif';
      fb.style.lineHeight = '1.3';
      videoPreview.appendChild(fb);
    }
    return fb;
  }

  function setFeedback(msg, isError = false) {
    const fb = ensureFeedbackContainer();
    fb.textContent = msg;
    fb.style.color = isError ? '#d33' : '#ccc';
  }

  async function listDevices() {
    if (!navigator.mediaDevices?.enumerateDevices) {
      console.warn("[SCAN] enumerateDevices indisponível.");
      return;
    }
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      console.log("[SCAN] Dispositivos:", devices.map(d => ({
        kind: d.kind,
        label: d.label,
        deviceId: d.deviceId
      })));
      if (!devices.some(d => d.kind === 'videoinput')) {
        setFeedback("Nenhuma câmera foi detectada neste dispositivo.", true);
      }
    } catch (e) {
      console.warn("[SCAN] enumerateDevices falhou:", e);
      // Opcional: setFeedback("Não foi possível listar dispositivos (permita acesso à câmera).");
    }
  }

  function clearVideoOnly() {
    if (videoEl && videoEl.parentElement) {
      videoEl.parentElement.removeChild(videoEl);
    }
    videoEl = null;
  }

  function cleanupPreview(full = true) {
    if (full) {
      videoPreview.innerHTML = '';
      videoEl = null;
    } else {
      clearVideoOnly();
      // mantém feedback
    }
  }

  function buildVideoElement() {
    cleanupPreview(false);
    if (!videoEl) {
      videoEl = document.createElement('video');
      videoEl.setAttribute('playsinline', 'true');
      videoEl.setAttribute('autoplay', 'true');
      videoEl.setAttribute('muted', 'true');
      videoEl.muted = true;
      videoEl.style.width = '100%';
      videoEl.style.maxHeight = '60vh';
      videoEl.style.objectFit = 'cover';
      videoEl.style.background = '#000';
      videoEl.style.border = '1px solid #333';
      videoEl.style.borderRadius = '8px';
      videoPreview.prepend(videoEl);
    }

    // Botão cancelar (cria só uma vez)
    if (!videoPreview.querySelector('button[data-role="stop-scan"]')) {
      const stopBtn = document.createElement('button');
      stopBtn.type = 'button';
      stopBtn.dataset.role = 'stop-scan';
      stopBtn.textContent = 'Cancelar';
      stopBtn.style.marginTop = '8px';
      stopBtn.addEventListener('click', () => {
        stopCamera(true);
      });
      videoPreview.appendChild(stopBtn);
    }
  }

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setFeedback("Navegador não suporta acesso à câmera.", true);
      return;
    }
    if (stream) {
      setFeedback("Câmera já ativa.");
      return;
    }

    disableButton(qrBtn, "Abrindo...");
    buildVideoElement();
    setFeedback("Solicitando acesso à câmera...");

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false
      });
      console.log("[SCAN] Stream OK (environment).");
    } catch (err1) {
      console.warn("[SCAN] Falhou com environment:", err1.name, err1.message);
      if (err1.name === 'NotFoundError' || err1.name === 'OverconstrainedError') {
        setFeedback("Tentando fallback de câmera genérica...");
        try {
          stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
          console.log("[SCAN] Stream OK (fallback).");
        } catch (err2) {
          handleCameraError(err2);
          enableButton(qrBtn);
          return;
        }
      } else {
        handleCameraError(err1);
        enableButton(qrBtn);
        return;
      }
    }

    videoEl.srcObject = stream;
    try {
      await videoEl.play();
    } catch (playErr) {
      console.warn("[SCAN] Falha ao iniciar vídeo:", playErr);
      setFeedback("Falha ao iniciar vídeo.", true);
      stopCamera(true);
      enableButton(qrBtn);
      return;
    }

    scanning = true;
    setFeedback("Câmera ativa. Aponte para o QR (detecção ainda não implementada).");
    listDevices();
    enableButton(qrBtn);
    // startScanLoop() futuramente aqui
  }

  function stopCamera(keepFeedback = false) {
    if (stopping) return;
    stopping = true;
    scanning = false;

    if (stream) {
      stream.getTracks().forEach(t => {
        try { t.stop(); } catch {}
      });
      stream = null;
    }
    if (keepFeedback) {
      clearVideoOnly();
      setFeedback("Câmera parada.");
    } else {
      cleanupPreview();
    }
    enableButton(qrBtn);
    stopping = false;
  }

  function handleCameraError(err) {
    console.error("[SCAN] Erro câmera:", err);
    let msg;
    switch (err.name) {
      case 'NotAllowedError':
        msg = "Permissão negada. Habilite a câmera nas configurações do navegador e tente novamente.";
        break;
      case 'NotFoundError':
      case 'OverconstrainedError':
        msg = "Nenhuma câmera disponível/compatível foi encontrada.";
        break;
      case 'NotReadableError':
        msg = "Câmera em uso por outro aplicativo.";
        break;
      default:
        msg = `Erro ao acessar câmera (${err.name}).`;
    }
    setFeedback(msg, true);
  }

  function onQRCodeDetected(decodedText) {
    if (decodedText === lastDecode) return;
    lastDecode = decodedText;
    console.log("[SCAN] QR detectado:", decodedText);
    scanning = false;
    stopCamera(true);
    const target = `${trussDetailUrl}?qr=${encodeURIComponent(decodedText)}`;
    window.location.href = target;
  }

  function disableButton(btn, text) {
    if (!btn) return;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = text || '...';
    btn.disabled = true;
    btn.style.opacity = '0.6';
  }

  function enableButton(btn) {
    if (!btn) return;
    if (btn.dataset.originalText) {
      btn.textContent = btn.dataset.originalText;
      delete btn.dataset.originalText;
    }
    btn.disabled = false;
    btn.style.opacity = '1';
  }

  if (qrBtn) {
    qrBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      startCamera();
    });
  } else {
    console.warn("[SCAN] Botão qrBtn não encontrado.");
  }

  window.addEventListener('beforeunload', () => stopCamera(false));

  // Expor para debug em dev
  if (location.hostname === 'localhost' || location.hostname.endsWith('.local')) {
    window.__qrScan = { startCamera, stopCamera, onQRCodeDetected };
  }
})();
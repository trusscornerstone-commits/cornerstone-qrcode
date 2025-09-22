// VERSION_MARKER: SCAN_PAGE_2025-09-22
(function() {
  const videoEl = document.getElementById('scanVideo');
  const feedbackBox = document.getElementById('feedbackBox');
  const backBtn = document.getElementById('backBtn');
  const cancelBtn = document.getElementById('cancelBtn');
  const startOverlay = document.getElementById('startBtn');
  const manualStartBtn = document.getElementById('manualStart');
  const frame = document.getElementById('scanFrame');

  let stream = null;
  let scanning = false;
  let lastDecode = null;

  function setFeedback(msg, isError=false) {
    feedbackBox.textContent = msg;
    feedbackBox.classList.toggle('error', !!isError);
  }

  async function startCamera(userInitiated=false) {
    if (stream || scanning) return;
    setFeedback(userInitiated ? "Iniciando câmera..." : "Solicitando permissão...");

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false
      });
    } catch (err1) {
      if (err1.name === 'NotFoundError' || err1.name === 'OverconstrainedError') {
        setFeedback("Tentando fallback de câmera...", false);
        try {
          stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        } catch (err2) {
          handleError(err2);
          return;
        }
      } else if (!userInitiated && isAutoplayBlock(err1)) {
        showManualStart();
        return;
      } else {
        handleError(err1);
        return;
      }
    }

    try {
      videoEl.srcObject = stream;
      await videoEl.play();
    } catch (playErr) {
      if (!userInitiated) {
        showManualStart("Toque para ativar o vídeo (bloqueio do navegador).");
        return;
      }
      setFeedback("Falha ao iniciar vídeo.", true);
      stopCamera();
      return;
    }

    scanning = true;
    setFeedback("Câmera ativa. Aponte para o QR.");
    // startScanLoop(); -> quando integrar jsQR / ZXing
  }

  function isAutoplayBlock(err) {
    return err.name === 'NotAllowedError' || err.message?.toLowerCase().includes('play');
  }

  function showManualStart(msg) {
    if (msg) setFeedback(msg);
    startOverlay.classList.remove('hidden');
  }

  function hideManualStart() {
    startOverlay.classList.add('hidden');
  }

  function stopCamera() {
    scanning = false;
    if (stream) {
      stream.getTracks().forEach(t => { try { t.stop(); } catch {} });
      stream = null;
    }
    videoEl.removeAttribute('srcObject');
    videoEl.srcObject = null;
  }

  function handleError(err) {
    console.error("[SCAN_PAGE] Erro câmera:", err);
    let msg;
    switch (err.name) {
      case 'NotAllowedError': msg = "Permissão negada. Habilite a câmera nas configurações do navegador."; break;
      case 'NotFoundError':
      case 'OverconstrainedError': msg = "Nenhuma câmera disponível."; break;
      case 'NotReadableError': msg = "Câmera em uso por outro app."; break;
      default: msg = `Erro de câmera (${err.name}).`;
    }
    setFeedback(msg, true);
    showManualStart("Tentar novamente");
  }

  function onQRCodeDetected(decodedText) {
    if (decodedText === lastDecode) return;
    lastDecode = decodedText;
    setFeedback("QR detectado. Redirecionando...");
    stopCamera();
    const target = `${trussDetailUrl}?qr=${encodeURIComponent(decodedText)}`;
    window.location.href = target;
  }

  // Placeholder de loop (ativar ao integrar lib)
  /*
  function startScanLoop() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const loop = () => {
      if (!scanning || videoEl.readyState !== 4) return;
      canvas.width = videoEl.videoWidth;
      canvas.height = videoEl.videoHeight;
      ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
      // const imageData = ctx.getImageData(0,0,canvas.width,canvas.height);
      // const code = jsQR(imageData.data, canvas.width, canvas.height);
      // if (code?.data) { onQRCodeDetected(code.data.trim()); return; }
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
  */

  backBtn.addEventListener('click', () => {
    stopCamera();
    window.location.href = homeUrl;
  });

  cancelBtn.addEventListener('click', () => {
    stopCamera();
    setFeedback("Scanner parado.");
    showManualStart("Reiniciar scanner");
  });

  manualStartBtn.addEventListener('click', () => {
    hideManualStart();
    startCamera(true);
  });

  window.addEventListener('pageshow', (e) => {
    if (e.persisted) {
      setFeedback("Recarregando câmera...");
      startCamera(true);
    }
  });

  window.addEventListener('beforeunload', stopCamera);

  if (navigator.mediaDevices?.getUserMedia) {
    startCamera(false);
  } else {
    setFeedback("Navegador não suporta câmera.", true);
  }

  if (location.hostname === 'localhost' || location.hostname.endsWith('.local')) {
    window.__scanPage = { startCamera, stopCamera, onQRCodeDetected };
  }
})();
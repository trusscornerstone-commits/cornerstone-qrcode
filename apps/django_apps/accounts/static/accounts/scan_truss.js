/**
 * scan_truss.js (DEBUG v2)
 * Adiciona logs e proteção contra redirecionamentos acidentais.
 * Data build: 2025-09-22T18:05Z
 */
(function () {
  console.log("[SCAN] Versão DEBUG v2 carregada.");
  const qrBtn = document.getElementById('qrBtn');
  const videoPreview = document.getElementById('videoPreview');

  if (!qrBtn) {
    console.warn("[SCAN] Botão qrBtn não encontrado.");
    return;
  }

  // Impedir que outra função capture o clique e redirecione
  // (ex: listeners adicionados antes ou delegação global)
  qrBtn.addEventListener('click', (e) => {
    console.log("[SCAN] Primeiro listener marcador (capturing) executado.");
  }, { capture: true });

  let stream = null;
  let scanning = false;
  let videoEl = null;
  let scanAnimationId = null;
  let lastDecode = null;

  const HARD_BLOCK_REDIRECT = true; // enquanto debug

  function logEvent(name) {
    console.log(`[SCAN] ${name}`);
  }

  async function startCamera() {
    logEvent("startCamera chamado");
    if (!navigator.mediaDevices?.getUserMedia) {
      alert("Navegador não suporta câmera.");
      return;
    }
    if (stream) {
      logEvent("Stream já existe.");
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false
      });
      logEvent("Permissão concedida e stream ativo.");
      prepareVideoElement();
      videoEl.srcObject = stream;
      await videoEl.play();
      logEvent("Video em reprodução.");
      scanning = true;
    } catch (err) {
      console.error("[SCAN] Erro getUserMedia:", err);
    }
  }

  function prepareVideoElement() {
    videoPreview.innerHTML = "";
    videoEl = document.createElement("video");
    videoEl.setAttribute("playsinline", "true");
    videoEl.setAttribute("autoplay", "true");
    videoEl.setAttribute("muted", "true");
    videoEl.muted = true;
    videoEl.style.width = "100%";
    videoEl.style.background = "#000";
    videoEl.style.border = "1px solid #333";
    videoEl.style.borderRadius = "8px";
    videoPreview.appendChild(videoEl);

    const stopBtn = document.createElement("button");
    stopBtn.textContent = "Parar";
    stopBtn.type = "button";
    stopBtn.addEventListener("click", stopCamera);
    videoPreview.appendChild(stopBtn);

    logEvent("Elemento de vídeo preparado.");
  }

  function stopCamera() {
    logEvent("stopCamera chamado");
    scanning = false;
    if (scanAnimationId) {
      cancelAnimationFrame(scanAnimationId);
      scanAnimationId = null;
    }
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
      logEvent("Tracks paradas.");
    }
    videoPreview.innerHTML = "";
    videoEl = null;
  }

  function onQRCodeDetected(decoded) {
    if (decoded === lastDecode) return;
    lastDecode = decoded;
    logEvent("QR detectado: " + decoded);
    stopCamera();
    if (HARD_BLOCK_REDIRECT) {
      logEvent("Redirecionamento BLOQUEADO (modo debug).");
      return;
    }
    const target = `${trussDetailUrl}?qr=${encodeURIComponent(decoded)}`;
    logEvent("Redirecionando para " + target);
    window.location.href = target;
  }

  qrBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation(); // impede outros handlers
    logEvent("Clique principal do qrBtn recebido.");
    await startCamera();
  });

  // Logar qualquer tentativa geral de redirecionamento
  const originalAssign = window.location.assign;
  window.location.assign = function () {
    console.warn("[SCAN] location.assign chamado:", arguments);
    if (HARD_BLOCK_REDIRECT) {
      console.warn("[SCAN] bloqueado (debug).");
      return;
    }
    return originalAssign.apply(this, arguments);
  };
  Object.defineProperty(window.location, 'href', {
    set(v) {
      console.warn("[SCAN] location.href set ->", v);
      if (!HARD_BLOCK_REDIRECT) {
        history.pushState({}, "", v); // simula (para debug). Trocar para real se quiser.
      } else {
        console.warn("[SCAN] href bloqueado (debug).");
      }
    },
    get() {
      return document.URL;
    }
  });

  window.addEventListener('beforeunload', () => {
    logEvent("beforeunload -> stopCamera");
    stopCamera();
  });

  // Expor p/ teste manual
  window.__qrScanDebug = {
    startCamera,
    stopCamera,
    forceQR: onQRCodeDetected
  };

})();
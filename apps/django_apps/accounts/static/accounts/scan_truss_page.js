// VERSION_MARKER: SCAN_PAGE_2025-09-22 + QR_ENABLED_V2
(function() {
  const videoEl       = document.getElementById('scanVideo');
  const feedbackBox   = document.getElementById('feedbackBox');
  const backBtn       = document.getElementById('backBtn');
  const cancelBtn     = document.getElementById('cancelBtn');
  const startOverlay  = document.getElementById('startBtn');
  const manualStartBtn= document.getElementById('manualStart');
  const frame         = document.getElementById('scanFrame'); // opcional (janela visual)
  // Certifique-se que trussDetailUrl, homeUrl são globais definidos antes.

  let stream = null;
  let scanning = false;
  let lastDecode = null;
  let rafId = null;

  let detectionEngine = null;      // 'barcode' | 'jsqr' | 'zxing'
  let barcodeDetector = null;
  let zxingReader = null;          // se integrar ZXing depois

  const SCAN_INTERVAL_MS = 120;    // throttle
  let lastAttemptTs = 0;

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d', { willReadFrequently: true });

  function log(...args) {
    console.log('[SCAN_PAGE]', ...args);
  }

  function setFeedback(msg, isError=false) {
    feedbackBox.textContent = msg;
    feedbackBox.classList.toggle('error', !!isError);
  }

  async function loadJsQRIfNeeded() {
    if (typeof window.jsQR === 'function') {
      log('jsQR já presente.');
      return true;
    }
    return new Promise((resolve) => {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js';
      s.async = true;
      s.onload = () => {
        log('jsQR carregado.');
        resolve(true);
      };
      s.onerror = () => {
        console.warn('[SCAN_PAGE] Falha ao carregar jsQR CDN.');
        resolve(false);
      };
      document.head.appendChild(s);
    });
  }

  async function initDetectors() {
    // 1. BarcodeDetector (Chrome/Edge/Alguns Android) - NÃO iOS Safari
    if ('BarcodeDetector' in window) {
      try {
        const formats = await BarcodeDetector.getSupportedFormats();
        if (formats.includes('qr_code')) {
          barcodeDetector = new BarcodeDetector({ formats: ['qr_code'] });
          detectionEngine = 'barcode';
          log('Engine selecionada: BarcodeDetector');
          return;
        } else {
          log('BarcodeDetector disponível mas sem formato qr_code.');
        }
      } catch (e) {
        log('BarcodeDetector falhou:', e);
      }
    }

    // 2. jsQR
    let jsqrOk = await loadJsQRIfNeeded();
    if (jsqrOk && typeof window.jsQR === 'function') {
      detectionEngine = 'jsqr';
      log('Engine selecionada: jsQR');
      return;
    }

    // 3. ZXing (se quiser depois)
    // if (window.__ZXingReader) {
    //   zxingReader = window.__ZXingReader;
    //   detectionEngine = 'zxing';
    //   log('Engine selecionada: ZXing');
    //   return;
    // }

    // Se chegou aqui, não tem engine
    detectionEngine = null;
  }

  async function startCamera(userInitiated=false) {
    if (stream || scanning) return;
    setFeedback(userInitiated ? 'Iniciando câmera...' : 'Solicitando permissão...');

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
    } catch (err1) {
      if (err1.name === 'NotFoundError' || err1.name === 'OverconstrainedError') {
        setFeedback('Tentando fallback de câmera...');
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
        showManualStart('Toque para ativar o vídeo (bloqueio do navegador).');
        return;
      }
      setFeedback('Falha ao iniciar vídeo.', true);
      stopCamera();
      return;
    }

    scanning = true;
    await initDetectors();

    if (!detectionEngine) {
      setFeedback('Sem engine de QR disponível.', true);
      log('Nenhuma engine disponível: verifique carregamento de jsQR ou suporte do navegador.');
      return;
    }

    setFeedback('Câmera ativa. Aponte para o QR.');
    startScanLoop();
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
    if (rafId) cancelAnimationFrame(rafId);
    if (stream) {
      stream.getTracks().forEach(t => { try { t.stop(); } catch {} });
      stream = null;
    }
    videoEl.removeAttribute('srcObject');
    videoEl.srcObject = null;
  }

  function handleError(err) {
    console.error('[SCAN_PAGE] Erro câmera:', err);
    let msg;
    switch (err.name) {
      case 'NotAllowedError': msg = 'Permissão negada. Habilite a câmera nas configurações.'; break;
      case 'NotFoundError':
      case 'OverconstrainedError': msg = 'Nenhuma câmera disponível.'; break;
      case 'NotReadableError': msg = 'Câmera em uso por outro aplicativo.'; break;
      default: msg = `Erro de câmera (${err.name}).`;
    }
    setFeedback(msg, true);
    showManualStart('Tentar novamente');
  }

  function onQRCodeDetected(decodedText) {
  if (!decodedText || decodedText === lastDecode) return;
  lastDecode = decodedText;
  // Para o MVP: sempre manda para a página genérica
  stopCamera();
  window.location.href = `/truss/generic/?qr=${encodeURIComponent(decodedText)}`;
}

  function getCropRegion(videoW, videoH) {
    if (frame && frame.getBoundingClientRect) {
      const rectVideo = videoEl.getBoundingClientRect();
      const rectFrame = frame.getBoundingClientRect();
      const scaleX = videoW / rectVideo.width;
      const scaleY = videoH / rectVideo.height;
      const x = (rectFrame.left - rectVideo.left) * scaleX;
      const y = (rectFrame.top - rectVideo.top) * scaleY;
      const w = rectFrame.width * scaleX;
      const h = rectFrame.height * scaleY;
      if (w > 60 && h > 60) {
        return {
          x: Math.max(0, x|0),
          y: Math.max(0, y|0),
          w: Math.min(videoW, w|0),
          h: Math.min(videoH, h|0)
        };
      }
    }
    return { x:0, y:0, w:videoW, h:videoH };
  }

  async function detectBarcodeDetector(bmp) {
    try {
      const codes = await barcodeDetector.detect(bmp);
      if (codes && codes.length) {
        for (const c of codes) {
          if (c.rawValue) {
            onQRCodeDetected(c.rawValue.trim());
            break;
          }
        }
      }
    } catch(e) {
      log('BarcodeDetector erro:', e);
    }
  }

  function detectJsQR(imageData) {
    const code = window.jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'attemptBoth'
    });
    if (code?.data) {
      onQRCodeDetected(code.data.trim());
    }
  }

  function startScanLoop() {
    const loop = () => {
      if (!scanning) return;
      const now = performance.now();
      if (now - lastAttemptTs < SCAN_INTERVAL_MS) {
        rafId = requestAnimationFrame(loop);
        return;
      }
      lastAttemptTs = now;

      if (videoEl.readyState === 4) {
        const vw = videoEl.videoWidth;
        const vh = videoEl.videoHeight;
        if (vw && vh) {
          const crop = getCropRegion(vw, vh);
          canvas.width = crop.w;
          canvas.height = crop.h;
          ctx.drawImage(videoEl, crop.x, crop.y, crop.w, crop.h, 0, 0, crop.w, crop.h);

          if (detectionEngine === 'barcode') {
            createImageBitmap(canvas)
              .then(bmp => detectBarcodeDetector(bmp))
              .catch(()=>{});
          } else if (detectionEngine === 'jsqr') {
            const imgData = ctx.getImageData(0,0,canvas.width,canvas.height);
            detectJsQR(imgData);
          } else if (detectionEngine === 'zxing') {
            // implementar se integrar ZXing
          }
        }
      }
      rafId = requestAnimationFrame(loop);
    };
    rafId = requestAnimationFrame(loop);
  }

  // BOTÕES
  backBtn?.addEventListener('click', () => {
    stopCamera();
    window.location.href = homeUrl;
  });

  cancelBtn?.addEventListener('click', () => {
    stopCamera();
    setFeedback('Scanner parado.');
    showManualStart('Reiniciar scanner');
  });

  manualStartBtn?.addEventListener('click', () => {
    hideManualStart();
    startCamera(true);
  });

  window.addEventListener('pageshow', (e) => {
    if (e.persisted) {
      setFeedback('Recarregando câmera...');
      startCamera(true);
    }
  });

  window.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopCamera();
    }
  });

  window.addEventListener('beforeunload', stopCamera);

  if (navigator.mediaDevices?.getUserMedia) {
    startCamera(false);
  } else {
    setFeedback('Navegador não suporta câmera.', true);
  }

  // Debug global em ambiente local
  if (location.hostname === 'localhost' || location.hostname.endsWith('.local')) {
    window.__scanPage = { startCamera, stopCamera };
  }
})();
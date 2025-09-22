/**
 * scan_truss.js
 * Melhorias implementadas:
 * - Não interrompe o stream imediatamente.
 * - facingMode 'environment' (câmera traseira quando disponível).
 * - Preview real do vídeo.
 * - Suporte a iniciar/pausar.
 * - Tratamento detalhado de erros.
 * - Possibilidade de integrar leitura de QR (placeholder).
 * - Redireciona apenas quando apropriado (após leitura ou ação do usuário).
 *
 * Requisitos no template:
 *  - Um botão com id="qrBtn"
 *  - Um container para o vídeo com id="videoPreview"
 *  - Variáveis globais definidas no template Django:
 *      const trussDetailUrl = "{% url 'truss_detail' %}";
 *
 * Para realmente decodificar QR:
 *  - Incluir biblioteca (ex: jsQR ou @zxing/browser)
 *  - Implementar a função decodeFrame()
 */

(function () {
  const qrBtn = document.getElementById('qrBtn');
  const videoPreview = document.getElementById('videoPreview');

  // Caso deseje adicionar um botão de parar posteriormente
  let stopBtn = null;

  let stream = null;
  let scanning = false;
  let videoEl = null;
  let scanAnimationId = null;
  let lastDecode = null;
  let decodeThrottleMs = 250;
  let lastDecodeAttempt = 0;

  /**
   * Inicia a câmera.
   */
  async function startCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Este navegador não suporta acesso à câmera.');
      return;
    }

    // Se já está rodando, ignora
    if (stream) {
      return;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' }, // tenta traseira
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      });

      prepareVideoElement();
      videoEl.srcObject = stream;

      await videoEl.play(); // garante início (iOS precisa disso)

      scanning = true;

      // Inicia loop de leitura (se quiser ativar decodificação depois)
      // startScanLoop();

    } catch (err) {
      handleCameraError(err);
    }
  }

  /**
   * Cria/limpa o elemento de vídeo dentro do container.
   */
  function prepareVideoElement() {
    videoPreview.innerHTML = '';

    videoEl = document.createElement('video');
    videoEl.setAttribute('playsinline', 'true'); // iOS
    videoEl.setAttribute('autoplay', 'true');
    videoEl.setAttribute('muted', 'true'); // ajuda autoplay
    videoEl.muted = true;

    videoEl.style.width = '100%';
    videoEl.style.border = '1px solid #333';
    videoEl.style.borderRadius = '8px';
    videoEl.style.background = '#000';
    videoEl.style.objectFit = 'cover';

    videoPreview.appendChild(videoEl);

    // Opcional: adicionar botão de cancelar/parar
    if (!stopBtn) {
      stopBtn = document.createElement('button');
      stopBtn.type = 'button';
      stopBtn.textContent = 'Cancelar';
      stopBtn.style.marginTop = '8px';
      stopBtn.addEventListener('click', () => {
        stopCamera();
        clearPreview();
      });
      videoPreview.appendChild(stopBtn);
    }
  }

  /**
   * Limpa a área de preview.
   */
  function clearPreview() {
    videoPreview.innerHTML = '';
    videoEl = null;
    stopBtn = null;
  }

  /**
   * Para a câmera/stream.
   */
  function stopCamera() {
    scanning = false;
    if (scanAnimationId) {
      cancelAnimationFrame(scanAnimationId);
      scanAnimationId = null;
    }
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
  }

  /**
   * Tratamento de erros de getUserMedia.
   */
  function handleCameraError(err) {
    console.error('Erro ao acessar a câmera:', err);
    let msg = 'Não foi possível acessar a câmera.';
    switch (err.name) {
      case 'NotAllowedError':
        msg = 'Permissão negada. Habilite o acesso à câmera nas configurações do navegador.';
        break;
      case 'NotFoundError':
      case 'OverconstrainedError':
        msg = 'Nenhuma câmera compatível encontrada neste dispositivo.';
        break;
      case 'NotReadableError':
        msg = 'A câmera está em uso por outro aplicativo.';
        break;
      default:
        msg = `${msg} (${err.name})`;
    }
    alert(msg);
    // Opcional: fallback de redirecionar mesmo assim
    // window.location.href = trussDetailUrl;
  }

  /**
   * Loop de varredura para decodificar (placeholder).
   * Ative chamando startScanLoop() após iniciar a câmera.
   */
  function startScanLoop() {
    if (!videoEl) return;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    const loop = () => {
      if (!scanning || videoEl.readyState !== 4) {
        return;
      }

      canvas.width = videoEl.videoWidth;
      canvas.height = videoEl.videoHeight;
      ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);

      const now = performance.now();
      if (now - lastDecodeAttempt > decodeThrottleMs) {
        lastDecodeAttempt = now;
        try {
          // Exemplo com jsQR (se adicionar biblioteca):
          // const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          // const code = jsQR(imageData.data, canvas.width, canvas.height);
          // if (code && code.data) {
          //   onQRCodeDetected(code.data);
          //   return;
          // }
        } catch (e) {
          console.warn('Falha durante decodificação:', e);
        }
      }

      scanAnimationId = requestAnimationFrame(loop);
    };

    scanAnimationId = requestAnimationFrame(loop);
  }

  /**
   * Chamada quando um QR é detectado (integrar a biblioteca e chamar aqui).
   */
  function onQRCodeDetected(decodedText) {
    if (decodedText === lastDecode) {
      return; // evita repetição imediata
    }
    lastDecode = decodedText;

    console.log('QR detectado:', decodedText);

    // Para tudo antes de ir
    stopCamera();

    // Redirecionar anexando parâmetro (ajuste conforme sua lógica)
    const target = `${trussDetailUrl}?qr=${encodeURIComponent(decodedText)}`;
    window.location.href = target;
  }

  /**
   * Clique do botão principal.
   * Em vez de redirecionar direto, inicia a câmera.
   */
  qrBtn.addEventListener('click', async (e) => {
    e.preventDefault();

    // Se já está ativo, não reinicia; pode decidir parar ou apenas ignorar
    if (stream) {
      return;
    }

    await startCamera();

    // Se quiser já iniciar o loop de leitura:
    // startScanLoop();
  });

  /**
   * Limpa câmera ao sair/navegar
   */
  window.addEventListener('beforeunload', () => {
    stopCamera();
  });

  // (Opcional) expor para debug no console
  window.__qrScanDebug = {
    startCamera,
    stopCamera,
    startScanLoop
  };
})();
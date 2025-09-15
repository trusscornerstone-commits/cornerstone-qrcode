// home.js

const qrBtn = document.getElementById('qrBtn');
const videoPreview = document.getElementById('videoPreview');

qrBtn.addEventListener('click', async () => {
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      // Tenta acessar a câmera
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      
      // Opcional: exibir preview da câmera
      const video = document.createElement('video');
      video.srcObject = stream;
      video.autoplay = true;
      video.playsInline = true;
      videoPreview.innerHTML = '';
      videoPreview.appendChild(video);

      // Redireciona para truss-detail.html
      window.location.href = 'truss-detail.html';

    } catch (err) {
      // Se houver erro ou permissão negada, ainda assim redireciona
      console.warn('Câmera não acessível, redirecionando mesmo assim:', err.message);
      window.location.href = 'truss-detail.html';
    }
  } else {
    // Navegador não suporta câmera, redireciona
    window.location.href = 'truss-detail.html';
  }
});

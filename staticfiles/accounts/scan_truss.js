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

      // Encerrar o stream para liberar a câmera
      stream.getTracks().forEach(track => track.stop());

      window.location.href = "{% url 'truss_detail' %}";
    } catch (err) {
      console.warn('Câmera não acessível, redirecionando mesmo assim:', err.message);
      window.location.href = "{% url 'truss_detail' %}";
    }
  } else {
    window.location.href = "{% url 'truss_detail' %}";
  }
});

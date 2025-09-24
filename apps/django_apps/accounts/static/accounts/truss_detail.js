(function () {
  const meta = document.querySelector('meta[name="truss-id"]');
  const trussId = meta ? meta.content : null;

  const titleEl = document.getElementById("title");
  const jobEl = document.getElementById("job");
  const tipoEl = document.getElementById("tipo");
  const qtyEl = document.getElementById("qty");
  const endEl = document.getElementById("endereco");
  const tamEl = document.getElementById("tamanho");
  const descEl = document.getElementById("desc");
  const statusBtn = document.getElementById("statusBtn");

  function setStatus(statusText) {
    const txt = (statusText || "").toString();
    statusBtn.classList.remove("ongoing", "completed");
    if (txt.toLowerCase() === "instalado" || txt.toLowerCase() === "completed") {
      statusBtn.classList.add("completed");
    } else {
      statusBtn.classList.add("ongoing");
    }
    statusBtn.textContent = txt || "Truss Ongoing";
  }

  async function load() {
    if (!trussId) {
      titleEl.textContent = "Truss not found";
      return;
    }
    try {
      const url = `/static/truss-data/${trussId}.json?ts=${Date.now()}`;
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const truss = await res.json();

      titleEl.textContent = truss.truss_number || `#${trussId}`;
      jobEl.textContent = truss.job_number || "-";
      tipoEl.textContent = truss.tipo || "-";
      qtyEl.textContent = truss.quantidade || "-";
      endEl.textContent = truss.endereco || "-";
      tamEl.textContent = truss.tamanho || "-";
      descEl.textContent = `Details for truss ${truss.truss_number || trussId}. Job: ${truss.job_number || "-"}. Type: ${truss.tipo || "-"}. Qty: ${truss.quantidade || "-"}.`;

      setStatus(truss.status);

      // Toggle visual (não persiste)
      statusBtn.addEventListener("click", () => {
        if (statusBtn.classList.contains("ongoing")) setStatus("Completed");
        else setStatus("Truss Ongoing");
      });
    } catch (e) {
      titleEl.textContent = `Truss ${trussId}`;
      setStatus("Unknown");
      descEl.textContent = "Could not load truss data.";
      console.error("Failed to load truss json:", e);
    }
  }

  load();
})();
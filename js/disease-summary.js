(() => {
  const diseases = {
    dbd: 'DBD (Demam Berdarah)',
    leptospirosis: 'Leptospirosis',
    tb_baru: 'Tuberkulosis'
  };
  const years = Array.from({ length: 8 }, (_, index) => 2019 + index);
  const modal = document.getElementById('disease-modal');
  const title = document.getElementById('disease-modal-title');
  const subtitle = document.getElementById('disease-modal-subtitle');
  const tableBody = document.getElementById('disease-modal-rows');
  const cache = new Map();
  let activeDisease = null;

  function numberOrZero(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
  }

  function summarize(rows) {
    return rows.reduce((totals, row) => {
      totals.male += numberOrZero(row.laki_laki);
      totals.female += numberOrZero(row.perempuan);
      totals.deaths += numberOrZero(row.meninggal_laki_laki);
      totals.deaths += numberOrZero(row.meninggal_perempuan);
      return totals;
    }, { male: 0, female: 0, deaths: 0 });
  }

  function formatNumber(value) {
    return value.toLocaleString('id-ID');
  }

  function showMessage(message) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 5;
    cell.className = 'disease-modal-state';
    cell.textContent = message;
    row.append(cell);
    tableBody.replaceChildren(row);
  }

  async function loadSummary(disease) {
    if (cache.has(disease)) return cache.get(disease);

    const request = Promise.all(years.map(async year => {
      const response = await fetch(`data/${disease}/bar_${year}.json`);
      if (!response.ok) throw new Error(`Data tahun ${year} tidak dapat dimuat.`);
      const rows = await response.json();
      if (!Array.isArray(rows)) throw new Error(`Format data tahun ${year} tidak valid.`);
      return { year, ...summarize(rows) };
    })).catch(error => {
      cache.delete(disease);
      throw error;
    });

    cache.set(disease, request);
    return request;
  }

  function renderRows(summary) {
    const fragment = document.createDocumentFragment();
    summary.forEach(item => {
      const row = document.createElement('tr');
      [
        item.year,
        formatNumber(item.male),
        formatNumber(item.female),
        formatNumber(item.male + item.female),
        formatNumber(item.deaths)
      ].forEach(value => {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.append(cell);
      });
      fragment.append(row);
    });
    tableBody.replaceChildren(fragment);
  }

  document.querySelectorAll('.disease-item[data-disease]').forEach(button => {
    button.addEventListener('click', async () => {
      const disease = button.dataset.disease;
      if (!diseases[disease]) return;

      activeDisease = disease;
      title.textContent = `Data Kasus ${diseases[disease]}`;
      subtitle.textContent = `Data Kasus Kota Semarang Tahun ${years[0]}-${years[years.length - 1]}`;
      showMessage('Memuat data...');
      modal.showModal();

      try {
        const summary = await loadSummary(disease);
        if (activeDisease === disease && modal.open) renderRows(summary);
      } catch (error) {
        if (activeDisease === disease && modal.open) {
          showMessage(`${error.message} Pastikan halaman dijalankan melalui server lokal.`);
        }
      }
    });
  });

  modal.querySelector('.disease-modal-close').addEventListener('click', () => modal.close());
  modal.addEventListener('click', event => {
    if (event.target === modal) modal.close();
  });
})();

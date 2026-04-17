const statusText = document.getElementById('statusText');
const productsGrid = document.getElementById('productsGrid');
const searchInput = document.getElementById('searchInput');
const categorySelect = document.getElementById('categorySelect');
const brandSelect = document.getElementById('brandSelect');
const statusSelect = document.getElementById('statusSelect');
const reloadButton = document.getElementById('reloadButton');
const prevPageButton = document.getElementById('prevPageButton');
const nextPageButton = document.getElementById('nextPageButton');
const pageInfoText = document.getElementById('pageInfoText');

const pageSize = 24;
let currentOffset = 0;
let currentTotal = 0;

function fillSelectOptions(selectElement, values, defaultLabel) {
  const currentValue = selectElement.value;
  selectElement.innerHTML = '';

  const defaultOption = document.createElement('option');
  defaultOption.value = '';
  defaultOption.textContent = defaultLabel;
  selectElement.appendChild(defaultOption);

  for (const value of values) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    if (value === currentValue) {
      option.selected = true;
    }
    selectElement.appendChild(option);
  }
}

async function loadFilterOptions() {
  const response = await fetch('/api/filter-options');
  if (!response.ok) {
    return;
  }

  const payload = await response.json();
  fillSelectOptions(categorySelect, payload.general_categories || [], 'Все общие категории');
  fillSelectOptions(brandSelect, payload.brands || [], 'Все бренды');
}

function updatePagination() {
  const currentPage = Math.floor(currentOffset / pageSize) + 1;
  const totalPages = Math.max(1, Math.ceil(currentTotal / pageSize));
  pageInfoText.textContent = `Страница ${currentPage} из ${totalPages}`;
  prevPageButton.disabled = currentOffset <= 0;
  nextPageButton.disabled = currentOffset + pageSize >= currentTotal;
}

async function loadProducts() {
  statusText.textContent = 'Загрузка...';
  productsGrid.innerHTML = '';

  const params = new URLSearchParams();
  if (searchInput.value.trim()) {
    params.set('q', searchInput.value.trim());
  }
  if (categorySelect.value) {
    params.set('general_category', categorySelect.value);
  }
  if (brandSelect.value) {
    params.set('brand', brandSelect.value);
  }
  if (statusSelect.value) {
    params.set('status', statusSelect.value);
  }
  params.set('limit', pageSize.toString());
  params.set('offset', currentOffset.toString());

  const response = await fetch(`/api/products?${params.toString()}`);
  if (!response.ok) {
    statusText.textContent = 'Не удалось загрузить товары';
    updatePagination();
    return;
  }

  const payload = await response.json();
  const products = payload.items || [];
  currentTotal = payload.total || 0;
  statusText.textContent = `Найдено товаров: ${currentTotal} · источник: ${payload.data_source}`;
  updatePagination();

  if (!products.length) {
    productsGrid.innerHTML = '<p>Товары не найдены</p>';
    return;
  }

  for (const product of products) {
    const card = document.createElement('article');
    card.className = 'product-card';
    card.innerHTML = `
      <img class="product-image" src="${product.main_image_url || ''}" alt="${product.title}" />
      <div class="product-body">
        <p><strong>${product.brand_name || 'Без бренда'}</strong></p>
        <p>${product.title}</p>
        <p>Категория: ${product.general_category_name || '-'} / ${product.category_name || '-'} / ${product.subcategory_name || '-'}</p>
        <p>Размер: ${product.size_label || '-'}</p>
        <p>Состояние: ${product.condition_rank || '-'}</p>
        <p>Статус: ${product.status || 'active'}</p>
        <p>Цена: ${product.price_original || '-'} ${product.currency_code || ''}</p>
        <p><a href="/product.html?id=${product.source_product_id}">Открыть товар</a></p>
      </div>
    `;
    productsGrid.appendChild(card);
  }
}

reloadButton.addEventListener('click', loadProducts);
searchInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    currentOffset = 0;
    loadProducts();
  }
});
categorySelect.addEventListener('change', () => {
  currentOffset = 0;
  loadProducts();
});
brandSelect.addEventListener('change', () => {
  currentOffset = 0;
  loadProducts();
});
statusSelect.addEventListener('change', () => {
  currentOffset = 0;
  loadProducts();
});
prevPageButton.addEventListener('click', () => {
  if (currentOffset <= 0) {
    return;
  }
  currentOffset -= pageSize;
  loadProducts();
});
nextPageButton.addEventListener('click', () => {
  if (currentOffset + pageSize >= currentTotal) {
    return;
  }
  currentOffset += pageSize;
  loadProducts();
});

loadFilterOptions().then(loadProducts);

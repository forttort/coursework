const statusText = document.getElementById('statusText');
const productsGrid = document.getElementById('productsGrid');
const searchInput = document.getElementById('searchInput');
const categorySelect = document.getElementById('categorySelect');
const reloadButton = document.getElementById('reloadButton');

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

  const response = await fetch(`/api/products?${params.toString()}`);
  if (!response.ok) {
    statusText.textContent = 'Не удалось загрузить товары';
    return;
  }

  const products = await response.json();
  statusText.textContent = `Найдено товаров: ${products.length}`;

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
    loadProducts();
  }
});
categorySelect.addEventListener('change', loadProducts);

loadProducts();

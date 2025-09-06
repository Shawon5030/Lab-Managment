
const equipmentCards = document.querySelectorAll('.equipment-card');
const searchInput = document.querySelector('.search-box input');
const categorySelect = document.querySelector('select[name="category"]');
const statusSelect = document.querySelector('select[name="status"]');
const sortSelect = document.querySelector('select[name="sort_by"]');

function filterAndSort() {
    const query = searchInput.value.toLowerCase().trim();
    const selectedCategory = categorySelect.value.toLowerCase();
    const selectedStatus = statusSelect.value.toLowerCase();
    const sortBy = sortSelect.value;

    let cardsArray = Array.from(equipmentCards);

    // Filter
    cardsArray.forEach(card => {
        const name = card.dataset.name;
        const desc = card.dataset.desc;
        const category = card.dataset.category;
        const status = card.dataset.status;

        const matchesSearch = name.includes(query) || desc.includes(query) || category.includes(query);
        const matchesCategory = selectedCategory === "" || category === selectedCategory;
        const matchesStatus = selectedStatus === "" || status === selectedStatus;

        if (matchesSearch && matchesCategory && matchesStatus) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });

    // Sort
    cardsArray = cardsArray.filter(card => card.style.display !== 'none');
    const grid = document.querySelector('.equipment-grid');
    
    if (sortBy === 'name_asc') {
        cardsArray.sort((a, b) => a.dataset.name.localeCompare(b.dataset.name));
    } else if (sortBy === 'name_desc') {
        cardsArray.sort((a, b) => b.dataset.name.localeCompare(a.dataset.name));
    } else if (sortBy === 'recent') {
        cardsArray.sort((a, b) => b.dataset-id - a.dataset-id); // if you add data-id="{{ product.id }}"
    }

    // Re-append in new order
    cardsArray.forEach(card => grid.appendChild(card));
}

// Event listeners
searchInput.addEventListener('input', filterAndSort);
categorySelect.addEventListener('change', filterAndSort);
statusSelect.addEventListener('change', filterAndSort);
sortSelect.addEventListener('change', filterAndSort);


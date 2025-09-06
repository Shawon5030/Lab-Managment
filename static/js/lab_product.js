
const equipmentCards = document.querySelectorAll('.equipment-card');
const searchInput = document.querySelector('.search-box input');
const categorySelect = document.querySelector('select[name="category"]');
const statusSelect = document.querySelector('select[name="status"]');
const sortSelect = document.querySelector('select[name="sort_by"]');

// Transferred product ids from Django
const transferred_dict_ids = [
    {% for product_id in transferred_dict.keys %}
        {{ product_id }}{% if not forloop.last %}, {% endif %}
    {% endfor %}
];

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
        const productId = parseInt(card.dataset.id);

        const matchesSearch = name.includes(query) || desc.includes(query) || category.includes(query);
        const matchesCategory = selectedCategory === "" || category === selectedCategory;

        let matchesStatus = false;
        if (selectedStatus === "" || selectedStatus === status) {
            matchesStatus = true;
        } else if (selectedStatus === "transferred") {
            matchesStatus = transferred_dict_ids.includes(productId);
        }

        if (matchesSearch && matchesCategory && matchesStatus) {
            card.style.display = '';
            card.style.animation = 'fadeIn 0.5s ease-out';
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
        cardsArray.sort((a, b) => b.dataset.id - a.dataset.id);
    }

    // Re-append in new order
    cardsArray.forEach(card => grid.appendChild(card));
}

// Event listeners
searchInput.addEventListener('input', filterAndSort);
categorySelect.addEventListener('change', filterAndSort);
statusSelect.addEventListener('change', filterAndSort);
sortSelect.addEventListener('change', filterAndSort);

// Initial call
filterAndSort();

// --- Chart.js code remains the same ---
const ctx = document.getElementById('categoryChart').getContext('2d');
const categories = [
    {% for category in category_counts %}
        "{{ category.category__name }}"{% if not forloop.last %}, {% endif %}
    {% endfor %}
];
const counts = [
    {% for category in category_counts %}
        {{ category.count }}{% if not forloop.last %}, {% endif %}
    {% endfor %}
];

const categoryChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: categories,
        datasets: [{
            data: counts,
            backgroundColor: ['#3498db','#9b59b6','#2ecc71','#f39c12','#e74c3c','#7f8c8d','#34495e','#16a085'],
            borderColor: '#fff',
            borderWidth: 2,
            hoverOffset: 10
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                position: 'right',
                labels: { font: { size: 12 }, padding: 20 }
            }
        },
        cutout: '50%',
        animation: { animateScale: true, animateRotate: true }
    }
});


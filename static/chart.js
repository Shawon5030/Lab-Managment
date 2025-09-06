
    const ctx = document.getElementById('categoryChart').getContext('2d');

    // Get category names and counts from Django context
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
        type: 'bar', // You can also use 'pie', 'doughnut', 'line', etc.
        data: {
            labels: categories,
            datasets: [{
                label: 'Number of Products',
                data: counts,
                backgroundColor: [
                    '#3498db',
                    '#9b59b6',
                    '#2ecc71',
                    '#f39c12',
                    '#e74c3c',
                    '#7f8c8d'
                ],
                borderColor: '#fff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Category-wise Product Counts',
                    font: {
                        size: 18
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });


function renderPieChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: [
                    '#4e73df',
                    '#1cc88a',
                    '#f6c23e'
                ]
            }]
        },
        options: {
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

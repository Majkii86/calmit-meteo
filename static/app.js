let chart = null;

function showValue(value, unit) {
    if (value === null || value === undefined) {
        return '-- ' + unit;
    }

    return value + ' ' + unit;
}

async function loadCurrent() {
    const res = await fetch('/api/current');
    const data = await res.json();

    document.getElementById('temperature').innerText =
        showValue(data.temperature, '°C');

    document.getElementById('humidity').innerText =
        showValue(data.humidity, '%');

    document.getElementById('pressure').innerText =
        showValue(data.pressure, 'hPa');

    document.getElementById('wind_speed').innerText =
        showValue(data.wind_speed, 'm/s');

    document.getElementById('wind_gust').innerText =
        showValue(data.wind_gust, 'm/s');

    const windText = data.wind_direction_text ? ' ' + data.wind_direction_text : '';

    document.getElementById('wind_direction').innerText =
        showValue(data.wind_direction, '°') + windText;

    document.getElementById('dew_point').innerText =
        showValue(data.dew_point, '°C');

    document.getElementById('solar_radiation').innerText =
        showValue(data.solar_radiation, 'W/m²');

    document.getElementById('uv_index').innerText =
        data.uv_index ?? '--';

    document.getElementById('last_update').innerText =
        data.last_update ?? '--';

    const status = document.getElementById('status');

    if (data.online) {
        status.innerText = '🟢 ONLINE';
        status.className = 'status online';
    } else {
        status.innerText = '🔴 OFFLINE';
        status.className = 'status offline';
    }
}

async function loadToday() {
    const res = await fetch('/api/today');
    const data = await res.json();

    document.getElementById('temperature_min').innerText =
        showValue(data.temperature_min, '°C');

    document.getElementById('temperature_max').innerText =
        showValue(data.temperature_max, '°C');

    document.getElementById('wind_speed_max').innerText =
        showValue(data.wind_speed_max, 'm/s');

    document.getElementById('wind_gust_max').innerText =
        showValue(data.wind_gust_max, 'm/s');

    document.getElementById('uv_max').innerText =
        data.uv_max ?? '--';

    document.getElementById('records_today').innerText =
        data.records_today ?? '--';
}

async function loadHistory() {
    const res = await fetch('/api/history');
    const data = await res.json();

    const labels = data.map(x => x.created_at);
    const temps = data.map(x => x.temperature);

    if (chart) {
        chart.destroy();
    }

    const ctx = document.getElementById('temperatureChart');

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Teplota °C',
                data: temps,
                borderWidth: 0.1,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: 'white'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'white'
                    }
                },
                y: {
                    ticks: {
                        color: 'white'
                    }
                }
            }
        }
    });
}

loadCurrent();
loadToday();
loadHistory();

setInterval(loadCurrent, 5000);
setInterval(loadToday, 30000);
setInterval(loadHistory, 30000);

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
        .then(() => console.log('Service Worker registered'))
        .catch(error => console.log('Service Worker error:', error));
}
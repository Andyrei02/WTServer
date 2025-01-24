const ctx = document.getElementById('temperatureChart').getContext('2d');

// Создаем градиент для кольца
const gradient = ctx.createLinearGradient(0, 0, 200, 0);
gradient.addColorStop(0, 'blue');
gradient.addColorStop(0.5, 'yellow');
gradient.addColorStop(1, 'red');

// Инициализация Chart.js
const temperatureChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    datasets: [
      {
        data: [0, 100], // Температура и оставшаяся часть
        backgroundColor: [gradient, 'rgba(0, 0, 0, 0)'], // Градиент и прозрачный фон
        borderWidth: 0, // Без обводки
        cutout: '80%', // Размер выреза в центре
        borderRadius: 15, // Закругленные края
      },
    ],
  },
  options: {
    rotation: -90, // Начало с нижней точки
    circumference: 180, // Полукруг
    plugins: {
      tooltip: { enabled: false }, // Отключаем подсказки
    },
    animation: {
      animateRotate: true, // Анимация вращения
      animateScale: true, // Анимация масштабирования
    },
  },
  plugins: [
    {
      id: 'centerText',
      beforeDraw: function (chart) {
        const { width } = chart;
        const { height } = chart;
        const { ctx } = chart;
        const temperature = chart.data.datasets[0].data[0]; // Текущая температура
        const timestamp = new Date().toLocaleTimeString(); // Время обновления

        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = 'bold 30px Arial';
        ctx.fillStyle = '#fff';
        ctx.fillText(`${temperature}°C`, width / 2, height / 2 + 25); // Температура

        ctx.font = '15px Arial';
        ctx.fillText(timestamp, width / 2, height / 2 + 65); // Время
        ctx.restore();
      },
    },
  ],
});

// Обновление температуры
function updateTemperature(temperature) {
  const percentage = Math.min(Math.max(temperature, 0), 100);
  temperatureChart.data.datasets[0].data = [percentage, 100 - percentage];
  temperatureChart.update();
}

async function fetchTemperature() {
    try {
        const response = await fetch('/current_temp');
        const data = await response.json();

        if (data.temperature !== null) {
            updateTemperature(data.temperature); // Обновление индикатора
        } else {
            console.log('Нет данных для температуры');
        }
    } catch (error) {
        console.error('Ошибка загрузки температуры:', error);
    }
}

setInterval(fetchTemperature, 5000);

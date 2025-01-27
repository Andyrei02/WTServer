const today = new Date();
let currentDate = today.toISOString().split('T')[0];

async function fetchData(date) {
  const response = await fetch(`/data/${date}`);
  return response.json();
}

async function updateGraphs(date) {
  const data = await fetchData(date);

  const timestamps = data.map(entry => entry.timestamp);
  const tempTank = data.map(entry => entry.temperature_in_tank);
  const tempHouse = data.map(entry => entry.temperature_in_house);
  const humidity = data.map(entry => entry.humidity_in_house);

  // Update charts
  tankChart.data.labels = timestamps;
  tankChart.data.datasets[0].data = tempTank;
  tankChart.update();

  houseChart.data.labels = timestamps;
  houseChart.data.datasets[0].data = tempHouse;
  houseChart.update();

  humidityChart.data.labels = timestamps;
  humidityChart.data.datasets[0].data = humidity;
  humidityChart.update();
}

function switchDay(offset) {
  const date = new Date(currentDate);
  date.setDate(date.getDate() + offset);
  currentDate = date.toISOString().split('T')[0];
  updateGraphs(currentDate);
}

// Create charts
const tankChart = new Chart(document.getElementById('temperatureTankChart'), {
  type: 'line',
  data: {
    labels: [],
    datasets: [{ label: 'Temperature in Tank', data: [], borderColor: 'red', borderWidth: 2 }]
  }
});

const houseChart = new Chart(document.getElementById('temperatureHouseChart'), {
  type: 'line',
  data: {
    labels: [],
    datasets: [{ label: 'Temperature in House', data: [], borderColor: 'blue', borderWidth: 2 }]
  }
});

const humidityChart = new Chart(document.getElementById('humidityChart'), {
  type: 'line',
  data: {
    labels: [],
    datasets: [{ label: 'Humidity in House', data: [], borderColor: 'green', borderWidth: 2 }]
  }
});

// Initial graph load
updateGraphs(currentDate);

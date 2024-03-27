let ctx = document.getElementById("chart");
let data = {
	datasets: [{
		label: "脂解試驗", 
		data: XY, 
		borderColor: "rgba(0, 0, 0, 0.5)", 
		backgroundColor: "rgb(0, 0, 0, 0.5)", 
		showLine: true
	}]
};
const config = {
	type: "scatter", 
	data: data, 
	options: {
		responsive: true, 
		maintainAspectRatio: false, 
		plugins: {
			title: {
				display: true, 
				text: "脂解試驗", 
				font: {
					size: 36
				}
			}, 
		}, 
		scales: {
			x: {
				type: "linear", 
				position: "bottom",
				title: {
					display: true, 
					text: "時間 (min)", 
					font: {
						size: 20
					}
				}, 
				ticks: {
					font: {
						size: 20
					}
				}
			}, 
			y: {
				beginAtZero: true,
				title: {
					display: true, 
					text: "NaOH使用量 (μL)", 
					font: {
						size: 20
					}
				}, 
				ticks: {
					font: {
						size: 20
					}
				}
			}
		}
	}
};
let chart = new Chart(ctx, config);
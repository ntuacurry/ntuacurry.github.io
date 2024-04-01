let X = [];
let Y = [];
let XY = [];
let initial_time;
let n = 0;
function START(){
	ini = new Date().getTime();
	X.push(0);	
	Y.push(0);
	document.getElementById("start").disabled=true;
	XY.push({x: X[n], y: Y[n]});
	chart.data.datasets[0].data = XY;
	chart.update()
	n++;
	document.getElementById("addTime").innerHTML = "實驗開始";
	document.getElementById("start").innerHTML = ENDTIME(ini);
	document.getElementById("start").style.width = "400px";
	document.getElementById("start").style.color = "rgb(255, 0, 0)";
}

function ADDTIME(now) {
		addTime = new Date(now);
		H = addTime.getHours() < 10 ? "0" + addTime.getHours():addTime.getHours()
		M = addTime.getMinutes() < 10 ? "0" + addTime.getMinutes():addTime.getMinutes()
		S = addTime.getSeconds() < 10 ? "0" + addTime.getSeconds():addTime.getSeconds()
		addTimeStr = ("上次加NaOH的時間為" + H + ":" + M + ":" + S);
		return addTimeStr
}

function ENDTIME(now) {
		endTime = new Date(now);
		H = (endTime.getHours() + 2) < 10 ? "0" + (endTime.getHours() + 2):(endTime.getHours() + 2)
		M = endTime.getMinutes() < 10 ? "0" + endTime.getMinutes():endTime.getMinutes()
		S = endTime.getSeconds() < 10 ? "0" + endTime.getSeconds():endTime.getSeconds()
		endTimeStr = ("預計結束時間為" + H + ":" + M + ":" + S);
		return endTimeStr
}

function ADD_50(){
	if (X.length == 0) {
		alert("請先按消化開始！")
	} else {
		let now = new Date().getTime();
		time_dif = (((now - ini) / 1000) / 60);
		document.getElementById("finish").disabled=false;
		X.push(time_dif);
		Y.push(Y[n - 1] + 50);
		XY.push({x: X[n], y: Y[n]});
		chart.data.datasets[0].data = XY;
		chart.update()
		n++;
		document.getElementById("addTime").innerHTML = ADDTIME(now);
	}
}

function ADD_25(){
	if (X.length == 0) {
		alert("請先按消化開始！")
	} else {
		let now = new Date().getTime();
		time_dif = (((now - ini) / 1000) / 60);
		document.getElementById("finish").disabled=false;
		X.push(time_dif);
		Y.push(Y[n - 1] + 25);
		XY.push({x: X[n], y: Y[n]});
		chart.data.datasets[0].data = XY;
		chart.update()
		n++;
		document.getElementById("addTime").innerHTML = ADDTIME(now);
	}
}

function NO_ADD(){
	if (X.length == 0) {
		alert("什麼都還沒加就想什麼都不加？？？")
	} else {
		let now = new Date().getTime();
		time_dif = (((now - ini) / 1000) / 60);
		document.getElementById("finish").disabled=false;
		X.push(time_dif);
		Y.push(Y[n - 1]);
		XY.push({x: X[n], y: Y[n]});
		chart.data.datasets[0].data = XY;
		chart.update()
		n++;
		document.getElementById("addTime").innerHTML = ADDTIME(now);
	}
}

function Download() {
	let filename = window.prompt("請輸入檔案名稱");
	if (filename == "" || filename == "null" || filename == null) {
		alert("請輸入檔案名稱！")
	} else {
		rows = [];
		for (let i = 0; i < n; i++) {
			rows.push([X[i], Y[i]]);
		};

		const workbook = new ExcelJS.Workbook();
		const sheet = workbook.addWorksheet("脂解試驗");

		sheet.addTable({
			name: "digestion",
			ref: "A1",
			columns: [{name: "時間 (min)"}, {name: "NaOH使用量 (μL)"}],
			rows: rows
		});

		workbook.xlsx.writeBuffer().then((content) => {
			const link = document.createElement("a");
			const blobData = new Blob([content], {
				type: "application / vnd.ms - excel; charset=utf - 8; "
			});
			link.download = (filename + ".xlsx");
			link.href = URL.createObjectURL(blobData);
			link.click();
		});
	}
}

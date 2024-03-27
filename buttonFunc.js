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
		}

		function ADD_50(){
			let now = new Date().getTime();
			time_dif = (((now - ini) / 1000) / 60);
			document.getElementById("finish").disabled=false;
			X.push(time_dif);
			Y.push(Y[n - 1] + 50);
			XY.push({x: X[n], y: Y[n]});
			chart.data.datasets[0].data = XY;
			chart.update()
			n++;
		}

		function ADD_25(){
			let now = new Date().getTime();
			time_dif = (((now - ini) / 1000) / 60);
			document.getElementById("finish").disabled=false;
			X.push(time_dif);
			Y.push(Y[n - 1] + 25);
			XY.push({x: X[n], y: Y[n]});
			chart.data.datasets[0].data = XY;
			chart.update()
			n++;
		}

		function NO_ADD(){
			let now = new Date().getTime();
			time_dif = (((now - ini) / 1000) / 60);
			document.getElementById("finish").disabled=false;
			X.push(time_dif);
			Y.push(Y[n - 1]);
			XY.push({x: X[n], y: Y[n]});
			chart.data.datasets[0].data = XY;
			chart.update()
			n++;
		}

		function FINISH(){
			let now = new Date().getTime();
			alert("自1970.01.01以來過了" + (ini / 1000) + "秒");
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
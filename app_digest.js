new Vue({
    el: '#app',
    data: {
        chart: null,
        timeData: [],
        volumeData: [],
        chartData: [],
        dataCount: 0,
        startTime: null,
        experimentStarted: false,
        canDownload: false,
        statusMessage: '請按下消化開始以開始記錄數據',
        startButtonText: '消化開始'
    },
    mounted() {
         this.initChart();
    },
    methods: {
        initChart() {
            const ctx = this.$refs.chart.getContext('2d');
            this.chart = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                    label: '脂解試驗',
                    data: this.chartData,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    showLine: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                    x: {
                        type: 'linear',
                        title: { display: true, text: '時間 (min)', font: { size: 14 } },
                        beginAtZero: true
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'NaOH 使用量 (μL)', font: { size: 14 } }
                    }
                    }
                }
            });
        },
        startExperiment() {
            this.startTime = new Date().getTime();
            this.timeData = [0];
            this.volumeData = [0];
            this.chartData = [{ x: 0, y: 0 }];
            this.dataCount = 1;
            this.experimentStarted = true;
            this.statusMessage = '實驗開始';
            const end = new Date(this.startTime);
            end.setHours(end.getHours() + 2);
            this.startButtonText = `預計結束時間為 ${this.formatTime(end)}`;
            this.updateChart();
        },
        addNaOH(amount) {
            const now = new Date().getTime();
            const timeDiff = ((now - this.startTime) / 1000) / 60;
            const lastVolume = this.volumeData[this.dataCount - 1];
            this.timeData.push(timeDiff);
            this.volumeData.push(lastVolume + amount);
            this.chartData.push({ x: timeDiff, y: lastVolume + amount });
            this.dataCount++;
            this.canDownload = true;
            this.statusMessage = `上次加 NaOH 的時間為 ${this.formatTime(new Date(now))}`;
            this.updateChart();
        },
        recordNoAdd() {
            const now = new Date().getTime();
            const timeDiff = ((now - this.startTime) / 1000) / 60;
            const lastVolume = this.volumeData[this.dataCount - 1];
            this.timeData.push(timeDiff);
            this.volumeData.push(lastVolume);
            this.chartData.push({ x: timeDiff, y: lastVolume });
            this.dataCount++;
            this.canDownload = true;
            this.statusMessage = `上次更新時間為 ${this.formatTime(new Date(now))}`;
            this.updateChart();
         },
      updateChart() {
        if (this.chart) {
            this.chart.data.datasets[0].data = this.chartData;
            this.chart.update();
        }
        },
        formatTime(date) {
            return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
        },
        downloadData() {
            const filename = window.prompt('請輸入檔案名稱');
            if (!filename) return alert('請輸入檔案名稱！');

            const workbook = new ExcelJS.Workbook();
            const sheet = workbook.addWorksheet('脂解試驗');
            const rows = this.timeData.map((time, i) => [time, this.volumeData[i]]);
            sheet.addTable({
                name: 'digestion',
                ref: 'A1',
                columns: [{ name: '時間 (min)' }, { name: 'NaOH使用量 (μL)' }],
                rows: rows
            });
            workbook.xlsx.writeBuffer().then(content => {
                const blob = new Blob([content], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = filename + '.xlsx';
                link.click();
                this.statusMessage = '已成功下載數據檔案';
            });
        }
    }
});

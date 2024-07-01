// 替換為您的 Google Sheets API 憑證
const CLIENT_ID = '269340063869-hua6h3613jrk1oe4sgaicakod3pm3q20.apps.googleusercontent.com';
const API_KEY = 'AIzaSyAdQ9w_Y97e8PUXbntYcZwT6i6cm3Qqbrw';
const SPREADSHEET_ID = '1hZqpxjsez2T8BNYI95F-uEe-XuXJZXZ-8S2sJ7xQ4kc';
const RANGE = 'Sheet1!A:D';

let expenses = [];
let currentDisplayMonth = new Date();

// 初始化 Google Sheets API
function initClient() {
    gapi.client.init({
        apiKey: API_KEY,
        clientId: CLIENT_ID,
        discoveryDocs: ["https://sheets.googleapis.com/$discovery/rest?version=v4"],
        scope: "https://www.googleapis.com/auth/spreadsheets"
    }).then(function () {
        loadExpenses();
    }, function(error) {
        console.error('Error initializing Google Sheets API', error);
    });
}

// 載入支出數據
function loadExpenses() {
    gapi.client.sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: RANGE
    }).then(function(response) {
        const values = response.result.values;
        if (values && values.length > 0) {
            expenses = values.map(row => ({
                date: row[0],
                amount: parseInt(row[1]),
                type: row[2],
                note: row[3]
            }));
            updateContent();
        }
    }, function(response) {
        console.error('Error loading expenses', response.result.error.message);
    });
}

// 添加新支出
function addExpense(date, amount, type, note) {
    gapi.client.sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: RANGE,
        valueInputOption: 'USER_ENTERED',
        resource: {
            values: [[date, amount, type, note]]
        }
    }).then(function(response) {
        expenses.push({date, amount: parseInt(amount), type, note});
        expenses.sort((a, b) => new Date(a.date) - new Date(b.date));
        updateContent();
    }, function(response) {
        console.error('Error adding expense', response.result.error.message);
    });
}

function openTab(tabName) {
    var tabContent = document.getElementsByClassName("tab-content");
    for (var i = 0; i < tabContent.length; i++) {
        tabContent[i].style.display = "none";
    }
    var tabButtons = document.getElementsByClassName("tab-button");
    for (var i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove("active");
    }
    document.getElementById(tabName).style.display = "block";
    document.querySelector(`[onclick="openTab('${tabName}')"]`).classList.add("active");

    updateContent();
}

function updateContent() {
    updateExpenseTable();
    updateMealExpensesChart();
    updateOverallExpensesChart();
}

function updateDateTime() {
    var now = new Date();
    var year = now.getFullYear() - 1911; // 轉換為民國年
    var month = (now.getMonth() + 1).toString().padStart(2, '0');
    var day = now.getDate().toString().padStart(2, '0');
    var hours = now.getHours().toString().padStart(2, '0');
    var minutes = now.getMinutes().toString().padStart(2, '0');
    var seconds = now.getSeconds().toString().padStart(2, '0');
    
    var dateTimeString = year + '/' + month + '/' + day + ' ' + hours + ':' + minutes + ':' + seconds;
    document.getElementById('datetime').textContent = dateTimeString;
}

setInterval(updateDateTime, 1000);

var modal = document.getElementById("modal");
var btn = document.getElementById("addButton");
var saveButton = document.getElementById("saveButton");
var cancelButton = document.getElementById("cancelButton");

btn.onclick = function() {
    modal.style.display = "block";
    document.getElementById('date').valueAsDate = new Date();
}

function clearModalForm() {
    document.getElementById('date').value = '';
    document.getElementById('amount').value = '';
    document.getElementById('type').value = '';
    document.getElementById('note').value = '';
}

cancelButton.onclick = function() {
    modal.style.display = "none";
    clearModalForm();
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
        clearModalForm();
    }
}

saveButton.onclick = function() {
    const date = document.getElementById('date').value;
    const amount = document.getElementById('amount').value;
    const type = document.getElementById('type').value;
    const note = document.getElementById('note').value;

    if (date && amount && type) {
        addExpense(date, amount, type, note);
        modal.style.display = "none";
        clearModalForm();
    } else {
        alert('請填寫所有必填欄位');
    }
}

function updateExpenseTable() {
    const tbody = document.querySelector('#expenseTable tbody');
    tbody.innerHTML = '';

    const filteredExpenses = getFilteredExpenses();

    let currentDate = null;
    filteredExpenses.forEach((expense) => {
        const row = tbody.insertRow();
        
        if (expense.date !== currentDate) {
            const dateCell = row.insertCell();
            dateCell.textContent = expense.date;
            dateCell.classList.add('date-cell');
            dateCell.rowSpan = filteredExpenses.filter(e => e.date === expense.date).length;
            currentDate = expense.date;
        }

        const amountCell = row.insertCell();
        amountCell.textContent = expense.amount;

        const typeCell = row.insertCell();
        typeCell.textContent = expense.type;

        const noteCell = row.insertCell();
        noteCell.textContent = expense.note;
    });
}

function getFilteredExpenses() {
    return expenses.filter(expense => {
        const expenseDate = new Date(expense.date);
        return expenseDate.getMonth() === currentDisplayMonth.getMonth() &&
               expenseDate.getFullYear() === currentDisplayMonth.getFullYear();
    });
}

function updateMealExpensesChart() {
    const filteredExpenses = getFilteredExpenses();

    const mealCategories = ['早餐', '午餐', '晚餐', '飲料'];
    const mealExpenses = mealCategories.map(category => 
        filteredExpenses.filter(expense => expense.type === category)
                       .reduce((sum, expense) => sum + expense.amount, 0)
    );

    const ctx = document.getElementById('mealExpensesChart').getContext('2d');
    
    if (window.mealChart) {
        window.mealChart.destroy();
    }

    window.mealChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: mealCategories,
            datasets: [{
                data: mealExpenses,
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: '飲食支出分布'
            }
        }
    });
}

function updateOverallExpensesChart() {
    const filteredExpenses = getFilteredExpenses();

    const categories = ['食物', '房租+電費', '交通', '手機費', '日常開銷', '投資', '投資自己', '儲蓄', '外幣', '其他'];
    const categoryExpenses = categories.map(category => 
        filteredExpenses.filter(expense => expense.type === category)
                       .reduce((sum, expense) => sum + expense.amount, 0)
    );

    const ctx = document.getElementById('overallExpensesChart').getContext('2d');
    
    if (window.overallChart) {
        window.overallChart.destroy();
    }

    window.overallChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: categories,
            datasets: [{
                data: categoryExpenses,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                    '#FF9F40', '#FF6384', '#C9CBCF', '#7CFC00', '#8B4513'
                ]
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: '整體支出分布'
            }
        }
    });
}

document.getElementById('prevMonth').addEventListener('click', function() {
    currentDisplayMonth.setMonth(currentDisplayMonth.getMonth() - 1);
    updateMonthDisplay();
    updateContent();
});

document.getElementById('nextMonth').addEventListener('click', function() {
    currentDisplayMonth.setMonth(currentDisplayMonth.getMonth() + 1);
    updateMonthDisplay();
    updateContent();
});

function updateMonthDisplay() {
    const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "十一月", "十二月"
    ];
    document.getElementById('currentMonth').textContent = 
        `${currentDisplayMonth.getFullYear()}年 ${monthNames[currentDisplayMonth.getMonth()]}`;
}

// 初始化頁面
function init() {
    gapi.load('client:auth2', initClient);
    updateMonthDisplay();
    openTab('home');
}

// 當頁面加載完成時調用 init 函數
window.onload = init;

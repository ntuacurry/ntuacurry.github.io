// Google Sheets API 設定
const API_KEY = '7be2c667a11312a0e1ce0d110ecef6637c5cc65a';
const SPREADSHEET_ID = '1hZqpxjsez2T8BNYI95F-uEe-XuXJZXZ-8S2sJ7xQ4kc';
const RANGE = 'Sheet1!A:D';  // 假設我們使用 Sheet1，從 A 列到 D 列

let expenses = [];

// 初始化 Google Sheets API
function initClient() {
    gapi.client.init({
        apiKey: API_KEY,
        discoveryDocs: ["https://sheets.googleapis.com/$discovery/rest?version=v4"],
    }).then(function() {
        loadExpenses();
    }, function(error) {
        console.error('Error initializing Google Sheets API', error);
    });
}

// 載入支出資料
function loadExpenses() {
    gapi.client.sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: RANGE,
    }).then(function(response) {
        const values = response.result.values;
        if (values && values.length > 0) {
            expenses = values.map(row => ({
                date: row[0],
                amount: parseFloat(row[1]),
                type: row[2],
                note: row[3] || ''
            }));
            updateExpenseTable();
            updateMealExpensesChart();
        }
    }, function(response) {
        console.error('Error loading data from Google Sheets', response.result.error.message);
    });
}

// 添加支出
function addExpense(date, amount, type, note) {
    const newExpense = {date, amount: parseFloat(amount), type, note};
    expenses.push(newExpense);
    expenses.sort((a, b) => new Date(a.date) - new Date(b.date));

    // 將新支出添加到 Google Sheets
    gapi.client.sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: RANGE,
        valueInputOption: 'USER_ENTERED',
        resource: {
            values: [[date, amount, type, note]]
        }
    }).then(function(response) {
        console.log('Expense added to Google Sheets');
        updateExpenseTable();
        updateMealExpensesChart();
    }, function(response) {
        console.error('Error adding expense to Google Sheets', response.result.error.message);
    });
}

function openTab(tabName) {
    var i, tabContent, tabButtons;
    tabContent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabContent.length; i++) {
        tabContent[i].style.display = "none";
    }
    tabButtons = document.getElementsByClassName("tab-button");
    for (i = 0; i < tabButtons.length; i++) {
        tabButtons[i].className = tabButtons[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    event.currentTarget.className += " active";

    if (tabName === 'home') {
        updateMealExpensesChart();
    }
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

function updateExpenseTable() {
    const tbody = document.querySelector('#expenseTable tbody');
    tbody.innerHTML = '';

    let currentDate = null;
    expenses.forEach((expense, index) => {
        const row = tbody.insertRow();
        
        if (expense.date !== currentDate) {
            const dateCell = row.insertCell();
            dateCell.textContent = expense.date;
            dateCell.classList.add('date-cell');
            dateCell.rowSpan = expenses.filter(e => e.date === expense.date).length;
            currentDate = expense.date;
        }

        const amountCell = row.insertCell();
        amountCell.textContent = expense.amount.toFixed(2);

        const typeCell = row.insertCell();
        typeCell.textContent = expense.type;

        const noteCell = row.insertCell();
        noteCell.textContent = expense.note;
    });
}

function updateMealExpensesChart() {
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    const currentYear = currentDate.getFullYear();

    const monthlyExpenses = expenses.filter(expense => {
        const expenseDate = new Date(expense.date);
        return expenseDate.getMonth() === currentMonth && expenseDate.getFullYear() === currentYear;
    });

    const mealCategories = ['早餐', '午餐', '晚餐', '飲料'];
    const mealExpenses = mealCategories.map(category => 
        monthlyExpenses.filter(expense => expense.type === category)
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
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: '本月餐飲消費分類'
            }
        }
    });
}

// 初始化頁面
document.addEventListener('DOMContentLoaded', function() {
    gapi.load('client', initClient);
    updateDateTime();
    openTab('home');

    // 設置事件監聽器
    document.getElementById('addButton').onclick = function() {
        modal.style.display = "block";
        document.getElementById('date').valueAsDate = new Date();
    }

    document.getElementById('cancelButton').onclick = function() {
        modal.style.display = "none";
    }

    document.getElementById('saveButton').onclick = function() {
        const date = document.getElementById('date').value;
        const amount = document.getElementById('amount').value;
        const type = document.getElementById('type').value;
        const note = document.getElementById('note').value;

        if (date && amount && type) {
            addExpense(date, amount, type, note);
            modal.style.display = "none";
            // 清空表單
            document.getElementById('date').value = '';
            document.getElementById('amount').value = '';
            document.getElementById('type').value = '';
            document.getElementById('note').value = '';
        } else {
            alert('請填寫所有必要欄位');
        }
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    setInterval(updateDateTime, 1000);
});
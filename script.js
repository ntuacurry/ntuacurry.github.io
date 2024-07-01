const CLIENT_ID = '118287483567917938340';
const API_KEY = 'AIzaSyAdQ9w_Y97e8PUXbntYcZwT6i6cm3Qqbrw';
const SPREADSHEET_ID = '1hZqpxjsez2T8BNYI95F-uEe-XuXJZXZ-8S2sJ7xQ4kc';
const RANGE = 'Sheet1!A:D';

let expenses = [];
let currentDisplayMonth = new Date();

function initClient() {
    gapi.load('client:auth2', () => {
        gapi.client.init({
            apiKey: API_KEY,
            clientId: CLIENT_ID,
            discoveryDocs: ["https://sheets.googleapis.com/$discovery/rest?version=v4"],
            scope: "https://www.googleapis.com/auth/spreadsheets"
        }).then(() => {
            loadExpenses();
        }, (error) => {
            console.error('Error initializing Google Sheets API', error);
        });
    });
}

function loadExpenses() {
    gapi.client.sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: RANGE
    }).then((response) => {
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
    }, (response) => {
        console.error('Error loading expenses', response.result.error.message);
    });
}

function addExpense(date, amount, type, note) {
    gapi.client.sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: RANGE,
        valueInputOption: 'USER_ENTERED',
        resource: {
            values: [[date, amount, type, note]]
        }
    }).then((response) => {
        expenses.push({date, amount: parseInt(amount), type, note});
        expenses.sort((a, b) => new Date(a.date) - new Date(b.date));
        updateContent();
    }, (response) => {
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
    var date = document.getElementById('date').value;
    var amount = document.getElementById('amount').value;
    var type = document.getElementById('type').value;
    var note = document.getElementById('note').value;

    if (date && amount && type) {
        addExpense(date, amount, type, note);
        modal.style.display = "none";
        clearModalForm();
    } else {
        alert("請填寫所有必填欄位");
    }
}

document.getElementById("prevMonth").onclick = function() {
    currentDisplayMonth.setMonth(currentDisplayMonth.getMonth() - 1);
    updateContent();
}

document.getElementById("nextMonth").onclick = function() {
    currentDisplayMonth.setMonth(currentDisplayMonth.getMonth() + 1);
    updateContent();
}

function updateExpenseTable() {
    var tbody = document.getElementById('expenseTable').getElementsByTagName('tbody')[0];
    tbody.innerHTML = '';

    expenses.forEach(expense => {
        var tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${expense.date}</td>
            <td>${expense.amount}</td>
            <td>${expense.type}</td>
            <td>${expense.note}</td>
        `;
        tbody.appendChild(tr);
    });
}

function updateMealExpensesChart() {
    var mealExpenses = expenses.filter(expense => ['早餐', '午餐', '晚餐'].includes(expense.type));
    var mealTypes = ['早餐', '午餐', '晚餐'];
    var mealSums = mealTypes.map(type => mealExpenses.filter(expense => expense.type === type).reduce((sum, expense) => sum + expense.amount, 0));

    var ctx = document.getElementById('mealExpensesChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: mealTypes,
            datasets: [{
                data: mealSums,
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
            }]
        }
    });
}

function updateOverallExpensesChart() {
    var expenseTypes = [...new Set(expenses.map(expense => expense.type))];
    var expenseSums = expenseTypes.map(type => expenses.filter(expense => expense.type === type).reduce((sum, expense) => sum + expense.amount, 0));

    var ctx = document.getElementById('overallExpensesChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: expenseTypes,
            datasets: [{
                data: expenseSums,
                backgroundColor: expenseTypes.map(() => '#' + Math.floor(Math.random()*16777215).toString(16)),
            }]
        }
    });
}

initClient();
openTab('home');
// 替換為您的 Google Sheets API 憑證
const CLIENT_ID = '269340063869-hua6h3613jrk1oe4sgaicakod3pm3q20.apps.googleusercontent.com';
const API_KEY = 'AIzaSyAdQ9w_Y97e8PUXbntYcZwT6i6cm3Qqbrw';
const SPREADSHEET_ID = '1hZqpxjsez2T8BNYI95F-uEe-XuXJZXZ-8S2sJ7xQ4kc';

let tokenClient;
let expenses = [];
let currentDisplayMonth = new Date();
let isAuthorized = false;

function init() {
    gapi.load('client', initGapiClient);
    updateMonthDisplay();
    document.addEventListener('DOMContentLoaded', function() {
        openTab('home');
        initBudgetTable();
    });
}

window.onload = init;

function initGapiClient() {
    gapi.client.init({
        apiKey: API_KEY,
        discoveryDocs: ["https://sheets.googleapis.com/$discovery/rest?version=v4"],
    }).then(() => {
        console.log('GAPI client initialized');
        tokenClient = google.accounts.oauth2.initTokenClient({
            client_id: CLIENT_ID,
            scope: 'https://www.googleapis.com/auth/spreadsheets',
            callback: (tokenResponse) => {
                if (tokenResponse && tokenResponse.access_token) {
                    isAuthorized = true;
                    loadExpenses();
                }
            },
        });
    }, (error) => {
        console.error('Error initializing GAPI client', error);
    });
}

function getToken() {
    if (!isAuthorized) {
        tokenClient.requestAccessToken();
    } else {
        console.log('Already authorized');
    }
}

function loadExpenses() {
    const sheetName = getCurrentSheetName();
    gapi.client.sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A:E`
    }).then(function(response) {
        const values = response.result.values;
        if (values && values.length > 0) {
            expenses = values.slice(1).map((row) => ({
                id: parseInt(row[0]),
                date: row[1],
                amount: parseInt(row[2]),
                type: row[3],
                note: row[4]
            }));
            updateContent();
        }
    }, function(response) {
        console.error('Error loading expenses', response.result.error.message);
    });
}

function addExpense(date, amount, type, note) {
    checkAndCreateSheet();
    const sheetName = getCurrentSheetName();
    gapi.client.sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A:A`
    }).then(function(response) {
        const values = response.result.values;
        const newIndex = values ? values.length : 1;
        gapi.client.sheets.spreadsheets.values.append({
            spreadsheetId: SPREADSHEET_ID,
            range: `${sheetName}!A:E`,
            valueInputOption: 'USER_ENTERED',
            resource: {
                values: [[newIndex, date, amount, type, note]]
            }
        }).then(function(response) {
            const newExpense = {id: newIndex, date, amount: parseInt(amount), type, note};
            expenses.push(newExpense);
            expenses.sort((a, b) => new Date(a.date) - new Date(b.date));
            updateContent();
        }, function(response) {
            console.error('Error adding expense', response.result.error.message);
            getToken();
        });
    });
}

function updateExpense(id, date, amount, type, note) {
    const sheetName = getCurrentSheetName();
    gapi.client.sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A${id + 1}:E${id + 1}`,
        valueInputOption: 'USER_ENTERED',
        resource: {
            values: [[id, date, amount, type, note]]
        }
    }).then(function(response) {
        const index = expenses.findIndex(e => e.id === id);
        if (index !== -1) {
            expenses[index] = {id, date, amount: parseInt(amount), type, note};
            updateExpenseTable();
            updateContent();
        }
    }, function(response) {
        console.error('Error updating expense', response.result.error.message);
        getToken();
    });
}

function deleteExpense(id) {
    const sheetName = getCurrentSheetName();
    gapi.client.sheets.spreadsheets.values.clear({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A${id + 1}:E${id + 1}`
    }).then(function(response) {
        const index = expenses.findIndex(e => e.id === id);
        if (index !== -1) {
            expenses.splice(index, 1);
            updateExpenseTable();
            updateContent();
        }
    }, function(response) {
        console.error('Error deleting expense', response.result.error.message);
        getToken();
    });
}

function getCurrentSheetName() {
    const date = new Date();
    const year = date.getFullYear();
    const month = date.toLocaleString('en-US', { month: 'short' });
    return `${year}-${month}`;
}

function checkAndCreateSheet() {
    const sheetName = getCurrentSheetName();
    gapi.client.sheets.spreadsheets.get({
        spreadsheetId: SPREADSHEET_ID
    }).then(function(response) {
        const sheets = response.result.sheets;
        const sheetExists = sheets.some(sheet => sheet.properties.title === sheetName);
        if (!sheetExists) {
            createNewSheet(sheetName);
        }
    });
}

function createNewSheet(sheetName) {
    gapi.client.sheets.spreadsheets.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        resource: {
            requests: [{
                addSheet: {
                    properties: {
                        title: sheetName
                    }
                }
            }]
        }
    }).then(function(response) {
        console.log('New sheet created:', sheetName);
        gapi.client.sheets.spreadsheets.values.update({
            spreadsheetId: SPREADSHEET_ID,
            range: `${sheetName}!A1:E1`,
            valueInputOption: 'USER_ENTERED',
            resource: {
                values: [["Index", "Date", "Amount", "Type", "Remark"]]
            }
        }).then(function(response) {
            console.log('Header added to new sheet');
        }, function(response) {
            console.error('Error adding header to new sheet', response.result.error.message);
        });
    }, function(response) {
        console.error('Error creating new sheet', response.result.error.message);
    });
}

function updateContent() {
    updateExpenseTable();
    updateMealExpensesChart();
    updateOverallExpensesChart();
    updateDailyExpenses();
}

function updateDateTime() {
    var now = new Date();
    var year = now.getFullYear() - 1911;
    var month = (now.getMonth() + 1).toString().padStart(2, '0');
    var day = now.getDate().toString().padStart(2, '0');
    var hours = now.getHours().toString().padStart(2, '0');
    var minutes = now.getMinutes().toString().padStart(2, '0');
    var seconds = now.getSeconds().toString().padStart(2, '0');
    
    var dateTimeString = year + '/' + month + '/' + day + ' ' + hours + ':' + minutes + ':' + seconds;
    document.getElementById('datetime').textContent = dateTimeString;
}

setInterval(updateDateTime, 1000);

function updateMonthDisplay() {
    const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "十一月", "十二月"
    ];
    document.getElementById('currentMonth').textContent = 
        `${currentDisplayMonth.getFullYear()}年 ${monthNames[currentDisplayMonth.getMonth()]}`;
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
    var selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.style.display = "block";
    }
    var selectedButton = document.querySelector(`[onclick="openTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add("active");
    }

    if (tabName === 'dashboard' || tabName === 'expenses') {
        updateDailyExpenses();
    }

    if (tabName === 'budget') {
        initBudgetTable();
    }
}

function updateDailyExpenses() {
    const filteredExpenses = getFilteredExpenses();
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    const currentYear = currentDate.getFullYear();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    
    const daysPassed = Math.min(currentDate.getDate(), daysInMonth);

    const totalFoodExpense = filteredExpenses.filter(expense => 
        ['早餐', '午餐', '晚餐', '飲料', '食物'].includes(expense.type)
    ).reduce((sum, expense) => sum + expense.amount, 0);

    const totalExpense = filteredExpenses.reduce((sum, expense) => sum + expense.amount, 0);

    const dailyFoodExpense = (totalFoodExpense / daysPassed).toFixed(1);
    const dailyTotalExpense = (totalExpense / daysInMonth).toFixed(1);

    updatePageDailyExpenses('dashboard', dailyFoodExpense, dailyTotalExpense);
    updatePageDailyExpenses('expense', dailyFoodExpense, dailyTotalExpense);
}

function updatePageDailyExpenses(page, dailyFoodExpense, dailyTotalExpense) {
    const dailyFoodExpenseElement = document.getElementById(`${page}DailyFoodExpense`);
    const dailyTotalExpenseElement = document.getElementById(`${page}DailyTotalExpense`);

    if (dailyFoodExpenseElement) {
        dailyFoodExpenseElement.textContent = `日均飲食花費為${dailyFoodExpense}元`;
    }
    if (dailyTotalExpenseElement) {
        dailyTotalExpenseElement.textContent = `本月日均開銷為${dailyTotalExpense}元`;
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

        const actionCell = row.insertCell();
        const editButton = document.createElement('button');
        editButton.textContent = '修改';
        editButton.onclick = () => editExpense(expense);
        actionCell.appendChild(editButton);

        const deleteButton = document.createElement('button');
        deleteButton.textContent = '刪除';
        deleteButton.onclick = () => deleteExpense(expense.id);
        actionCell.appendChild(deleteButton);
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

    const categories = ['飲食', '居住', '交通', '日常生活開銷', '投資自己', '儲蓄', '投資'];
    const categoryExpenses = categories.map(category => {
        switch(category) {
            case '飲食':
                return filteredExpenses.filter(expense => ['早餐', '午餐', '晚餐', '飲料', '食物'].includes(expense.type))
                                       .reduce((sum, expense) => sum + expense.amount, 0);
            case '居住':
                return filteredExpenses.filter(expense => expense.type === '房租')
                                       .reduce((sum, expense) => sum + expense.amount, 0);
            case '交通':
                return filteredExpenses.filter(expense => expense.type === '交通')
                                       .reduce((sum, expense) => sum + expense.amount, 0);
            case '日常生活開銷':
                return filteredExpenses.filter(expense => ['手機費', '電費', '其他', '日常開銷'].includes(expense.type))
                                       .reduce((sum, expense) => sum + expense.amount, 0);
            case '投資自己':
                return filteredExpenses.filter(expense => expense.type === '投資自己')
                                       .reduce((sum, expense) => sum + expense.amount, 0);
            case '儲蓄':
                return filteredExpenses.filter(expense => expense.type === '儲蓄')
                                       .reduce((sum, expense) => sum + expense.amount, 0);
            case '投資':
                return filteredExpenses.filter(expense => ['投資', '外幣'].includes(expense.type))
                                       .reduce((sum, expense) => sum + expense.amount, 0);
        }
    });

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
                    '#FF9F40', '#FF6384'
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

function initBudgetTable() {
    const table = document.getElementById('yearlyBudgetTable');
    if (!table) {
        console.error('Table with id "yearlyBudgetTable" not found');
        return;
    }

    // 在這裡生成全年預算表格的內容
    // 這部分代碼需要根據您的具體需求來實現
    // ...

    const headerRow = table.rows[0];
    if (headerRow) {
        for (let i = 1; i < headerRow.cells.length - 1; i++) {
            const cell = headerRow.cells[i];
            if (cell) {
                cell.removeEventListener('click', openMonthlyDetailModal);
                cell.addEventListener('click', function() {
                    openMonthlyDetailModal(i);
                });
            }
        }
    } else {
        console.error('Header row not found in the table');
    }
}

function openMonthlyDetailModal(monthIndex) {
    const months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];
    const year = document.getElementById('yearSelector').value;
    const month = months[monthIndex - 1];
    
    document.getElementById('monthlyDetailTitle').textContent = `${year}年${month} 收入及預算`;
    document.getElementById('incomeTableContainer').innerHTML = generateIncomeTable();
    document.getElementById('expenseTableContainer').innerHTML = generateExpenseTable();
    document.getElementById('monthlyDetailContainer').style.display = 'block';
}

function generateIncomeTable() {
    // 生成收入表格的 HTML
    // ...
}

function generateExpenseTable() {
    // 生成支出表格的 HTML
    // ...
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

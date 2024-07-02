// 替換為您的 Google Sheets API 憑證
const CLIENT_ID = '269340063869-hua6h3613jrk1oe4sgaicakod3pm3q20.apps.googleusercontent.com';
const API_KEY = 'AIzaSyAdQ9w_Y97e8PUXbntYcZwT6i6cm3Qqbrw';
const SPREADSHEET_ID = '1hZqpxjsez2T8BNYI95F-uEe-XuXJZXZ-8S2sJ7xQ4kc';
const RANGE = '2024-Jul!A:E';

let tokenClient;
let expenses = [];
let currentDisplayMonth = new Date();

function initClient() {
    tokenClient = google.accounts.oauth2.initTokenClient({
        client_id: CLIENT_ID,
        scope: 'https://www.googleapis.com/auth/spreadsheets',
        callback: (tokenResponse) => {
            if (tokenResponse && tokenResponse.access_token) {
                loadExpenses();
            }
        },
    });

    gapi.load('client', initGapiClient);
}

function initGapiClient() {
    gapi.client.init({
        apiKey: API_KEY,
        discoveryDocs: ["https://sheets.googleapis.com/$discovery/rest?version=v4"],
    }).then(() => {
        console.log('GAPI client initialized');
    }, (error) => {
        console.error('Error initializing GAPI client', error);
    });
}

function getToken() {
    tokenClient.requestAccessToken();
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
        // 添加表頭
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

    loadExpenses();

    if (tabName === 'dashboard' || tabName === 'expenses') {
        updateDailyExpenses();
    }
}

function updateContent() {
    updateExpenseTable();
    updateMealExpensesChart();
    updateOverallExpensesChart();
    updateDailyExpenses();
}

function updateDailyExpenses() {
    const filteredExpenses = getFilteredExpenses();
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    const currentYear = currentDate.getFullYear();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    
    // 計算到當月底
    const daysPassed = Math.min(currentDate.getDate(), daysInMonth);

    const totalFoodExpense = filteredExpenses.filter(expense => 
        ['早餐', '午餐', '晚餐', '飲料', '食物'].includes(expense.type)
    ).reduce((sum, expense) => sum + expense.amount, 0);

    const totalExpense = filteredExpenses.reduce((sum, expense) => sum + expense.amount, 0);

    const dailyFoodExpense = (totalFoodExpense / daysPassed).toFixed(1);
    const dailyTotalExpense = (totalExpense / daysInMonth).toFixed(1);

    // 更新收支儀錶板頁面
    updatePageDailyExpenses('dashboard', dailyFoodExpense, dailyTotalExpense);

    // 更新消費紀錄頁面
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
    
    // 設置日期選擇器的預設值為當前日期
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
    var yyyy = today.getFullYear();

    today = yyyy + '-' + mm + '-' + dd;
    document.getElementById('date').value = today;
}

function clearModalForm() {
    document.getElementById('expenseId').value = '';
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
    const id = document.getElementById('expenseId').value;
    const date = document.getElementById('date').value;
    const amount = document.getElementById('amount').value;
    const type = document.getElementById('type').value;
    const note = document.getElementById('note').value;

    if (date && amount && type) {
        if (id) {
            updateExpense(parseInt(id), date, amount, type, note);
        } else {
            addExpense(date, amount, type, note);
        }
        modal.style.display = "none";
        clearModalForm();
    } else {
        alert('請填寫所有必填欄位');
    }
}

function initBudgetTable() {
    const table = document.getElementById('budgetTable');
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        for (let j = 0; j < 13; j++) {
            const cell = rows[i].insertCell();
            cell.textContent = '0';
            cell.addEventListener('click', function() {
                openBudgetModal(i - 1, j);
            });
        }
    }
}

function openBudgetModal(rowIndex, colIndex) {
    const modal = document.getElementById('modal');
    const modalContent = document.querySelector('.modal-content');
    
    // 清空現有內容
    modalContent.innerHTML = '';
    
    // 添加新內容
    const title = document.createElement('h2');
    title.textContent = `編輯 ${rowIndex === 0 ? '自由現金' : rowIndex === 1 ? '支出預算' : '收入'}`;
    modalContent.appendChild(title);
    
    const input = document.createElement('input');
    input.type = 'number';
    input.value = document.getElementById('budgetTable').rows[rowIndex + 1].cells[colIndex + 1].textContent;
    modalContent.appendChild(input);
    
    const saveButton = document.createElement('button');
    saveButton.textContent = '保存';
    saveButton.onclick = function() {
        saveBudgetData(rowIndex, colIndex, input.value);
        modal.style.display = 'none';
    };
    modalContent.appendChild(saveButton);
    
    const cancelButton = document.createElement('button');
    cancelButton.textContent = '取消';
    cancelButton.onclick = function() {
        modal.style.display = 'none';
    };
    modalContent.appendChild(cancelButton);
    
    modal.style.display = 'block';
}

function saveBudgetData(rowIndex, colIndex, value) {
    const table = document.getElementById('budgetTable');
    table.rows[rowIndex + 1].cells[colIndex + 1].textContent = value;
    
    // 更新自由現金
    if (rowIndex !== 0) {
        const income = parseInt(table.rows[3].cells[colIndex + 1].textContent);
        const expense = parseInt(table.rows[2].cells[colIndex + 1].textContent);
        table.rows[1].cells[colIndex + 1].textContent = income - expense;
    }
    
    updateTotals();
}

function updateTotals() {
    const table = document.getElementById('budgetTable');
    
    for (let i = 1; i < 4; i++) {
        let total = 0;
        for (let j = 1; j <= 12; j++) {
            total += parseInt(table.rows[i].cells[j].textContent);
        }
        table.rows[i].cells[13].textContent = total;
    }
}

document.getElementById('yearSelector').addEventListener('change', function() {
    // 這裡可以添加載入不同年份數據的邏輯
    console.log('Selected year:', this.value);
});

// 在init函數中調用initBudgetTable
function init() {
    gapi.load('client', initClient);
    updateMonthDisplay();
    openTab('home');
    initBudgetTable();
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

function editExpense(expense) {
    document.getElementById('expenseId').value = expense.id;
    document.getElementById('date').value = expense.date;
    document.getElementById('amount').value = expense.amount;
    document.getElementById('type').value = expense.type;
    document.getElementById('note').value = expense.note;
    modal.style.display = "block";
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

function init() {
    gapi.load('client', initClient);
    updateMonthDisplay();
    openTab('home');
}

window.onload = init;

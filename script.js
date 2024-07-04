// 替換為您的 Google Sheets API 憑證
const CLIENT_ID = '269340063869-hua6h3613jrk1oe4sgaicakod3pm3q20.apps.googleusercontent.com';
const API_KEY = 'AIzaSyAdQ9w_Y97e8PUXbntYcZwT6i6cm3Qqbrw';
const SPREADSHEET_ID = '1hZqpxjsez2T8BNYI95F-uEe-XuXJZXZ-8S2sJ7xQ4kc';

let tokenClient;
let expenses = [];
let currentDisplayMonth = new Date();
let isAuthorized = false;
//預算頁面所需的變數
let currentBudgetMonth = new Date().getMonth() + 1;
let currentBudgetYear = new Date().getFullYear();

var modal = document.getElementById("modal");
var btn = document.getElementById("addButton");
var saveButton = document.getElementById("saveButton");
var cancelButton = document.getElementById("cancelButton");

const budgetCache = new Map();

function init() {
    gapi.load('client', initGapiClient);
    updateMonthDisplay();
    document.addEventListener('DOMContentLoaded', function() {
        openTab('home');
        setInterval(updateDateTime, 1000);
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
					loadExpenses().then(() => {
						updateContent();
					}).catch((error) => {
						console.error('Failed to load expenses:', error);
					});
                }
            },
        });
    }, (error) => {
        console.error('Error initializing GAPI client', error);
    });
}

function getToken() {
    if (!isAuthorized) {
        tokenClient.requestAccessToken({
            callback: (tokenResponse) => {
                if (tokenResponse && tokenResponse.access_token) {
                    isAuthorized = true;
                    loadExpenses().then(() => {
                        updateContent();
                        // 更新預算頁面
                        initBudgetPage();
                    });
                }
            }
        });
    } else {
        console.log('Already authorized');
    }
}

const throttle = (func, limit) => {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

const throttledLoadExpenses = throttle(loadExpenses, 1000);

function loadExpenses() {
    return new Promise((resolve, reject) => {
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
                console.log('Expenses loaded:', expenses);
                resolve();
            } else {
                console.log('No expenses data found');
                resolve();
            }
        }, function(response) {
            console.error('Error loading expenses', response.result.error.message);
            reject(response.result.error);
        });
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

btn.onclick = function() {
    modal.style.display = "block";
    
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
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
        const currentYear = new Date().getFullYear();
        checkAndCreateBudgetSheet(currentYear).then(() => {
            loadBudgetData(currentYear, currentBudgetMonth).then(data => {
                updateBudgetTables(data, currentYear, currentBudgetMonth);
            });
        });
    }

    if (tabName === 'budget') {
        initBudgetPage();
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
	if (!expenses || !Array.isArray(expenses)) {
        console.log('Expenses data not available yet');
        return;
    }
	const tbody = document.querySelector('#expenseTable tbody');
    tbody.innerHTML = '';

    const filteredExpenses = getFilteredExpenses();

    if (!filteredExpenses || filteredExpenses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">暫無支出數據</td></tr>';
        return;
    }

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
        editButton.addEventListener('click', function() {
            editExpense(expense);
        });
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

//預算頁面功能區
//初始化預算頁面
function initBudgetPage() {
    updateBudgetMonthDisplay();
    const currentYear = new Date().getFullYear();
    if (isAuthorized) {
        checkAndCreateBudgetSheet(currentYear).then(() => {
            updateYearlyBudgetTable(currentYear);
            getCachedBudgetData(currentYear, currentBudgetMonth).then(data => {
	        updateBudgetTables(data, currentYear, currentBudgetMonth);
	    });
        });
    } else {
        document.getElementById('incomeTable').innerHTML = '<tr><td colspan="4">請先進行授權</td></tr>';
        document.getElementById('expenseTable').innerHTML = '<tr><td colspan="4">請先進行授權</td></tr>';
        document.getElementById('yearlyBudgetTable').innerHTML = '<tr><td colspan="14">請先進行授權</td></tr>';
    }

    document.getElementById('prevMonthBudget').addEventListener('click', function() {
        if (currentBudgetMonth === 1) {
            currentBudgetMonth = 12;
            currentYear--;
        } else {
            currentBudgetMonth--;
        }
        updateBudgetMonthDisplay();
        getCachedBudgetData(currentYear, currentBudgetMonth).then(data => {
	    updateBudgetTables(data, currentYear, currentBudgetMonth);
	});
    });

    document.getElementById('nextMonthBudget').addEventListener('click', function() {
        if (currentBudgetMonth === 12) {
            currentBudgetMonth = 1;
            currentYear++;
        } else {
            currentBudgetMonth++;
        }
        updateBudgetMonthDisplay();
        getCachedBudgetData(currentYear, currentBudgetMonth).then(data => {
	    updateBudgetTables(data, currentYear, currentBudgetMonth);
	});
    });
}

//檢查和建立新活頁簿
function checkAndCreateBudgetSheet(year) {
    const sheetName = `${year}-budget`;
    return gapi.client.sheets.spreadsheets.get({
        spreadsheetId: SPREADSHEET_ID
    }).then(response => {
        const sheets = response.result.sheets;
        const sheetExists = sheets.some(sheet => sheet.properties.title === sheetName);
        if (!sheetExists) {
            return createNewBudgetSheet(sheetName);
        }
        return Promise.resolve();
    });
}

//建立新的預算活頁簿
function createNewBudgetSheet(sheetName) {
    return gapi.client.sheets.spreadsheets.batchUpdate({
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
    }).then(() => {
        return gapi.client.sheets.spreadsheets.values.update({
            spreadsheetId: SPREADSHEET_ID,
            range: `${sheetName}!A1:F1`,
            valueInputOption: 'USER_ENTERED',
            resource: {
                values: [["Index", "Month", "Amount", "Type", "Item", "Note"]]
            }
        });
    });
}


function batchLoadMonthlyBudgetData(year) {
    const sheetName = `${year}-budget`;
    const ranges = Array.from({length: 12}, (_, i) => 
        `${sheetName}!A${i*100+1}:F${(i+1)*100}`
    );
    
    gapi.client.sheets.spreadsheets.values.batchGet({
        spreadsheetId: SPREADSHEET_ID,
        ranges: ranges
    }).then(response => {
        const valueRanges = response.result.valueRanges;
        valueRanges.forEach((range, index) => {
            const month = index + 1;
            const values = range.values;
            if (values && values.length > 0) {
                
getCell(processMonthData(values), month);
            }
        });
    }, response => {
        console.error('批量加載預算數據時出錯', response.result.error.message);
    });
}

//處理從API獲取的原始數據，將其組織成結構化的格式，包括收入和支出數據，並計算各類型的總計。
function processMonthData(values) {
    const incomeData = {
        '本業收入': [],
        '業外收入': [],
        '利息股息收入': []
    };
    const expenseData = {
        '一般預算': [],
        '儲蓄投資預算': []
    };

    values.forEach(row => {
        const [_, __, amount, type, item, note] = row;
        if (incomeData.hasOwnProperty(type)) {
            incomeData[type].push({ item, amount: parseFloat(amount), note });
        } else if (expenseData.hasOwnProperty(type)) {
            expenseData[type].push({ item, amount: parseFloat(amount), note });
        }
    });

    // 計算總計
    Object.keys(incomeData).forEach(type => {
        const total = incomeData[type].reduce((sum, item) => sum + item.amount, 0);
        incomeData[type].push({ item: '總計', amount: total, note: '' });
    });

    Object.keys(expenseData).forEach(type => {
        const total = expenseData[type].reduce((sum, item) => sum + item.amount, 0);
        expenseData[type].push({ item: '總計', amount: total, note: '' });
    });

    return { incomeData, expenseData };
}

function retryOperation(operation, delay, tries) {
    return new Promise((resolve, reject) => {
        return operation()
            .then(resolve)
            .catch((reason) => {
                if (tries > 0) {
                    return wait(delay)
                        .then(retryOperation.bind(null, operation, delay * 2, tries - 1))
                        .then(resolve)
                        .catch(reject);
                }
                return reject(reason);
            });
    });
}

function wait(delay) {
    return new Promise((resolve) => setTimeout(resolve, delay));
}

//更新預算表格
function updateBudgetTables(budgetData, year, month) {
    updateIncomeTable(budgetData, year, month);
    updateExpenseTable(budgetData, year, month);
    updateYearlyBudgetTable(year);
}

//更新年度預算表格
function updateYearlyBudgetTable(year) {
    const yearlyBudgetTable = document.getElementById('yearlyBudgetTable');
    const tbody = yearlyBudgetTable.querySelector('tbody');
    tbody.innerHTML = '';

    const months = Array.from({length: 12}, (_, i) => i + 1);
    const rows = ['自由現金', '支出預算', '收入'];

    rows.forEach(row => {
        const tr = document.createElement('tr');
        tr.className = row.replace(/\s+/g, '-').toLowerCase();
        tr.innerHTML = `<td>${row}</td>`;

        months.forEach(month => {
            const cell = document.createElement('td');
            cell.id = `${row.replace(/\s+/g, '-').toLowerCase()}-${month}`;
            cell.textContent = '0';  // 預設值
            tr.appendChild(cell);
        });

        const totalCell = document.createElement('td');
        totalCell.id = `${row.replace(/\s+/g, '-').toLowerCase()}-total`;
        totalCell.textContent = '0';  // 預設值
        tr.appendChild(totalCell);

        tbody.appendChild(tr);
    });

    // 加載每個月的數據
    months.forEach(month => {
        loadMonthlyBudgetData(year, month);
    });
}

//更新年度預算儲存格
function updateYearlyBudgetCell(budgetData, month) {
    const incomeTotal = budgetData.filter(item => ['本業收入', '業外收入', '利息股息收入'].includes(item.type))
        .reduce((sum, item) => sum + item.amount, 0);
    const expenseTotal = budgetData.filter(item => ['一般預算', '儲蓄投資預算'].includes(item.type))
        .reduce((sum, item) => sum + item.amount, 0);
    const freeCash = incomeTotal - expenseTotal;

    document.getElementById(`收入-${month}`).textContent = incomeTotal || '0';
    document.getElementById(`支出預算-${month}`).textContent = expenseTotal || '0';
    document.getElementById(`自由現金-${month}`).textContent = freeCash || '0';

    updateYearlyTotals();
}


function updateIncomeTable(budgetData, year, month) {
    const incomeTable = document.getElementById('incomeTable');
    const incomeTypes = ["本業收入", "業外收入", "利息股息收入"];
    let html = `<thead><tr><th>類型</th><th>項目</th><th>金額</th><th>備註</th></tr></thead><tbody>`;

	incomeTypes.forEach(type => {
        const typeData = budgetData.filter(item => item.type === type);
        if (typeData.length === 0) {
            html += `<tr class="${type.replace(/\s+/g, '-')}">
                <td rowspan="2">${type}</td>
                <td></td><td>0</td><td></td>
            </tr>`;
        } else {
            typeData.forEach((item, index) => {
                html += `<tr class="${type.replace(/\s+/g, '-')}">
                    ${index === 0 ? `<td rowspan="${typeData.length}">${type}</td>` : ''}
                    <td>${item.item}</td><td>${item.amount}</td><td>${item.note}</td>
                </tr>`;
            });
        }
        const total = typeData.reduce((sum, item) => sum + item.amount, 0);
        html += `<tr class="${type.replace(/\s+/g, '-')}-total">
            <td colspan="2">${type}總計</td><td>${total}</td><td></td>
        </tr>`;

    });

    html += '</tbody>';
    incomeTable.innerHTML = html;
}

function updateExpenseTable(budgetData, year, month) {
    const expenseTable = document.getElementById('expenseTable');
    const expenseTypes = ["一般預算", "儲蓄投資預算"];
    let html = `<thead><tr><th>類型</th><th>項目</th><th>金額</th><th>備註</th></tr></thead><tbody>`;

    expenseTypes.forEach(type => {
        const typeData = budgetData.filter(item => item.type === type);
        if (typeData.length === 0) {
            html += `<tr class="${type.replace(/\s+/g, '-')}">
                <td rowspan="2">${type}</td>
                <td></td><td>0</td><td></td>
            </tr>`;
        } else {
            typeData.forEach((item, index) => {
                html += `<tr class="${type.replace(/\s+/g, '-')}">
                    ${index === 0 ? `<td rowspan="${typeData.length}">${type}</td>` : ''}
                    <td>${item.item}</td><td>${item.amount}</td><td>${item.note}</td>
                </tr>`;
            });
        }
        const total = typeData.reduce((sum, item) => sum + item.amount, 0);
        html += `<tr class="${type.replace(/\s+/g, '-')}-total">
            <td colspan="2">${type}總計</td><td>${total}</td><td></td>
        </tr>`;
    });

    html += '</tbody>';
    expenseTable.innerHTML = html;
}

// 使用重試機制的例子
function loadBudgetDataWithRetry(year, month) {
    return retryOperation(() => loadBudgetDataFromAPI(year, month), 1000, 3)
        .then(data => updateBudgetTables(data, year, month))
        .catch(error => console.error('加載預算數據失敗', error));
}


function getMonthName(month) {
    const monthNames = ["January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"];
    return monthNames[month - 1];
}

function updateBudgetMonthDisplay() {
    const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "十一月", "十二月"
    ];
    document.getElementById('currentMonthBudget').textContent = 
        `${currentBudgetYear}年 ${monthNames[currentBudgetMonth - 1]}`;
}

//從Google Sheets API加載指定年月的預算數據。如果該月份沒有數據，它會創建預設數據。
function loadBudgetDataFromAPI(year, month) {
    const sheetName = `${year}-budget`;
    const monthName = getMonthName(month);
    
    return gapi.client.sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A:F`
    }).then(response => {
        const values = response.result.values;
        if (values && values.length > 1) {
            return processMonthData(values.filter(row => row[1] === monthName));
        } else {
            console.log('No budget data found');
            return createDefaultMonthData(year, month);
        }
    }).catch(error => {
        console.error('Error loading budget data', error);
        return null;
    });
}

//當指定月份沒有數據時，創建預設數據並將其添加到電子表格中。
function createDefaultMonthData(year, month) {
    const sheetName = `${year}-budget`;
    const monthName = getMonthName(month);
    const defaultData = [
        [1, monthName, 0, '本業收入', '', ''],
        [2, monthName, 0, '業外收入', '', ''],
        [3, monthName, 0, '利息股息收入', '', ''],
        [4, monthName, 0, '一般預算', '', ''],
        [5, monthName, 0, '儲蓄投資預算', '', '']
    ];

    return gapi.client.sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A:F`,
        valueInputOption: 'USER_ENTERED',
        resource: { values: defaultData }
    }).then(() => {
        return processMonthData(defaultData);
    }).catch(error => {
        console.error('Error creating default month data', error);
        return null;
    });
}

function getCachedBudgetData(year, month) {
    const key = `${year}-${month}`;
    if (budgetCache.has(key)) {
        return Promise.resolve(budgetCache.get(key));
    }
    return loadBudgetDataFromAPI(year, month).then(data => {
        budgetCache.set(key, data);
        return data;
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

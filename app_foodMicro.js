// DOM 元素
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const resultContainer = document.getElementById('resultContainer');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modalTitle');
const modalTableBody = document.getElementById('modalTableBody');
const closeBtn = document.querySelector('.close');

// 初始化頁面時不顯示任何食品品項
document.addEventListener('DOMContentLoaded', () => {
  // 不再調用 displayAllFoodItems()
  // 顯示歡迎訊息
  displayWelcomeMessage();
});

// 顯示歡迎訊息
function displayWelcomeMessage() {
  resultContainer.innerHTML = '';
  
  const welcomeMessage = document.createElement('div');
  welcomeMessage.className = 'welcome-message';
  welcomeMessage.innerHTML = `
    <h2>歡迎使用食品微生物衛生標準查詢系統</h2>
    <p>請在上方輸入框中輸入食品品項關鍵字進行搜尋。</p>
    <p>例如：鮮乳、嬰兒食品、水產品、飲料等。</p>
  `;
  
  resultContainer.appendChild(welcomeMessage);
}

// 搜尋按鈕點擊事件 (保留作為備用)
searchButton.addEventListener('click', () => {
  performSearch();
});

// 按下 Enter 鍵也觸發搜尋
searchInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    performSearch();
  }
});

// 添加即時搜尋功能 - 輸入文字時即開始搜尋
searchInput.addEventListener('input', () => {
  // 如果搜尋框為空，顯示歡迎訊息
  if (searchInput.value.trim() === '') {
    displayWelcomeMessage();
    return;
  }
  
  // 執行搜尋
  performSearch();
});

// 關閉模態視窗的點擊事件
closeBtn.addEventListener('click', () => {
  modal.style.display = 'none';
});

// 點擊模態視窗外部區域也關閉模態視窗
window.addEventListener('click', (e) => {
  if (e.target === modal) {
    modal.style.display = 'none';
  }
});

// 顯示所有食品品項 (保留作為備用功能)
function displayAllFoodItems() {
  resultContainer.innerHTML = '';
  
  // 遍歷每個類別
  for (const categoryName in foodSafetyData) {
    const categoryData = foodSafetyData[categoryName];
    const categoryItems = categoryData.items;
    
    // 建立類別元素
    const categoryElement = document.createElement('div');
    categoryElement.className = 'category';
    
    // 設置類別標題
    const categoryTitle = document.createElement('h2');
    categoryTitle.textContent = categoryName;
    const itemCount = document.createElement('span');
    itemCount.className = 'category-count';
    itemCount.textContent = categoryItems.length;
    categoryTitle.appendChild(itemCount);
    categoryElement.appendChild(categoryTitle);
    
    // 新增該類別下所有食品品項
    categoryItems.forEach(item => {
      const foodItem = document.createElement('div');
      foodItem.className = 'food-item';
      foodItem.textContent = item.name;
      foodItem.addEventListener('click', () => {
        showModal(item);
      });
      categoryElement.appendChild(foodItem);
    });
    
    resultContainer.appendChild(categoryElement);
  }
}

// 執行搜尋
function performSearch() {
  const keyword = searchInput.value.trim();
  
  // 如果搜尋關鍵字為空，顯示歡迎訊息
  if (keyword === '') {
    displayWelcomeMessage();
    return;
  }
  
  resultContainer.innerHTML = '';
  let totalResults = 0;
  
  // 遍歷每個類別搜尋符合的食品品項
  for (const categoryName in foodSafetyData) {
    const categoryData = foodSafetyData[categoryName];
    const categoryItems = categoryData.items;
    
    // 過濾符合關鍵字的品項
    const matchedItems = categoryItems.filter(item => 
      item.name.toLowerCase().includes(keyword.toLowerCase())
    );
    
    // 如果該類別有符合的品項，建立類別元素
    if (matchedItems.length > 0) {
      totalResults += matchedItems.length;
      
      const categoryElement = document.createElement('div');
      categoryElement.className = 'category';
      
      const categoryTitle = document.createElement('h2');
      categoryTitle.textContent = categoryName;
      const itemCount = document.createElement('span');
      itemCount.className = 'category-count';
      itemCount.textContent = matchedItems.length;
      categoryTitle.appendChild(itemCount);
      categoryElement.appendChild(categoryTitle);
      
      // 新增符合條件的食品品項
      matchedItems.forEach(item => {
        const foodItem = document.createElement('div');
        foodItem.className = 'food-item';
        
        // 高亮顯示關鍵字
        const itemName = item.name;
        const highlightedName = itemName.replace(
          new RegExp(keyword, 'gi'),
          match => `<span class="highlight">${match}</span>`
        );
        
        foodItem.innerHTML = highlightedName;
        foodItem.addEventListener('click', () => {
          showModal(item);
        });
        categoryElement.appendChild(foodItem);
      });
      
      resultContainer.appendChild(categoryElement);
    }
  }
  
  // 如果沒有結果，顯示無結果訊息
  if (totalResults === 0) {
    const noResults = document.createElement('div');
    noResults.className = 'no-results';
    noResults.innerHTML = `<p>找不到含有 "<strong>${keyword}</strong>" 的食品品項，請嘗試其他關鍵字。</p>`;
    resultContainer.appendChild(noResults);
  }
}

// 顯示模態視窗
function showModal(item) {
  modalTitle.textContent = item.name;
  modalTableBody.innerHTML = '';
  
  // 填充標準表格
  item.standards.forEach(standard => {
    const row = document.createElement('tr');
    
    const microbeCell = document.createElement('td');
    microbeCell.textContent = standard.microbe;
    row.appendChild(microbeCell);
    
    const samplingCell = document.createElement('td');
    samplingCell.textContent = standard.sampling;
    row.appendChild(samplingCell);
    
    const limitCell = document.createElement('td');
    limitCell.textContent = standard.limit;
    row.appendChild(limitCell);
    
    modalTableBody.appendChild(row);
  });
  
  modal.style.display = 'block';
}

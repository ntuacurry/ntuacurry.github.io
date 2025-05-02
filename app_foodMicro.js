// DOM 元素
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const resultContainer = document.getElementById('resultContainer');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modalTitle');
const modalTableBody = document.getElementById('modalTableBody');
const closeBtn = document.querySelector('.close');

// 初始化頁面時顯示所有食品品項
document.addEventListener('DOMContentLoaded', () => {
  displayAllFoodItems();
});

// 搜尋按鈕點擊事件
searchButton.addEventListener('click', () => {
  performSearch();
});

// 按下 Enter 鍵也觸發搜尋
searchInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    performSearch();
  }
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

// 顯示所有食品品項
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
  
  // 如果搜尋關鍵字為空，顯示所有項目
  if (keyword === '') {
    displayAllFoodItems();
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
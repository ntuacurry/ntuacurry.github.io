const checkedCountDisplay = document.getElementById("score");

// 計算「符合」被勾選的數量
function passRate() {
    // 每次調用時重新選取 checkbox，確保不包含已變為 "NA" 的欄位
    const checkboxesCorrect = document.querySelectorAll(".correct");
    const checkboxesB = document.querySelectorAll(".B");
    const checkboxesStar = document.querySelectorAll(".star");

    let countCorrect = 0;
    checkboxesCorrect.forEach(checkbox => {
        if (checkbox.checked) {
            countCorrect++;
        }
    });

    let countB = 0;
    checkboxesB.forEach(checkbox => {
        if (checkbox.checked) {
            countB++;
        }
    });

    let countStar = 0;
    checkboxesStar.forEach(checkbox => {
        if (checkbox.checked) {
            countStar++;
        }
    });

    // 確保分母不為 0 避免錯誤
    const score = checkboxesCorrect.length > 0 
                  ? ((countCorrect / checkboxesCorrect.length) * 100 - (countB + countStar) * 2).toFixed(1)
                  : 0;
    checkedCountDisplay.textContent = score;
}

// 監聽每個核取方塊的變更事件
document.querySelectorAll(".correct, .B, .star").forEach(checkbox => {
    checkbox.addEventListener("change", passRate);
});

// 檢查是否需要改為 NA 並列印
document.getElementById("checkNA").addEventListener("click", function() {
	const rows = document.querySelectorAll("tr");

	rows.forEach(row => {
		// 查找該列中的所有帶有 correct、B 和 star class 的 checkbox
		const checkboxes = row.querySelectorAll(".correct, .B, .star");
		const checkboxColumns = row.querySelectorAll(".checkbox-column");

		// 如果該列中沒有任一個符合條件的 checkbox，則跳過這列
		if (checkboxes.length === 0) return;

		// 檢查該列的 checkbox 是否有任一個被勾選
		const isAnyChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);

		// 如果該列沒有任何 checkbox 被勾選，則合併該列的 checkbox 欄位並填入 "NA"
		if (!isAnyChecked) {
			// 移除該列中的 checkbox 欄位
			checkboxColumns.forEach(column => column.remove());

			// 建立一個合併欄位的 td，colspan 設為 3
			const mergedCell = document.createElement("td");
			mergedCell.setAttribute("colspan", "3");
			mergedCell.textContent = "NA";

			// 設定文字置中
			mergedCell.style.textAlign = "center";

			// 將合併後的 td 加入到該列的最後位置
			row.appendChild(mergedCell);
		}
	});

	// 更新分數
	passRate();
});



// 定義分公司和對應的餐廳
const branches = {
    "台北敦南": ["漢來海港", "名人坊", "漢來蔬食"],
    "台北天母": ["漢來海港"], 
	"台北南港": ["大廳酒廊", "日日烘焙坊", "島語", "宴會廳", "東方樓", "員工餐廳"]
};

// 取得分公司和餐廳下拉選單
const branchSelect = document.getElementById("branch");
const restaurantSelect = document.getElementById("restaurant");

// 監聽分公司選擇改變事件
branchSelect.addEventListener("change", function() {
    const selectedBranch = branchSelect.value;

    // 清空餐廳選單
    restaurantSelect.innerHTML = '<option value="">請選擇餐廳</option>';

    // 根據選擇的分公司填充餐廳選單
    if (selectedBranch && branches[selectedBranch]) {
        branches[selectedBranch].forEach(restaurant => {
            const option = document.createElement("option");
            option.value = restaurant;
            option.textContent = restaurant;
            restaurantSelect.appendChild(option);
        });
    }
});

// 列印
document.getElementById("print").addEventListener("click", function() {
	const selectedBranch = branchSelect.value;
    const selectedRestaurant = restaurantSelect.value;

    // 獲取原來的位置
    const locationCell = document.getElementById("location");

    // 檢查是否選擇了分公司和餐廳
    if (selectedBranch && selectedRestaurant) {
        locationCell.textContent = `${selectedBranch}分公司 ${selectedRestaurant}餐廳`;
        // 列印頁面
        window.print();
    } else {
        window.alert("請選擇分公司和餐廳");
    }

    // 在列印後將單元格內容重置回原始狀態
    locationCell.innerHTML = `
        <select id="branch" class="branch">
            <option value="">請選擇分公司</option>
            <option value="台北敦南">台北敦南</option>
            <option value="台北天母">台北天母</option>
            <option value="台北南港">台北南港</option>
        </select>
        分公司
        <select id="restaurant" class="restaurant">
            <option value="">請選擇餐廳</option>
        </select>
    `;

    // 重新獲取分公司和餐廳下拉選單的引用
    const newBranchSelect = document.getElementById("branch");
    const newRestaurantSelect = document.getElementById("restaurant");

    // 重新填充餐廳選單
    newBranchSelect.addEventListener("change", function() {
        const selectedBranch = newBranchSelect.value;

        // 清空餐廳選單
        newRestaurantSelect.innerHTML = '<option value="">請選擇餐廳</option>';

        // 根據選擇的分公司填充餐廳選單
        if (selectedBranch && branches[selectedBranch]) {
            branches[selectedBranch].forEach(restaurant => {
                const option = document.createElement("option");
                option.value = restaurant;
                option.textContent = restaurant;
                newRestaurantSelect.appendChild(option);
            });
        }
    });

    // 觸發分公司選擇改變事件以填充餐廳選單
    newBranchSelect.dispatchEvent(new Event("change"));
});

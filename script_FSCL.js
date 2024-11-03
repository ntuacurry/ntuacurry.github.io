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

// 檢查是否需要改為 NA
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
    "高雄": ["糕餅小舖-本館", "大廳酒廊-本館", "宴會廳-本館", "福園台菜海鮮餐廳-本館", 
			"翠園粵菜餐廳-本館", "日本料理弁慶-本館", "紅陶上海湯包-本館", "港式海鮮火鍋-本館", 
			"PAVO餐廳-本館", "名人坊-本館", "漢來海港-本館", "焰牛排館-本館", 
			"焰鐵板燒-本館", "上海湯包-夢時代", "溜溜酸菜魚-夢時代", "溜溜酸菜魚-SOGO"], 
    "巨蛋": ["Hi Lai Café", "漢來海港", "漢來蔬食", "宴會廳", "翠園餐廳"], 
    "佛陀": ["Hi Lai Café", "漢來蔬食"], 
    "台南": ["漢來海港", "漢來蔬食"], 
    "台南東寧": ["上海湯包", "名人坊"], 
    "台中": ["漢來海港", "漢來蔬食", "漢來軒"], 
    "台中三民": ["上海湯包", "名人坊"], 
    "新竹": ["上海湯包", "上菜片皮鴨"], 
    "桃園": ["漢來海港", "上海湯包", "上菜片皮鴨", "溜溜酸菜魚"], 
    "台北敦南": ["漢來海港", "名人坊", "漢來蔬食"], 
    "台北信義": ["名人坊"], 
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

// 儲存checkbox狀態
const checkboxes = document.querySelectorAll("input[type='checkbox']");
const purposes = new Set();
const classes = new Set();

// 將每個 checkbox 的狀態存入 sessionStorage 並收集 purposes 和 classes
checkboxes.forEach(checkbox => {
	const rowIdentifier = checkbox.getAttribute("data-row");
	const className = checkbox.classList[0]; // 取得 checkbox 的類別作為識別

	// 收集唯一的 purposes 和 classes
	purposes.add(rowIdentifier);
	classes.add(className);

	// 當 checkbox 狀態改變時，儲存到 sessionStorage
	checkbox.addEventListener("change", function () {
	  sessionStorage.setItem(`${className}-${rowIdentifier}`, checkbox.checked);
	});
});

// 將 purposes 和 classes 儲存到 sessionStorage
sessionStorage.setItem('purposes', JSON.stringify(Array.from(purposes)));
sessionStorage.setItem('classes', JSON.stringify(Array.from(classes)));

// 產生食安查核表
document.getElementById("printCheck").addEventListener("click", function() {
	const selectedBranch = branchSelect.value;
    const selectedRestaurant = restaurantSelect.value;
	const date = document.getElementById("dateSelector").value;

    // 獲取原來的位置
    const locationCell = document.getElementById("location");

    // 檢查是否選擇了分公司和餐廳
    if (selectedBranch && selectedRestaurant) {
        // 開啟列印頁面
		sessionStorage.setItem("branch", selectedBranch);
		sessionStorage.setItem("restaurant", selectedRestaurant);
		let dateStr = date.substring(0,4) + "年" + date.substring(5,7) + "月" + date.substring(8) + "日";
		sessionStorage.setItem("date", dateStr);
		window.open("print_FSCL.html");
    } else {
        window.alert("請選擇分公司和餐廳");
    }
});

document.addEventListener("DOMContentLoaded", function () {
    // 繁中翻譯對應表
    const translations = {
        person: "人員",
        dining: "用餐",
        operate: "作業",
        equipment: "設備",
        material: "原物料",
        document: "文件"
    };

    // 初始化填入的開始位置
    let reasonIndex = 1;

    // 用於存放符合條件的項目
    const items = [];

    // 迭代 sessionStorage 中的所有鍵值對
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        const value = sessionStorage.getItem(key);

        // 檢查條件：格式 xxx-xxxx-x 且值為 "true"
        if (/^[a-zA-Z]+-[a-zA-Z]+-\d+$/.test(key) && value === "true") {
            // 使用正則表達式提取前綴、項目類型和數字部分
            const match = key.match(/^([a-zA-Z]+)-([a-zA-Z]+)-(\d+)$/);

            if (match) { // 確保匹配成功
                const prefix = match[1];
                const itemType = match[2];
                const number = parseInt(match[3], 10); // 轉換數字為整數

                // 避免處理開頭為 "correct" 的項目
                if (prefix !== "correct") {
                    items.push({ itemType, number, key }); // 儲存匹配的項目
                }
            } else {
                console.warn(`變數名稱格式不符合預期: ${key}`);
            }
        }
    }

    // 按照 number 屬性排序
    items.sort((a, b) => a.number - b.number);

    // 依排序後的順序填入表格
    items.forEach((item) => {
        const { itemType, number } = item;

        // 翻譯前綴並組合中文名稱
        const chinesePurpose = `${translations[itemType]}${number}：`;
        console.log(`轉換後的中文名稱: ${chinesePurpose}`);

        // 選擇相應的 reason-<index> 欄位並填入
        const reasonCell = document.getElementById(`reason-${reasonIndex}`);
        const descriptCell = document.getElementById(`descript-${reasonIndex}`);
        
        if (reasonCell) {
            reasonCell.textContent = chinesePurpose;
            console.log(`填入 ${chinesePurpose} 到 reason-${reasonIndex}`);
            
            // 如果對應的 descript 欄位存在，插入 <textarea> 並使其高度隨換行自動調整
            if (descriptCell) {
                const textarea = document.createElement("textarea");
                textarea.setAttribute("cols", "45");
                textarea.setAttribute("rows", "1"); // 設定初始高度為 2 行
                textarea.classList.add("description");

                // 自動調整高度功能
                textarea.addEventListener("input", function () {
                    // 如果 scrollHeight 大於當前高度，則表示換行或新增了內容，更新高度
                    if (textarea.scrollHeight > textarea.clientHeight) {
                        textarea.style.height = `${textarea.scrollHeight}px`;
                    }
                });

                descriptCell.appendChild(textarea);
                console.log(`在 descript-${reasonIndex} 插入 <textarea>`);
            }

            reasonIndex++; // 更新下一個填入的位置

            // 若填滿 24 個欄位，則停止
            if (reasonIndex > 24) {
                return;
            }
        } else {
            console.warn(`未找到對應的 reason-${reasonIndex} 元素`);
        }
    });
});

// 產生缺失說明
document.getElementById("printDescript").addEventListener("click", function() {
	const endDate = document.getElementById("endDate").value;
	// 清除舊數據
	for (let i = 1; i <= 24; i++) {
		sessionStorage.removeItem(`reason-descript-${i}`);
	}

	// 遍歷每個 reason 和 descript，判斷是否都包含內容
	for (let i = 1; i <= 24; i++) {
		const reasonCell = document.getElementById(`reason-${i}`);
		const descriptTextarea = document.querySelector(`#descript-${i} textarea`);

		if (reasonCell && descriptTextarea) {
			const reasonText = reasonCell.textContent.trim();
			const descriptText = descriptTextarea.value.trim();

			// 只有當 reason 和 descript 同時有內容時才暫存
			if (reasonText && descriptText && endDate) {
				const combinedText = `${reasonText}${descriptText}`;
				sessionStorage.setItem(`reason-descript-${i}`, combinedText);
				console.log(`儲存 reason-descript-${i}: ${combinedText}`);
			}
		}
	}
	const endDateStr = endDate.substring(0,4) + "年" + endDate.substring(5,7) + "月" + endDate.substring(8) + "日";
	sessionStorage.setItem("endDate", endDateStr);
	window.open("print_missing_FSCL.html");
});
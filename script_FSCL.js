// 取得核取方塊總數
const checkboxesCorrect = document.querySelectorAll(".correct");
const checkboxesB = document.querySelectorAll(".B");
const checkboxesStar = document.querySelectorAll(".star");

const checkedCountDisplay = document.getElementById("score");

// 計算「符合」被勾選的數量
function passRate() {
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
	
	const score = ((countCorrect / checkboxesCorrect.length)
						* 100 - (countB + countStar) 
						* 2).toFixed(1);
	checkedCountDisplay.textContent = score;
}

// 監聽每個核取方塊的變更事件
checkboxesCorrect.forEach(checkbox => {
	checkbox.addEventListener("change", passRate);
});
checkboxesB.forEach(checkbox => {
	checkbox.addEventListener("change", passRate);
});
checkboxesStar.forEach(checkbox => {
	checkbox.addEventListener("change", passRate);
});

// 檢查是否需要改為NA並列印
document.getElementById("checkNA").addEventListener("click", function() {
	if (confirm("確定要列印嗎？") == true) {
		// 取得 row 內的所有 checkbox
		const checkboxes = document.querySelectorAll("#m1 .checkbox-column input[type='checkbox']");
		const checkboxColumns = document.querySelectorAll("#m1 .checkbox-column");

		// 檢查是否有任一個 checkbox 被勾選
		const isAnyChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);

		// 如果沒有任何 checkbox 被勾選，則合併 checkbox 的欄位並填入 "NA"
		if (!isAnyChecked) {
			// 移除 checkbox 欄位
			checkboxColumns.forEach(column => column.remove());

			// 建立一個合併欄位的 td，colspan 設為 3
			const mergedCell = document.createElement("td");
			mergedCell.setAttribute("colspan", "3");
			mergedCell.textContent = "NA";
			
			// 設定文字置中
			mergedCell.style.textAlign = "center";

			// 將合併後的 td 加入到 row 中最後的位置
			document.getElementById("m1").appendChild(mergedCell);
		}
		// 列印
		window.print();
	}
});
// 將PDF中的數據結構化為JavaScript對象
const foodSafetyData = {
  "1 乳及乳製品類": {
    "items": [
      {
        "name": "1.1 鮮乳、調味乳及乳飲品",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "n=5, c=0", "limit": "10 CFU/mL (g)" },
          { "microbe": "沙門氏菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "金黃色葡萄球菌腸毒素", "sampling": "n=5, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "1.2 乳粉、調製乳粉及供為食品加工原料之乳清粉",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "n=5, c=0", "limit": "10 CFU/mL (g)" },
          { "microbe": "沙門氏菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "金黃色葡萄球菌腸毒素", "sampling": "n=5, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "1.3 發酵乳",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "n=5, c=0", "limit": "10 CFU/mL (g)" },
          { "microbe": "沙門氏菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "金黃色葡萄球菌腸毒素", "sampling": "n=5, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "1.4 本表第1.6項所列罐頭食品以外之煉乳",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "n=5, c=0", "limit": "10 CFU/mL (g)" },
          { "microbe": "沙門氏菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "金黃色葡萄球菌腸毒素", "sampling": "n=5, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "1.5 乾酪(Cheese)、奶油(Butter)及乳脂(Cream)",
        "standards": [
          { "microbe": "大腸桿菌", "sampling": "n=5, c=2", "limit": "m=10 MPN/g (mL), M=100 MPN/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "金黃色葡萄球菌腸毒素", "sampling": "n=5, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "1.6 罐頭食品：保久乳、保久調味乳、保久乳飲品及煉乳",
        "standards": [
          { "microbe": "保溫試驗", "sampling": "", "limit": "經保溫試驗(37℃，10天)檢查合格：沒有因微生物繁殖而導致產品膨罐、變形或pH值異常改變等情形。" }
        ]
      }
    ]
  },
  "2 嬰兒食品類": {
    "items": [
      {
        "name": "2.1 嬰兒配方食品",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "n=10, c=0", "limit": "10 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "n=10, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=10, c=0", "limit": "陰性" },
          { "microbe": "阪崎腸桿菌(屬)", "sampling": "n=10, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "2.2 較大嬰兒配方輔助食品",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "n=10, c=0", "limit": "10 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "n=10, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=10, c=0", "limit": "陰性" },
          { "microbe": "阪崎腸桿菌(屬)", "sampling": "n=10, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "2.3 特殊醫療用途嬰兒配方食品",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "n=10, c=0", "limit": "10 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "n=10, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=10, c=0", "limit": "陰性" },
          { "microbe": "阪崎腸桿菌(屬)", "sampling": "n=10, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "2.4 本表第2.5項所列罐頭食品以外之其他專供嬰兒食用之副食品",
        "standards": [
          { "microbe": "大腸桿菌群", "sampling": "n=5, c=2", "limit": "m=陰性, M=10 MPN/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "n=5, c=0", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "n=5, c=0", "limit": "陰性" }
        ]
      },
      {
        "name": "2.5 罐頭食品：其他供直接食用之嬰兒罐頭食品，如：液態即食配方奶、肉泥、水果泥、蔬菜泥等",
        "standards": [
          { "microbe": "保溫試驗", "sampling": "", "limit": "經保溫試驗(37℃，10天)檢查合格：沒有因微生物繁殖而導致產品膨罐、變形或pH值異常改變等情形。" }
        ]
      }
    ]
  },
  "3 生鮮即食食品及生熟食混和即食食品類": {
    "items": [
      {
        "name": "3.1 生鮮即食水產品",
        "standards": [
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "腸炎弧菌", "sampling": "", "limit": "100 MPN/g" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "3.2 混和生鮮即食水產品之生熟食混和即食食品",
        "standards": [
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "腸炎弧菌", "sampling": "", "limit": "100 MPN/g" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "3.3 生鮮即食蔬果",
        "standards": [
          { "microbe": "大腸桿菌", "sampling": "", "limit": "10 MPN/g" },
          { "microbe": "大腸桿菌O157:H7", "sampling": "", "limit": "陰性" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "3.4 混和生鮮即食蔬果之生熟食混和即食食品",
        "standards": [
          { "microbe": "大腸桿菌", "sampling": "", "limit": "10 MPN/g" },
          { "microbe": "大腸桿菌O157:H7", "sampling": "", "limit": "陰性" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "3.5 供即食之未全熟蛋及含有未全熟蛋之即食食品",
        "standards": [
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" }
        ]
      }
    ]
  },
  "4 包裝/盛裝飲用水及飲料類": {
    "items": [
      {
        "name": "4.1 包裝飲用水及盛裝飲用水",
        "standards": [
          { "microbe": "大腸桿菌群", "sampling": "", "limit": "陰性" },
          { "microbe": "糞便性鏈球菌", "sampling": "", "limit": "陰性" },
          { "microbe": "綠膿桿菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "4.2 含碳酸之飲料(如：汽水、可樂及其他添加碳酸之含糖飲料)",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "4.3 本表第4.7及4.8項所列種類以外之其他還原果蔬汁、果蔬汁飲料、果漿(蜜)及其他類似製品",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "4.4 本表第4.7及4.8項所列種類以外之其他以食品原料萃取而得之飲料(包括咖啡、可可、茶或以穀物、豆類等原料萃取、磨製而成，供飲用之飲料)",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "4.5 未經商業殺菌之鮮榨果蔬汁、添加少於50 %乳品且未經商業殺菌之含乳鮮榨果蔬汁",
        "standards": [
          { "microbe": "大腸桿菌", "sampling": "", "limit": "10 MPN/mL" },
          { "microbe": "大腸桿菌O157:H7", "sampling": "", "limit": "陰性" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "4.6 本表第4.7項所列種類以外之其他發酵果蔬汁(飲料)、添加乳酸調味之酸性飲料、添加發酵液(含活性益生菌)之飲料",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "4.7 本表第4.5項所列種類以外之其他即時調製、未經殺菌處理，且架售期少於24小時之飲料",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "", "limit": "10 CFU /mL" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "4.8 罐頭食品：罐頭飲料",
        "standards": [
          { "microbe": "保溫試驗", "sampling": "", "limit": "經保溫試驗(37℃，10天)檢查合格：沒有因微生物繁殖而導致產品膨罐、變形或pH值異常改變等情形。" }
        ]
      }
    ]
  },
  "5 冷凍食品及冰類": {
    "items": [
      {
        "name": "5.1 食用冰塊",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "", "limit": "10 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "5.2 冷凍即食食品，包括:-冰品，如:冰淇淋、義式冰淇淋、冰棒、刨冰、聖代、雪酪、冰沙等-冷凍水果",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "", "limit": "10 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "5.3 本表第5.6項所列種類以外之其他經加熱煮熟後再冷凍之食品，僅需解凍或復熱即可食用者，包括:-冷凍熟蔬菜",
        "standards": [
          { "microbe": "腸桿菌科", "sampling": "", "limit": "10 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "5.4 冷凍非即食食品-須再經加熱煮熟始得食用之冷凍食品-非供生食之冷凍生鮮水產品",
        "standards": [
          { "microbe": "大腸桿菌", "sampling": "", "limit": "50 MPN/g" }
        ]
      },
      {
        "name": "5.5 供生食之冷凍生鮮水產品",
        "standards": [
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "腸炎弧菌", "sampling": "", "limit": "100 MPN/g" }
        ]
      },
      {
        "name": "5.6 經加熱煮熟後再冷凍之水產品，僅需解凍或復熱即可食用者",
        "standards": [
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "腸炎弧菌", "sampling": "", "limit": "陰性" }
        ]
      }
    ]
  },
  "6 其他即食食品類": {
    "items": [
      {
        "name": "6.1 本表第1類至第5類食品所列以外之其他經復水或沖調即可食用之食品",
        "standards": [
          { "microbe": "金黃色葡萄球菌", "sampling": "", "limit": "100 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "", "limit": "100 CFU /g (mL)" }
        ]
      },
      {
        "name": "6.2 本表第1類至第5類食品所列以外之其他即食食品，以常溫或熱藏保存者",
        "standards": [
          { "microbe": "金黃色葡萄球菌", "sampling": "", "limit": "100 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "", "limit": "100 CFU /g (mL)" }
        ]
      },
      {
        "name": "6.3 本表第1類至第5類食品所列以外之其他即食食品，以冷藏或低溫保存者，包括：-經復熱後即可食用之冷藏或低溫即食食品(如:18℃鮮食)-冷藏甜點、醬料等",
        "standards": [
          { "microbe": "金黃色葡萄球菌", "sampling": "", "limit": "100 CFU/g (mL)" },
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" },
          { "microbe": "單核球增多性李斯特菌", "sampling": "", "limit": "100 CFU /g (mL)" }
        ]
      },
      {
        "name": "6.4 本表第1類至第5類食品所列以外之其他罐頭食品",
        "standards": [
          { "microbe": "保溫試驗", "sampling": "", "limit": "經保溫試驗(37℃，10天)檢查合格：沒有因微生物繁殖而導致產品膨罐、變形或pH值異常改變等情形。" }
        ]
      }
    ]
  },
  "7 液蛋類": {
    "items": [
      {
        "name": "7.1 殺菌液蛋(冷藏或冷凍)",
        "standards": [
          { "microbe": "沙門氏菌", "sampling": "", "limit": "陰性" }
        ]
      },
      {
        "name": "7.2 未殺菌液蛋(冷藏或冷凍)",
        "standards": [
          { "microbe": "總生菌數", "sampling": "", "limit": "10^6 CFU/g" }
        ]
      }
    ]
  }
};

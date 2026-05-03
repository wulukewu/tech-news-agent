#!/usr/bin/env python3
"""
測試 HuggingFace Embedding API 是否真的可用
"""

import asyncio
import ssl
import time

import aiohttp
import certifi


async def test_hf_embedding():
    """測試 HuggingFace 免費 embedding API"""

    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    api_url = f"https://api-inference.huggingface.co/models/{model_name}"

    print("=" * 60)
    print("測試 HuggingFace Embedding API")
    print("=" * 60)
    print(f"模型: {model_name}")
    print(f"API URL: {api_url}")
    print("需要 API Key: 否（免費公開 API）")
    print()

    test_texts = ["人工智慧技術發展", "Machine learning trends", "Python programming"]

    # Create SSL context
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    for i, text in enumerate(test_texts, 1):
        print(f"\n測試 {i}: {text}")
        print("-" * 60)

        start_time = time.time()

        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                payload = {"inputs": text}

                async with session.post(
                    api_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    elapsed = time.time() - start_time

                    print(f"狀態碼: {response.status}")
                    print(f"回應時間: {elapsed:.2f}s")

                    if response.status == 200:
                        result = await response.json()

                        if isinstance(result, list) and len(result) > 0:
                            if isinstance(result[0], list):
                                embedding = result[0]
                            else:
                                embedding = result

                            print("✅ 成功！")
                            print(f"   Embedding 維度: {len(embedding)}")
                            print(f"   前 5 個值: {embedding[:5]}")
                        else:
                            print(f"❌ 回應格式錯誤: {result}")

                    elif response.status == 503:
                        error_data = await response.json()
                        print("⚠️  模型載入中...")
                        print(f"   錯誤訊息: {error_data}")
                        print("   建議: 等待幾秒後重試")

                    else:
                        error_text = await response.text()
                        print("❌ 失敗！")
                        print(f"   錯誤: {error_text}")

        except asyncio.TimeoutError:
            print("❌ 超時（> 30s）")
        except Exception as e:
            print(f"❌ 錯誤: {e}")

    print("\n" + "=" * 60)
    print("測試結論")
    print("=" * 60)
    print(
        """
HuggingFace 免費 Inference API 的特性：

✅ 優點：
   - 完全免費，無需 API key
   - 支援多種模型
   - 簡單易用

❌ 缺點：
   - 不穩定（可能 503 錯誤）
   - 有速率限制（未公開具體數字）
   - 首次請求需要載入模型（慢）
   - 無法追蹤用量
   - 不適合生產環境

💡 建議：
   1. 開發測試：可以使用免費 API
   2. 生產環境：應該使用關鍵字搜尋或自架 embedding 服務
   3. 如果真的需要 embedding：考慮 HuggingFace Pro ($9/月) 或自架
    """
    )


if __name__ == "__main__":
    asyncio.run(test_hf_embedding())

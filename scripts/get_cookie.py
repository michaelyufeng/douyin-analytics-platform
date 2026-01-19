#!/usr/bin/env python3
"""
抖音 Cookie 获取工具

这是一个独立的脚本，用于在本地获取抖音 Cookie。
运行此脚本会打开浏览器窗口，显示抖音登录页面的二维码，
用户扫码登录后，脚本会自动提取并输出 Cookie。

使用方法:
1. 确保已安装依赖: pip install playwright
2. 确保已安装浏览器: playwright install chromium
3. 运行脚本: python get_cookie.py
4. 用抖音 App 扫描二维码
5. 复制输出的 Cookie 字符串
6. 粘贴到抖音数据平台的设置页面

作者: Douyin Analytics Platform
基于 MediaCrawler 的登录逻辑
"""

import asyncio
import sys
from typing import Optional, Dict, Any

# 检查 Playwright 是否安装
try:
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError:
    print("=" * 60)
    print("错误: 未安装 Playwright")
    print("")
    print("请按以下步骤安装:")
    print("  1. pip install playwright")
    print("  2. playwright install chromium")
    print("=" * 60)
    sys.exit(1)


# 抖音登录 URL
DOUYIN_LOGIN_URL = "https://www.douyin.com/"

# QR 码选择器 (来自 MediaCrawler)
QR_CODE_SELECTOR = "xpath=//div[@id='animate_qrcode_container']//img"

# 必要的 Cookie
ESSENTIAL_COOKIES = ["sessionid", "sessionid_ss", "ttwid", "LOGIN_STATUS"]


async def check_login_status(page: Page, context: BrowserContext) -> bool:
    """
    检查是否已登录

    使用 MediaCrawler 的检测逻辑:
    1. 检查 localStorage.HasUserLogin == "1"
    2. 检查 LOGIN_STATUS cookie == "1"
    """
    try:
        # 方法 1: 检查 localStorage
        local_storage = await page.evaluate("() => window.localStorage")
        if local_storage and local_storage.get("HasUserLogin") == "1":
            return True

        # 方法 2: 检查 Cookie
        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}

        if cookie_dict.get("LOGIN_STATUS") == "1":
            return True

        if cookie_dict.get("sessionid"):
            return True

        return False

    except Exception as e:
        print(f"检查登录状态时出错: {e}")
        return False


async def get_cookie_string(context: BrowserContext) -> str:
    """获取格式化的 Cookie 字符串"""
    cookies = await context.cookies()
    return "; ".join([f"{c['name']}={c['value']}" for c in cookies])


async def wait_for_login(page: Page, context: BrowserContext, timeout: int = 300) -> bool:
    """等待用户扫码登录"""
    print("\n等待扫码登录...")
    print("(超时时间: {} 秒)".format(timeout))

    for i in range(timeout):
        if await check_login_status(page, context):
            return True
        await asyncio.sleep(1)
        if i % 10 == 0 and i > 0:
            print(f"已等待 {i} 秒...")

    return False


async def main():
    """主函数"""
    print("=" * 60)
    print("抖音 Cookie 获取工具")
    print("=" * 60)
    print("")
    print("此脚本将打开浏览器窗口，请按以下步骤操作:")
    print("1. 等待浏览器打开抖音页面")
    print("2. 使用抖音 App 扫描二维码")
    print("3. 在手机上确认登录")
    print("4. 登录成功后会自动输出 Cookie")
    print("")
    print("正在启动浏览器...")

    async with async_playwright() as p:
        # 启动浏览器 (非 headless 模式，用户可以看到页面)
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
        )

        # 创建浏览器上下文
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )

        # 防止检测自动化
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # 创建页面
        page = await context.new_page()

        try:
            # 导航到抖音
            print("正在打开抖音...")
            await page.goto(DOUYIN_LOGIN_URL, wait_until="networkidle", timeout=60000)

            # 等待页面加载
            await asyncio.sleep(2)

            # 尝试点击登录按钮
            try:
                login_btn = await page.query_selector("button:has-text('登录'), div:has-text('登录'):not(:has(*))")
                if login_btn:
                    await login_btn.click()
                    await asyncio.sleep(1)
            except:
                pass

            # 尝试切换到扫码登录
            try:
                qr_tab = await page.query_selector("div:has-text('扫码登录'), span:has-text('扫码登录')")
                if qr_tab:
                    await qr_tab.click()
                    await asyncio.sleep(1)
            except:
                pass

            print("")
            print("=" * 60)
            print("请在浏览器窗口中找到二维码并用抖音 App 扫描")
            print("=" * 60)
            print("")

            # 等待用户登录
            if await wait_for_login(page, context):
                # 获取 Cookie
                cookie_string = await get_cookie_string(context)

                # 验证必要的 Cookie
                cookies = await context.cookies()
                cookie_dict = {c["name"]: c["value"] for c in cookies}
                missing = [c for c in ESSENTIAL_COOKIES if c not in cookie_dict or not cookie_dict[c]]

                print("")
                print("=" * 60)
                print("登录成功!")
                print("=" * 60)
                print("")

                if missing:
                    print(f"警告: 缺少部分 Cookie: {missing}")
                    print("Cookie 可能不完整，但仍可尝试使用")
                    print("")

                print("请复制以下 Cookie 字符串:")
                print("")
                print("-" * 60)
                print(cookie_string)
                print("-" * 60)
                print("")
                print("然后粘贴到抖音数据平台的设置页面中")

                # 等待用户复制
                print("")
                input("按 Enter 键关闭浏览器...")

            else:
                print("")
                print("=" * 60)
                print("登录超时，请重新运行脚本")
                print("=" * 60)

        except Exception as e:
            print(f"发生错误: {e}")

        finally:
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)

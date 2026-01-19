#!/usr/bin/env python3
"""
抖音 Cookie 获取工具 - 自动上传版

这是一个独立的脚本，用于在本地获取抖音 Cookie 并自动上传到远程服务器。
运行此脚本会打开浏览器窗口，显示抖音登录页面的二维码，
用户扫码登录后，脚本会自动提取 Cookie 并上传到指定服务器。

使用方法:
1. 确保已安装依赖: pip install playwright httpx
2. 确保已安装浏览器: playwright install chromium
3. 运行脚本: python get_cookie_auto.py --server http://YOUR_SERVER:8080
4. 用抖音 App 扫描二维码
5. 登录成功后，Cookie 会自动上传到服务器

作者: Douyin Analytics Platform
基于 MediaCrawler 的登录逻辑
"""

import argparse
import asyncio
import sys
from typing import Optional

# 检查依赖
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

try:
    import httpx
except ImportError:
    print("=" * 60)
    print("错误: 未安装 httpx")
    print("")
    print("请安装: pip install httpx")
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


async def upload_cookie(server_url: str, cookie_string: str) -> dict:
    """上传 Cookie 到远程服务器"""
    api_url = f"{server_url.rstrip('/')}/api/auth/cookie/save"

    print(f"\n正在上传 Cookie 到服务器...")
    print(f"API 地址: {api_url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                api_url,
                json={"cookie": cookie_string},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"success": False, "message": f"HTTP 错误: {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"success": False, "message": f"请求错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"未知错误: {str(e)}"}


async def check_server_status(server_url: str) -> bool:
    """检查服务器是否可达"""
    api_url = f"{server_url.rstrip('/')}/api/auth/cookie/status"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(api_url)
            response.raise_for_status()
            return True
        except Exception:
            return False


async def main(server_url: Optional[str] = None, no_upload: bool = False):
    """主函数"""
    print("=" * 60)
    print("抖音 Cookie 获取工具 - 自动上传版")
    print("=" * 60)
    print("")

    # 检查服务器连接
    if server_url and not no_upload:
        print(f"目标服务器: {server_url}")
        print("正在检查服务器连接...")

        if await check_server_status(server_url):
            print("服务器连接正常")
        else:
            print("警告: 无法连接到服务器，Cookie 获取后将仅在本地显示")
            print("请检查服务器地址是否正确")
            no_upload = True
        print("")
    elif not no_upload:
        print("未指定服务器地址，Cookie 将仅在本地显示")
        print("使用 --server 参数指定服务器地址以启用自动上传")
        print("")
        no_upload = True

    print("此脚本将打开浏览器窗口，请按以下步骤操作:")
    print("1. 等待浏览器打开抖音页面")
    print("2. 使用抖音 App 扫描二维码")
    print("3. 在手机上确认登录")
    if not no_upload:
        print("4. 登录成功后会自动上传 Cookie 到服务器")
    else:
        print("4. 登录成功后会输出 Cookie")
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

                # 上传或显示 Cookie
                if not no_upload and server_url:
                    result = await upload_cookie(server_url, cookie_string)

                    print("")
                    if result.get("success"):
                        print("=" * 60)
                        print("Cookie 已成功上传到服务器!")
                        print("=" * 60)
                        print("")
                        print("您现在可以关闭此窗口，并在平台上使用数据采集功能")
                    else:
                        print("=" * 60)
                        print(f"上传失败: {result.get('message', '未知错误')}")
                        print("=" * 60)
                        print("")
                        print("Cookie 字符串 (可手动复制):")
                        print("-" * 60)
                        print(cookie_string)
                        print("-" * 60)
                else:
                    print("Cookie 字符串:")
                    print("-" * 60)
                    print(cookie_string)
                    print("-" * 60)
                    print("")
                    print("请复制上述 Cookie 并粘贴到抖音数据平台的设置页面中")

                # 等待用户确认
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


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="抖音 Cookie 获取工具 - 自动上传版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 指定服务器地址，自动上传
  python get_cookie_auto.py --server http://119.28.204.113:8080

  # 仅获取 Cookie，不上传
  python get_cookie_auto.py --no-upload

  # 使用本地服务器
  python get_cookie_auto.py --server http://localhost:8080
"""
    )

    parser.add_argument(
        "--server", "-s",
        type=str,
        help="远程服务器地址，例如: http://119.28.204.113:8080"
    )

    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="仅获取 Cookie，不自动上传"
    )

    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()
        asyncio.run(main(server_url=args.server, no_upload=args.no_upload))
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)

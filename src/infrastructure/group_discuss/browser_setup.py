"""Fixed host-only Playwright installation, never exposed as an AI tool."""

import asyncio
import logging
import sys

from playwright.async_api import Error, async_playwright

logger = logging.getLogger("astrbot")


async def chromium_available():
    """Probe the actual headless executable, not just the full Chromium path."""
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.launch(timeout=15000)
        except Error as exc:
            if "Executable doesn't exist" in str(exc):
                return False
            raise RuntimeError(
                "Chromium 无法启动，请检查浏览器系统依赖和运行用户权限；"
                "Linux 可由管理员执行 python -m playwright install-deps chromium。"
            ) from exc
        await browser.close()
        return True


async def install_chromium():
    """Same interpreter/user/cache as AstrBot. No shell, user args, sudo or AI."""
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "playwright",
        "install",
        "chromium",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        code = await asyncio.wait_for(process.wait(), timeout=300)
        if code:
            raise RuntimeError(
                f"Chromium 自动安装失败（退出码 {code}）。请检查网络和缓存目录权限，"
                "或在 AstrBot Python 环境手动执行 python -m playwright install chromium。"
            )
    finally:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()


class ChromiumSetup:
    def __init__(self, report):
        self.report, self.task = report, None

    def start(self):
        # Route-reload events do not repeatedly install after success or failure.
        if self.task is None:
            self.task = asyncio.create_task(self._run(), name="kakobot-chromium-setup")

    async def _run(self):
        try:
            if await asyncio.wait_for(chromium_available(), timeout=25):
                return
            logger.info("KakoBot: Chromium 缺失，后台安装中（最多 300 秒）。")
            await install_chromium()
            if not await asyncio.wait_for(chromium_available(), timeout=25):
                raise RuntimeError(
                    "Chromium 安装后仍未找到浏览器，请检查运行用户及缓存路径。"
                )
            logger.info("KakoBot: Chromium 安装完成，群讨论卡片已就绪。")
        except Exception as exc:
            logger.error("KakoBot: Chromium 检测/安装失败；卡片将退回文字。")
            try:
                await self.report(exc)
            except Exception:
                logger.error("KakoBot: Chromium 错误通知发送失败。")

    async def stop(self):
        if self.task is not None:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

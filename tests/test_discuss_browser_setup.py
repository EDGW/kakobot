import asyncio
from unittest.mock import AsyncMock

import pytest

from src.infrastructure.group_discuss import browser_setup as module


@pytest.mark.asyncio
@pytest.mark.parametrize("available, installs", [([True], 0), ([False, True], 1)])
async def test_startup_checks_once_and_installs_only_if_missing(
    monkeypatch, available, installs
):
    probe = AsyncMock(side_effect=available)
    install = AsyncMock()
    report = AsyncMock()
    monkeypatch.setattr(module, "chromium_available", probe)
    monkeypatch.setattr(module, "install_chromium", install)
    setup = module.ChromiumSetup(report)
    setup.start()
    first = setup.task
    setup.start()
    assert setup.task is first
    await setup.task
    setup.start()
    assert setup.task is first
    assert install.await_count == installs
    report.assert_not_awaited()
    await setup.stop()


@pytest.mark.asyncio
async def test_install_failure_reports_once_and_does_not_retry_on_route_reload(
    monkeypatch,
):
    monkeypatch.setattr(module, "chromium_available", AsyncMock(return_value=False))
    install = AsyncMock(side_effect=RuntimeError("network unavailable"))
    monkeypatch.setattr(module, "install_chromium", install)
    report = AsyncMock()
    setup = module.ChromiumSetup(report)
    setup.start()
    await setup.task
    setup.start()
    assert install.await_count == 1
    report.assert_awaited_once()
    await setup.stop()


@pytest.mark.asyncio
async def test_installer_uses_fixed_command_and_cleans_up_on_cancel(monkeypatch):
    started = asyncio.Event()

    class Process:
        returncode = None

        async def wait(self):
            started.set()
            if self.returncode is None:
                await asyncio.Event().wait()
            return self.returncode

        def kill(self):
            self.returncode = -9

    process = Process()
    create = AsyncMock(return_value=process)
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", create)
    task = asyncio.create_task(module.install_chromium())
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert process.returncode == -9
    assert create.call_args.args == (
        module.sys.executable,
        "-m",
        "playwright",
        "install",
        "chromium",
    )
    assert "shell" not in create.call_args.kwargs

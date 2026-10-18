import pytest

from src.infrastructure.storage.access.roles import RoleStore, empty_roles
from src.infrastructure.storage.broadcasts.conversations import ConversationStore
from src.infrastructure.storage.broadcasts.upgrades import UpgradeStore
from src.infrastructure.storage.json_store import atomic_json, read_json
from src.infrastructure.storage.migration import VERSION, migrate


def legacy_roles(version):
    data = empty_roles()
    data['version'] = version
    data.pop('group_ddl_everyone')
    data['group_admin_enabled'] = {'10': False, '20': True}
    data['group_roles']['10'] = {
        'group.admin': ['2'], 'group.ddl': ['3'], 'group.summary': ['4']
    }
    if version == 2:
        data.pop('discuss_roles')
    return data


@pytest.mark.parametrize('version', [2, 3])
def test_legacy_everyone_is_ddl_only_and_direct_grants_survive(tmp_path, version):
    path = tmp_path / 'roles.json'
    legacy = legacy_roles(version)
    atomic_json(path, legacy)
    roles = RoleStore(path, '1')
    assert roles.effective('5', '10', True) == {'group.ddl'}
    assert roles.sources('5', '10', True) == {'group.ddl': ['全员 group.ddl 模式']}
    assert roles.effective('5', '10', False) == set()
    assert roles.effective('5', '20', True) == set()
    assert roles.effective('5', '30', True) == set()
    assert roles.effective('2', '10', True) == {'group.admin', 'group.ddl', 'group.summary'}
    assert roles.direct('3', '10') == {'group.ddl'}
    assert roles.direct('4', '10') == {'group.summary'}
    assert roles.data['group_roles'] == legacy['group_roles']
    assert read_json(tmp_path / 'roles-before-everyone-ddl.json') == legacy
    assert RoleStore(path, '1').data == roles.data
    assert read_json(tmp_path / 'roles-before-everyone-ddl.json') == legacy


def test_schema_upgrade_queues_once_even_on_current_release(tmp_path):
    migrate(tmp_path)
    conversations = ConversationStore(tmp_path / 'conversations.sqlite3')
    UpgradeStore(conversations)
    assert conversations.db.execute('SELECT version FROM upgrade_broadcasts').fetchall() == []
    conversations.close()
    atomic_json(tmp_path / 'roles.json', legacy_roles(3))
    migrate(tmp_path)
    migrate(tmp_path)
    conversations = ConversationStore(tmp_path / 'conversations.sqlite3')
    assert conversations.db.execute('SELECT version FROM upgrade_broadcasts').fetchall() == [(VERSION + ':roles-v4',)]
    conversations.close()
    assert RoleStore(tmp_path / 'roles.json', '1').effective('5', '10', True) == {'group.ddl'}


def test_old_access_everyone_migrates_to_ddl(tmp_path):
    atomic_json(tmp_path / 'access.json', {
        'admins': [], 'readonly_groups': [],
        'group_admins': {'10': ['2']}, 'group_admin_disabled': ['10'],
    })
    migrate(tmp_path)
    roles = RoleStore(tmp_path / 'roles.json', '1')
    assert roles.effective('5', '10', True) == {'group.ddl'}
    assert 'group.admin' in roles.effective('2', '10', True)


@pytest.mark.asyncio
async def test_current_release_schema_announcement_delivered_once(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from src.application.messaging.upgrade_announcements import UpgradeAnnouncements
    from src.infrastructure.storage.migration import ROLE_UPGRADE

    migrate(tmp_path)
    old = legacy_roles(3)
    old['global_roles']['autoanalysis'] = ['2']
    atomic_json(tmp_path / 'roles.json', old)
    migrate(tmp_path)
    conversations = ConversationStore(tmp_path / 'conversations.sqlite3')
    conversations.observe(SimpleNamespace(platform='qq', bot='9', actor='2', group='', received_at=1.0))
    gateway = SimpleNamespace(send=AsyncMock())
    announcements = SimpleNamespace(
        roles=RoleStore(tmp_path / 'roles.json', '1'),
        conversations=conversations,
        locks={},
        guard=SimpleNamespace(secrets=SimpleNamespace(check=lambda text: None)),
    )
    monkeypatch.setattr('src.application.messaging.upgrade_announcements.asyncio.sleep', AsyncMock())
    store = UpgradeStore(conversations)
    delivery = UpgradeAnnouncements(announcements, store, lambda *args: gateway)
    await delivery.tick()
    await delivery.tick()
    gateway.send.assert_awaited_once()
    from src.infrastructure.storage.broadcasts.updates import load_update
    assert load_update().strip() in gateway.send.call_args.kwargs['text']
    assert store.pending(ROLE_UPGRADE) == []
    conversations.close()

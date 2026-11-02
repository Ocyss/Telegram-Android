"""Host C ABI contract smoke test; not an Android/JNI/device test.

Run after cargo build --locked -p chatcraft-ffi:
python clients/android/Tools/test_chatcraft_core.py target/debug/chatcraft_ffi.dll
"""

import ctypes
import json
import re
import sys
import tempfile
from pathlib import Path


def check_sources():
    """Source contracts only: these do not execute Java or replace device tests."""
    project = Path(__file__).resolve().parents[1] / "TMessagesProj"
    java = project / "src/main/java/org/telegram"
    expected = {
        "passwordRow": "password",
        "autoDeleteMesages": "autoDeleteMessages",
        "passcodeRow": "passcode",
        "passkeysRow": "passkeys",
        "emailLoginRow": "emailLogin",
        "blockedRow": "blocked",
        "sessionsRow": "sessions",
        "phoneNumberRow": "phoneNumber",
        "lastSeenRow": "lastSeen",
        "profilePhotoRow": "profilePhoto",
        "forwardsRow": "forwards",
        "callsRow": "calls",
        "voicesRow": "voices",
        "noncontactsRow": "noncontacts",
        "birthdayRow": "birthday",
        "giftsRow": "gifts",
        "bioRow": "bio",
        "musicRow": "music",
        "groupsRow": "groups",
        "newChatsRow": "newChats",
        "deleteAccountRow": "deleteAccount",
        "passportRow": "passport",
        "paymentsClearRow": "paymentsClear",
        "botsBiometryRow": "botsBiometry",
        "webSessionsRow": "webSessions",
        "contactsDeleteRow": "contactsDelete",
        "contactsSyncRow": "contactsSync",
        "contactsSuggestRow": "contactsSuggest",
        "secretMapRow": "secretMap",
        "secretWebpageRow": "secretWebpage",
    }
    pattern = re.compile(
        r'(?:org\.telegram\.messenger\.)?ChatcraftCore\s*\.\s*visible\s*\(\s*"(android\.[A-Za-z0-9_.-]+)"\s*\)'
    )
    ids = []
    for source in (java / "ui").rglob("*.java"):
        text = source.read_text(encoding="utf-8")
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//[^\r\n]*", "", text)
        ids.extend(pattern.findall(text))
    settings_ids = {
        "setAvatar",
        "number",
        "setUsername",
        "bio",
        "graceSuggestion",
        "phoneSuggestion",
        "passwordSuggestion",
        "chat",
        "privacy",
        "notifications",
        "data",
        "liteMode",
        "filters",
        "devices",
        "language",
        "premium",
        "stars",
        "ton",
        "business",
        "premiumGifting",
        "question",
        "faq",
        "policy",
        "sendLogs",
        "sendLastLogs",
        "clearLogs",
        "switchBackend",
        "version",
    }
    assert len(ids) == len(set(ids)) == 58, ids
    assert set(ids) == {"android.privacy." + name for name in expected.values()} | {
        "android.settings." + name for name in settings_ids
    }
    profile = (java / "ui/ProfileActivity.java").read_text(encoding="utf-8")
    assert "chatcraftRow = rowCount++;" in profile
    assert 'new SearchResult(9001, "Chatcraft"' in profile
    assert "presentFragment(new ChatcraftSettingsActivity())" in profile
    settings = (java / "ui/ChatcraftSettingsActivity.java").read_text(encoding="utf-8")
    assert 'defaults.put("hidden_ui_ids", new JSONArray());' in settings
    assert settings.index("ChatcraftCore.save(defaults);") < settings.index(
        "refresh(query);"
    )
    video = (java / "messenger/video/VideoAds.java").read_text(encoding="utf-8")
    for method, next_method in (
        ("private void init(", "private int requestId"),
        ("private void load()", "private void schedule()"),
        ("private void schedule()", "private long waitingTimeSince"),
        ("private void show()", "final TLRPC.TL_sponsoredMessage ad"),
    ):
        section = video[video.index(method) : video.index(next_method)]
        assert "ChatcraftCore.hideSponsored()" in section
    assert (
        "if (!loading) return;\n            if (org.telegram.messenger.ChatcraftCore.hideSponsored())"
        in video
    )
    privacy = (java / "ui/PrivacySettingsActivity.java").read_text(encoding="utf-8")
    for row, name in expected.items():
        assert (
            f'{row} = org.telegram.messenger.ChatcraftCore.visible("android.privacy.{name}") ? rowCount++ : -1;'
            in privacy
        )
    assert 'actionBar.createMenu().addItem(100, "Chatcraft")' in privacy
    assert "appear && emailLoginRow >= 0" in privacy
    for row in ("blockedRow", "passwordRow", "autoDeleteMesages", "sessionsRow"):
        assert "listAdapter != null && " + row + " >= 0" in privacy
    dialogs = (java / "ui/DialogsActivity.java").read_text(encoding="utf-8")
    guard = (
        "isChatcraftMainListFiltered(currentAccount, parentPage.dialogsType, folderId)"
    )
    assert guard + " || !allowMoving" in dialogs
    assert guard + " || !(target.itemView instanceof DialogCell)" in dialogs
    assert "return !" + guard + " && super.isLongPressDragEnabled();" in dialogs
    assert "if (folderId != 0 || onlySelect) return false;" in dialogs
    assert (
        "(filter == null || filter.isDefault()) && org.telegram.messenger.ChatcraftCore.hideGroupedChats()"
        in dialogs
    )
    adapter = (java / "ui/Adapters/DialogsAdapter.java").read_text(encoding="utf-8")
    move = adapter[adapter.index("public void moveDialogs(") :]
    assert move.index("if (parentFragment.isChatcraftMainListFiltered(") < move.index(
        "fromDialog.pinnedNum"
    )
    core = (java / "messenger/ChatcraftCore.java").read_text(encoding="utf-8")
    assert "if (DialogObject.isEncryptedDialog(dialogId))" in core
    assert "dialogId = encryptedChat.user_id;" in core
    assert "filter.includesDialog(instance, dialogId, dialog)" in core
    print(
        "Source contracts passed: 58 UI gates, settings entry/reset, video ad guards, drag guards, encrypted membership ID"
    )


def run(library):
    lib = ctypes.CDLL(str(Path(library).resolve()))
    signatures = {
        "open": (ctypes.c_void_p, [ctypes.c_char_p]),
        "free": (None, [ctypes.c_void_p]),
        "get_json": (ctypes.c_void_p, [ctypes.c_void_p]),
        "set_json": (ctypes.c_bool, [ctypes.c_void_p, ctypes.c_char_p]),
        "last_error": (ctypes.c_void_p, [ctypes.c_void_p]),
        "ui_visible": (ctypes.c_bool, [ctypes.c_void_p, ctypes.c_char_p]),
        "hide_sponsored": (ctypes.c_bool, [ctypes.c_void_p]),
        "chat_list_hide": (
            ctypes.c_bool,
            [ctypes.c_void_p, ctypes.c_bool, ctypes.c_uint32, ctypes.c_bool],
        ),
    }
    api = {}
    for name, (result, args) in signatures.items():
        method = getattr(lib, "chatcraft_settings_" + name)
        method.restype, method.argtypes = result, args
        api[name] = method
    lib.chatcraft_string_free.argtypes = [ctypes.c_void_p]
    lib.chatcraft_string_free.restype = None

    def text(pointer):
        try:
            return ctypes.string_at(pointer).decode("utf-8") if pointer else None
        finally:
            lib.chatcraft_string_free(pointer)

    with tempfile.TemporaryDirectory() as directory:
        handle = api["open"](directory.encode("utf-8"))
        assert handle
        try:
            document = json.loads(text(api["get_json"](handle)))
            document.update(
                hide_grouped_chats=True,
                hide_sponsored=False,
                hidden_ui_ids=["android.privacy.secretMap"],
                android_test_unknown={"unicode": "中文🌍"},
            )
            assert api["set_json"](
                handle, json.dumps(document, ensure_ascii=False).encode("utf-8")
            )
            assert not api["ui_visible"](handle, b"android.privacy.secretMap")
            assert api["ui_visible"](handle, b"android.privacy.secretWebpage")
            assert not api["hide_sponsored"](handle)
            for enabled in (False, True):
                for mode in (0, 1, 2, 99):
                    for grouped in (False, True):
                        assert api["chat_list_hide"](
                            handle, enabled, mode, grouped
                        ) == (enabled and mode == 0 and grouped)
            disabled = dict(document, hide_grouped_chats=False)
            assert api["set_json"](handle, json.dumps(disabled).encode("utf-8"))
            assert not api["chat_list_hide"](handle, True, 0, True)
            assert api["set_json"](handle, json.dumps(document).encode("utf-8"))
            assert not api["set_json"](handle, b'{"version":999}')
            assert text(api["last_error"](handle))
            assert json.loads(text(api["get_json"](handle))) == document
        finally:
            api["free"](handle)
        # A reopened process/account-independent store sees the same document.
        handle = api["open"](directory.encode("utf-8"))
        try:
            assert json.loads(text(api["get_json"](handle))) == document
        finally:
            api["free"](handle)
    print(
        "C ABI smoke test passed: UTF-8/unknown fields, persistence, visibility, sponsored, main/folder/archive modes, failed save"
    )


if __name__ == "__main__":
    check_sources()
    run(sys.argv[1])

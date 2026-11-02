package org.telegram.messenger;


import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.util.ArrayList;

import org.telegram.tgnet.TLRPC;

/** One process-wide store: independent of the selected Telegram account. */
public final class ChatcraftCore {
    private static long handle;

    private static long store() {
        if (handle == 0) {
            NativeLoader.initNativeLibs(ApplicationLoader.applicationContext);
            handle = nativeOpen(new File(ApplicationLoader.applicationContext.getFilesDir(), "chatcraft").getAbsolutePath());
            if (handle == 0) throw new IllegalStateException("Cannot open Chatcraft settings");
        }
        return handle;
    }

    public static synchronized JSONObject settings() throws JSONException {
        return new JSONObject(nativeGet(store()));
    }

    public static synchronized String error() {
        return nativeError(store());
    }

    public static synchronized void save(JSONObject settings) {
        if (!nativeSet(store(), settings.toString())) {
            throw new IllegalStateException(nativeError(store()));
        }
        AndroidUtilities.runOnUIThread(() -> {
            for (int account = 0; account < UserConfig.MAX_ACCOUNT_COUNT; account++) {
                if (UserConfig.getInstance(account).isClientActivated()) {
                    NotificationCenter.getInstance(account).postNotificationName(NotificationCenter.dialogsNeedReload);
                }
            }
        });
    }

    public static synchronized boolean visible(String id) {
        return nativeVisible(store(), id);
    }

    public static synchronized boolean hideSponsored() {
        return nativeSponsored(store());
    }

    public static synchronized boolean hideGroupedChats() {
        return nativeHide(store(), true, 0, true);
    }

    public static synchronized ArrayList<TLRPC.Dialog> mainDialogs(int account, ArrayList<TLRPC.Dialog> source) {
        if (!hideGroupedChats()) return source;
        ArrayList<TLRPC.Dialog> result = new ArrayList<>(source.size());
        AccountInstance instance = AccountInstance.getInstance(account);
        for (TLRPC.Dialog dialog : source) {
            boolean grouped = false;
            if (!(dialog instanceof TLRPC.TL_dialogFolder)) {
                long dialogId = dialog.id;
                if (DialogObject.isEncryptedDialog(dialogId)) {
                    TLRPC.EncryptedChat encryptedChat = instance.getMessagesController().getEncryptedChat(DialogObject.getEncryptedChatId(dialogId));
                    if (encryptedChat != null) {
                        dialogId = encryptedChat.user_id;
                    }
                }
                for (MessagesController.DialogFilter filter : instance.getMessagesController().getDialogFilters()) {
                    if (!filter.isDefault() && filter.includesDialog(instance, dialogId, dialog)) {
                        grouped = true;
                        break;
                    }
                }
            }
            if (!nativeHide(store(), true, 0, grouped)) result.add(dialog);
        }
        return result;
    }

    private static native long nativeOpen(String directory);
    private static native String nativeGet(long handle);
    private static native String nativeError(long handle);
    private static native boolean nativeSet(long handle, String json);
    private static native boolean nativeVisible(long handle, String id);
    private static native boolean nativeSponsored(long handle);
    private static native boolean nativeHide(long handle, boolean enabled, int mode, boolean grouped);
}

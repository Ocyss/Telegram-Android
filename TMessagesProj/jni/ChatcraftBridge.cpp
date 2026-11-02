#include <jni.h>
#include <cstdint>
#include <string>

extern "C" {
void *chatcraft_settings_open(const char *);
char *chatcraft_settings_get_json(void *);
char *chatcraft_settings_last_error(void *);
bool chatcraft_settings_set_json(void *, const char *);
bool chatcraft_settings_ui_visible(void *, const char *);
bool chatcraft_settings_hide_sponsored(void *);
bool chatcraft_settings_chat_list_hide(void *, bool, uint32_t, bool);
void chatcraft_string_free(char *);
}

namespace {
// JNI's GetStringUTFChars uses modified UTF-8; the C ABI requires real UTF-8.
std::string utf8(JNIEnv *env, jstring text) {
    jclass type = env->FindClass("java/lang/String");
    jmethodID method = env->GetMethodID(type, "getBytes", "(Ljava/lang/String;)[B");
    jstring encoding = env->NewStringUTF("UTF-8");
    auto bytes = static_cast<jbyteArray>(env->CallObjectMethod(text, method, encoding));
    if (env->ExceptionCheck() || !bytes) return {};
    std::string result(env->GetArrayLength(bytes), '\0');
    env->GetByteArrayRegion(bytes, 0, result.size(), reinterpret_cast<jbyte *>(&result[0]));
    return result;
}
jstring take(JNIEnv *env, char *text) {
    if (!text) return nullptr;
    std::string value(text);
    chatcraft_string_free(text);
    jbyteArray bytes = env->NewByteArray(value.size());
    env->SetByteArrayRegion(bytes, 0, value.size(), reinterpret_cast<const jbyte *>(value.data()));
    jclass type = env->FindClass("java/lang/String");
    return static_cast<jstring>(env->NewObject(type,
        env->GetMethodID(type, "<init>", "([BLjava/lang/String;)V"), bytes, env->NewStringUTF("UTF-8")));
}
void *store(jlong handle) { return reinterpret_cast<void *>(static_cast<uintptr_t>(handle)); }
}

extern "C" JNIEXPORT jlong JNICALL Java_org_telegram_messenger_ChatcraftCore_nativeOpen(JNIEnv *env, jclass, jstring path) {
    auto value = utf8(env, path);
    if (env->ExceptionCheck()) return 0;
    return reinterpret_cast<uintptr_t>(chatcraft_settings_open(value.c_str()));
}
extern "C" JNIEXPORT jstring JNICALL Java_org_telegram_messenger_ChatcraftCore_nativeGet(JNIEnv *env, jclass, jlong handle) {
    return take(env, chatcraft_settings_get_json(store(handle)));
}
extern "C" JNIEXPORT jstring JNICALL Java_org_telegram_messenger_ChatcraftCore_nativeError(JNIEnv *env, jclass, jlong handle) {
    return take(env, chatcraft_settings_last_error(store(handle)));
}
extern "C" JNIEXPORT jboolean JNICALL Java_org_telegram_messenger_ChatcraftCore_nativeSet(JNIEnv *env, jclass, jlong handle, jstring json) {
    auto value = utf8(env, json);
    return !env->ExceptionCheck() && chatcraft_settings_set_json(store(handle), value.c_str());
}
extern "C" JNIEXPORT jboolean JNICALL Java_org_telegram_messenger_ChatcraftCore_nativeVisible(JNIEnv *env, jclass, jlong handle, jstring id) {
    auto value = utf8(env, id);
    return env->ExceptionCheck() || chatcraft_settings_ui_visible(store(handle), value.c_str());
}
extern "C" JNIEXPORT jboolean JNICALL Java_org_telegram_messenger_ChatcraftCore_nativeSponsored(JNIEnv *, jclass, jlong handle) {
    return chatcraft_settings_hide_sponsored(store(handle));
}
extern "C" JNIEXPORT jboolean JNICALL Java_org_telegram_messenger_ChatcraftCore_nativeHide(JNIEnv *, jclass, jlong handle, jboolean enabled, jint mode, jboolean grouped) {
    return chatcraft_settings_chat_list_hide(store(handle), enabled, mode, grouped);
}
